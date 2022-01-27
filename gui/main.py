from multiprocessing.dummy import current_process
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
tcp_sock.connect((HOST, TCP_PORT))


class CurrentUserSingleton():
    def __init__(self):
        print('singleton created null')
        self.id = -999
        self.name = ''
        self.service = ''
        self.groups = []
    
    def get(self):
        return {"id": self.id, "name": self.name, "service": self.service, "groups": self.groups}

    def set(self, user):
        self.id = user["id"]
        self.name = user["name"]
        self.service = user["service"]
        self.groups = user["groups"]

    def reset(self):
        self.id = -999
        self.name = ''
        self.service = ''
        self.groups = []

    def has_curr_user(self):
        return self.id != -999
    
global current_user 
current_user = CurrentUserSingleton()

class InitialFrame(Frame):
    def __init__(self, link, navigator, quit_app):
        super().__init__(link)
        self.navigator = navigator
        self.main_label = Label(self, text="UFFlix", font=("Arial", 25))
        self.login_btn = Button(self, text="Entrar na app!", command=lambda: self.login_app(), width=20)
        self.quit_button = Button(self, text="Sair!", command=lambda: self.exit_app(quit_app), width=20)
        self.username_label = Label(self, text="username", pady=10, padx=10).grid(row=1, column=0)
        self.username_entry = Entry(self, width=20)
        self.type_label = Label(self, text="tipo do usuario",pady=10, padx=10).grid(row=2, column=0)
        self.type_var = StringVar()
        self.premium_radio_btn = Radiobutton(self, text="Premium", variable=self.type_var, value='premium',command=self.sel)
        self.guest_radio_btn = Radiobutton(self, text="Guest", variable=self.type_var, value='guest',command=self.sel)
        self.main_label.grid(column=0, row=0, columnspan=2)
        self.username_entry.grid(column=1, row=1)
        self.login_btn.grid(column=0, row=3, columnspan=2, pady=10)
        self.quit_button.grid(column=0, row=4, columnspan=2)
        self.premium_radio_btn.grid(column=1, row=2)
        self.guest_radio_btn.grid(column=2, row=2)
        self.premium_radio_btn.select()

    def login_app(self):
        name = self.username_entry.get()
        type = str(self.type_var.get())
        req = {"request": "ENTRAR_NA_APP", "name": name, "service": type, "ip": "127.0.0.1"}
        bytesToSend = json.dumps(req).encode()
        tcp_sock.sendall(bytesToSend)
        res = tcp_sock.recv(BUFF_SIZE)
        resAsJson = json.loads(res)
        global current_user
        current_user.set(resAsJson["content"])
        print(current_user.get())
        self.navigator()

    def sel(self):
        selection = "You selected the option " + str(self.type_var.get())
        print(selection)        

    def exit_app(self, quitter):
        global current_user
        current_user.reset()
        quitter()


class GroupsFrame(Frame):
    def __init__(self, link, navigator, quit_app):
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
        Button(self, text="Sair!", command=lambda: self.exit_app(quit_app), padx=50).pack(pady=20)
      
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

    def exit_app(self, quitter):
        global current_user
        user_id = current_user.get()["id"]
        req = {"request": "SAIR_DA_APP", "id": user_id}
        bytesToSend = json.dumps(req).encode()
        tcp_sock.sendall(bytesToSend)
        res = tcp_sock.recv(BUFF_SIZE)
        resAsJson = json.loads(res)
        current_user.reset()
        quitter()

class ListVideosFrame(Frame):
    def __init__(self, link, back, navigator, group, quit_app):
        super().__init__(link)

        # start socket comm
        req = {"request": "LISTAR_VIDEOS"}
        bytesToSend = json.dumps(req).encode()
        udp.sendall(bytesToSend)
        res = udp.recv(BUFF_SIZE)
        resAsJson = json.loads(res)
        while not 'lista' in resAsJson.keys():
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
            Button(curr_frame, text="720p (1280x720 pixels)", command=lambda video=video: navigator(video, "720p", group)).grid(
                column=1, row=0, pady=5, padx=5)
            Button(curr_frame, text="480p (854x480 pixels)", command=lambda video=video: navigator(video, "480p", group)).grid(
                column=2, row=0, pady=5, padx=5)
            Button(curr_frame, text="240p (426x240 pixels)", command=lambda video=video: navigator(video, "240p", group)).grid(
                column=3, row=0, pady=5, padx=5)

            curr_frame.pack(fill=BOTH, expand='yes')
            cur_row += 1

        Button(self, text="Sair", command=lambda: self.exit_app(quit_app), padx=50).pack(pady=20)

    def exit_app(self, quitter):
        global current_user
        user_id = current_user.get()["id"]
        req = {"request": "SAIR_DA_APP", "id": user_id}
        bytesToSend = json.dumps(req).encode()
        tcp_sock.sendall(bytesToSend)
        res = tcp_sock.recv(BUFF_SIZE)
        resAsJson = json.loads(res)
        current_user.reset()
        quitter()


class VideoFrame(Frame):
    def __init__(self, link, videoname, quality, group, navigator):
        super().__init__(link)

        req = {"request": "GET_USER_INFORMATION", "id": 0}
        res = self.message_server(req)
        print(res)
        
        if res['content']['service'] == 'premium':
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
                        content = bytes()
                        while len(content) < info.get("len"):
                            packet, _ = udp.recvfrom(BUFF_SIZE)
                            content += packet

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
            req = {"request": "PARAR_STREAMING"}
            bytesToSend = json.dumps(req).encode()
            udp.sendall(bytesToSend)
            Label(self, text="Fim da exibição de: " + videoname + " em " + quality).pack()
            Button(self, text="Voltar", command=lambda group=group: navigator(group)).pack(pady=20)
        else: 
            Label(self, text="Você não tem permissão para reproduzir vídeos. Por favor, mude sua classificação.").pack()
            Button(self, text="Voltar", command=lambda group=group: navigator(group)).pack(pady=20)

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

    def message_server(self, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, 6060))
            s.sendall(json.dumps(data).encode())
            response = s.recv(1024)
            if response:
                return json.loads(response)
            s.shutdown(socket.SHUT_RDWR)


class App(Tk):
    def __init__(self):
        super().__init__()
        self.title("Trabalho streaming de video")
        self.geometry("1280x1024")
        self.curr_frame = InitialFrame(self, self.navigate_to_main, self.sair_da_app)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)

    def navigate_to_main(self):
        self.curr_frame.place_forget()
        self.curr_frame = GroupsFrame(self, self.list_videos, self.sair_da_app)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)
        return

    def list_videos(self, group):
        self.curr_frame.place_forget()
        self.curr_frame = ListVideosFrame(self, self.navigate_to_main, self.go_to_video, group, self.sair_da_app)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)
        return

    def go_to_video(self, videoname, quality, group):
        self.curr_frame.place_forget()
        self.curr_frame = VideoFrame(self, videoname, quality, group, self.list_videos)
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
