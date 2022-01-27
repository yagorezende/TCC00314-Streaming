import os
import pickle
import struct
import threading
from tkinter import *
import socket
import json
from tokenize import group
import cv2
import base64
import numpy as np
import time
import zlib

import pyaudio

BUFF_SIZE = 65536
FRAME_SIZE = BUFF_SIZE - 2**10
HOST = '127.0.0.1'
PORT = 5050
TCP_PORT = 6060
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
audio_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dest = (HOST, PORT)
udp.connect(dest)
audio_udp.connect((HOST, PORT-1))


class InitialFrame(Frame):
    def __init__(self, link, navigator, quit_app):
        super().__init__(link)
        self.main_label = Label(self, text="UFFlix", font=("Arial", 25))
        self.login_btn = Button(self, text="Entrar na app!", command=navigator, width=20)
        self.quit_button = Button(self, text="Sair!", command=lambda: quit_app(), width=20)
        self.username_label = Label(self, text="username", pady=10, padx=10).grid(row=1, column=0)
        self.username_entry = Entry(self, width=20)
        self.main_label.grid(column=0, row=0, columnspan=2)
        self.username_entry.grid(column=1, row=1)
        self.login_btn.grid(column=0, row=3, columnspan=2, pady=10)
        self.quit_button.grid(column=0, row=4, columnspan=2)


class GroupsFrame(Frame):
    def __init__(self, link, navigator):
        super().__init__(link)

        req = {"request": "LISTAR_GRUPOS"}
        bytesToSend = json.dumps(req).encode()
        udp.sendall(bytesToSend)
        res = udp.recv(BUFF_SIZE)
        resAsJson = json.loads(res)
        groups = resAsJson['grupos']

        title = Label(self, text="Grupos", pady=10, font=("Arial", 25))
        title.pack()
        curr_frame = Frame(self, bd=0, relief=SUNKEN)
        curr_column = 0
        for group in groups:
            Button(curr_frame, text=group['nome'], command=lambda group=group: navigator(group['nome']), width=14, height=7, font=40, background='#4169e1').grid(
                column=curr_column, row=0, pady=5, padx=5)
            curr_frame.pack(fill=BOTH, expand='yes')
            curr_column += 1

        Button(curr_frame, text="+ novo grupo", command=lambda : self.new_group_dialog(link, navigator), width=14, height=7, font=40).grid(
                column=curr_column, row=0, pady=5, padx=5)
        curr_frame.pack(fill=BOTH, expand='yes')

    def new_group_dialog(self, link, navigator, event=None):        
        self.valor = StringVar()
        self.valor.set("")
 
        self.modal = Toplevel(link)
        self.modal.transient(link)
        self.modal.grab_set()
        self.modal.title("Novo grupo")
        Label(self.modal, text="Digite o nome do novo grupo:", pady=5, padx=5).pack()
        self.input = Entry(self.modal, text=self.valor.get())
        self.input.bind("<Escape>", self.close_modal)
        self.input.pack(padx=15)
        self.input.focus_set()
        b = Button(self.modal, text="OK", command=lambda : self.create_group(navigator, self.input.get()))
        b.pack(pady=5)

    def create_group(self, navigator, nome):
        if nome != "":
            req = {"request": "CRIAR_GRUPO", 'nome': nome}
            bytesToSend = json.dumps(req).encode()
            udp.sendall(bytesToSend)
            res = udp.recv(BUFF_SIZE)
            resAsJson = json.loads(res)
            if resAsJson['success']:
                self.close_modal()
                navigator(nome)
            else:
                self.close_modal()
        else:
            self.close_modal()

    def close_modal(self, event=None):
        self.modal.destroy()


class ListVideosFrame(Frame):
    def __init__(self, link, back, navigator, group, quit_app):
        super().__init__(link)

        # start socket comm
        req = {"request": "LISTAR_VIDEOS"}
        bytesToSend = json.dumps(req).encode()
        udp.sendall(bytesToSend)
        res = udp.recv(BUFF_SIZE)
        resAsJson = json.loads(res)
        self.videos = resAsJson['lista']
        self.videos.sort()
        # end socket comm

        cur_row = 0
        title = Frame(self, pady=20, bd=0)
        Label(title, text=group, pady=10, font=("Arial", 20)).grid(column=0, row=0, pady=5, padx=5)
        Button(title, text="Trocar de grupo", command=lambda : back()).grid(column=1, row=0, pady=5, padx=5)
        title.pack()
        Label(self, text="Lista de vídeos disponiveis", font=("Arial", 25)).pack()
        for video in self.videos:
            curr_frame = Frame(self, pady=20, highlightbackground="#ffffff", highlightthickness=1, bd=0, relief=SUNKEN)
            Label(curr_frame, text=video, width=30).grid(column=0, row=0, pady=5, padx=5)
            Button(curr_frame, text="720p (1280x720 pixels)", command=lambda video=video: navigator(video, "720p")).grid(
                column=1, row=0, pady=5, padx=5)
            Button(curr_frame, text="480p (854x480 pixels)", command=lambda video=video: navigator(video, "480p")).grid(
                column=2, row=0, pady=5, padx=5)
            Button(curr_frame, text="240p (426x240 pixels)", command=lambda video=video: navigator(video, "240p")).grid(
                column=3, row=0, pady=5, padx=5)

            curr_frame.pack(fill=BOTH, expand='yes')
            cur_row += 1

        Button(self, text="sair", command=lambda: quit_app(), padx=50).pack(pady=20)


class VideoFrame(Frame):
    def __init__(self, link, videoname, quality, navigator):
        super().__init__(link)

        # start socket comm
        req = {"request": "REPRODUZIR_VIDEO", "video": videoname, "quality": quality}
        bytesToSend = json.dumps(req).encode()
        udp.sendall(bytesToSend)
        audio_thread = threading.Thread(target=self.audio_stream, args=(videoname,))
        audio_thread.start()
        global close_stream
        close_stream = False
        fps, st, frames_to_count, cnt = (0, 0, 20, 0)

        while True:
            try:
                try:
                    packet, _ = udp.recvfrom(BUFF_SIZE)
                    info = json.loads(packet.decode("utf8"))
                    # print(info)
                    content = bytes()
                    while len(content) < info.get("len"):
                        packet, _ = udp.recvfrom(BUFF_SIZE)
                        content += packet
                        # print(len(content))

                    # print("Content size:", len(content))
                except Exception as e:
                    print("jumping due:", e)
                    continue

                uncompressed = zlib.decompress(content)
                data = pickle.loads(uncompressed)  # base64.b64decode(uncompressed,' /')
                npdata = np.fromstring(data, dtype=np.uint8)
                frame = cv2.imdecode(npdata, 1)
                cv2.imshow("RECEIVING VIDEO", frame)

                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or cv2.getWindowProperty('RECEIVING VIDEO',cv2.WND_PROP_VISIBLE) < 1:
                    # udp.close()
                    close_stream = True

                    cv2.destroyAllWindows()
                    break
                if cnt == frames_to_count:
                    try:
                        fps = round(frames_to_count / (time.time() - st))
                        st = time.time()
                        cnt = 0
                    except:
                        pass
                cnt += 1
            except Exception as e:
                print(e)
                # cv2.destroyAllWindows()
                #break

        Label(self, text="Fim da exibição de: " + videoname + " em " + quality).pack()
        Button(self, text="Voltar", command=navigator).pack(pady=20)

    def audio_stream(self, videoname):
        audio_req = {"request": "GET_AUDIO", "video": videoname}
        bytesToSend = json.dumps(audio_req).encode()


        p = pyaudio.PyAudio()
        CHUNK = 1024
        stream = p.open(format=p.get_format_from_width(2),
                        channels=2,
                        rate=44100,
                        output=True,
                        frames_per_buffer=CHUNK)
        # create socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_address = (HOST, PORT - 1)
        print('server listening at', socket_address)
        client_socket.connect(socket_address)
        print("CLIENT CONNECTED TO", socket_address)
        client_socket.sendall(bytesToSend)

        data = b""
        payload_size = struct.calcsize("Q")
        while True:
            try:
                if close_stream == True:
                    stream.close()
                    break
                while len(data) < payload_size:
                    packet = client_socket.recv(4 * 1024)  # 4K
                    if not packet: break
                    data += packet
                packet_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packet_msg_size)[0]
                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                frame = pickle.loads(frame_data)
                stream.write(frame)
            except:
                stream.close()
                break
        client_socket.close()
        # os._exit(1)


class App(Tk):
    def __init__(self):
        super().__init__()
        self.title("Trabalho streaming de video")
        self.geometry("1280x1024")
        self.curr_frame = InitialFrame(self, self.navigate_to_main, self.sair_da_app)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)

    def navigate_to_main(self):
        self.curr_frame.place_forget()
        self.curr_frame = GroupsFrame(self, self.list_videos)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)
        return

    def list_videos(self, group):
        self.curr_frame.place_forget()
        self.curr_frame = ListVideosFrame(self, self.navigate_to_main, self.go_to_video, group, self.sair_da_app)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)
        return

    def go_to_video(self, videoname, quality):
        self.curr_frame.place_forget()
        self.curr_frame = VideoFrame(self, videoname, quality, self.navigate_to_main)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)
        return

    def sair_da_app(self):
        # req = {"request": "SAIR_DA_APP"}
        # bytesToSend = json.dumps(req).encode()
        # udp.sendall(bytesToSend)
        # res = udp.recv(BUFF_SIZE)
        # resAsJson = json.loads(res)
        # if(resAsJson["request"] == "SAIR_DA_APP_ACK"):
        udp.close()
        quit()


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except:
        app.quit
