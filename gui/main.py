from email.headerregistry import Group
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
FRAME_SIZE = BUFF_SIZE - 2 ** 10
HOST = '127.0.0.1'
PORT = 5050
TCP_PORT = 6060
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
audio_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dest = (HOST, PORT)
udp.connect(dest)
audio_udp.connect((HOST, PORT - 1))
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
        self.type_label = Label(self, text="tipo do usuario", pady=10, padx=10).grid(row=2, column=0)
        self.type_var = StringVar()
        self.premium_radio_btn = Radiobutton(self, text="Premium", variable=self.type_var, value='premium',
                                             command=self.sel)
        self.guest_radio_btn = Radiobutton(self, text="Guest", variable=self.type_var, value='guest', command=self.sel)
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
        self.assemble_grid(link, navigator, quit_app)

    def assemble_grid(self, link, navigator, quit_app, refresh=False):
        global current_user
        if refresh:
            # refresh user
            bytesToSend = json.dumps({"request": "GET_USER_INFORMATION", "id": current_user.get()["id"]}).encode()
            tcp_sock.sendall(bytesToSend)
            answer = tcp_sock.recv(1024)
            user_data = json.loads(answer)["content"]
            current_user.set(user_data)
            print("user refresh:", user_data)

            for widget in self.winfo_children():
                widget.destroy()

        groups = []
        for group_id in current_user.groups:
            bytesToSend = json.dumps({"request": "VER_GRUPO", "gid": group_id}).encode()
            tcp_sock.sendall(bytesToSend)
            answer = tcp_sock.recv(1024)
            groups.append(json.loads(answer)["content"])
            print(answer)

        title = Label(self, text="Grupos", pady=10, font=("Arial", 25))
        title.pack()
        curr_frame = Frame(self, bd=0, relief=SUNKEN)
        curr_column = 0
        for group in groups:
            Button(curr_frame, text=group['name'], command=lambda group=group: navigator(group['name'], group['id']),
                   width=14, height=7, font=40, background='#4169e1').grid(
                column=curr_column, row=0, pady=5, padx=5)
            curr_frame.pack(fill=BOTH, expand='yes')
            curr_column += 1

        if current_user.service == "premium":
            Button(curr_frame, text="+ novo grupo", command=lambda: self.new_group_dialog(link, navigator), width=14,
                   height=7, font=40).grid(
                column=curr_column, row=0, pady=5, padx=5)
        elif len(groups) == 0:
            no_group_label = Label(self, text="Você ainda não participa de nenhum grupo", pady=5, font=("Arial", 16))
            no_group_label.pack()
        curr_frame.pack(fill=BOTH, expand='yes')
        Button(self, text="Sair!", command=lambda: self.exit_app(quit_app), padx=50).pack(pady=20)
        Button(self, text="Refresh", command=lambda: self.assemble_grid(link, navigator, quit_app, refresh=True),
               padx=50).pack(pady=20)

    def new_group_dialog(self, link, navigator, event=None):
        self.modal = Toplevel(link)
        self.modal.transient(link)
        self.modal.grab_set()
        self.modal.title("Novo grupo")
        Label(self.modal, text="Digite o nome do novo grupo:", pady=5, padx=5).pack()
        self.input = Entry(self.modal)
        self.input.pack(padx=15)
        self.input.bind("<Escape>", self.close_modal)
        b = Button(self.modal, text="OK", command=lambda: self.create_group(navigator))
        b.pack(pady=5)

    def create_group(self, navigator):
        nome = self.input.get()
        if nome != "":
            global current_user
            id = current_user.get()["id"]
            req = {"request": "CRIAR_GRUPO", "id": id, 'name': nome}
            bytesToSend = json.dumps(req).encode()
            tcp_sock.sendall(bytesToSend)
            res = tcp_sock.recv(1024)
            resAsJson = json.loads(res)
            if resAsJson.get("content", {}).get('id', False):
                self.close_modal()
                navigator(nome, resAsJson["content"]['id'])
            else:
                self.close_modal()
        else:
            self.close_modal()

    def close_modal(self, event=None):
        self.modal.destroy()

    def exit_app(self, quitter):
        global current_user
        user_id = current_user.id
        req = {"request": "SAIR_DA_APP", "id": user_id}
        bytesToSend = json.dumps(req).encode()
        tcp_sock.sendall(bytesToSend)
        res = tcp_sock.recv(BUFF_SIZE)
        resAsJson = json.loads(res)
        print("Exit app answer:", resAsJson)
        current_user.reset()
        quitter()


class ListVideosFrame(Frame):
    def __init__(self, link, back, navigator, group, groupId, quit_app, manage_group):
        super().__init__(link)
        global current_user
        # call streaming to ask if streaming video is on
        # if so: adds addr to thred
        if current_user.get()["service"] == "guest":
            req = {"request": "REPRODUZIR_VIDEO", 'gid': groupId}
            bytesToSend = json.dumps(req).encode()
            udp.sendall(bytesToSend)
            res = udp.recv(BUFF_SIZE)
            resAsJson = json.loads(res)
            if resAsJson["streaming_is_on"]:
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

                        if key == ord('q') or cv2.getWindowProperty('RECEIVING VIDEO', cv2.WND_PROP_VISIBLE) < 1:
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
                        # break
                return
        # if not: list videos
        # start socket comm
        req = {"request": "LISTAR_VIDEOS", 'id': current_user.get()["id"]}
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
        title.pack()
        Label(title, text=group + " - " + str(groupId), pady=10, font=("Arial", 20)).grid(column=0, row=0, pady=5,
                                                                                          padx=5)
        Button(title, text="Trocar de grupo", command=lambda: back()).grid(column=1, row=0, pady=5, padx=5)
        if current_user.service == "premium":
            Button(title, text="Gerenciar grupo", command=lambda: manage_group(group, groupId)).grid(column=2, row=0,
                                                                                                     pady=5, padx=5)
        Label(self, text="Lista de vídeos disponiveis", font=("Arial", 25)).pack()
        for video in self.videos:
            curr_frame = Frame(self, pady=20, highlightbackground="#ffffff", highlightthickness=1, bd=0, relief=SUNKEN)
            Label(curr_frame, text=video, width=30).grid(column=0, row=0, pady=5, padx=5)
            Button(curr_frame, text="720p (1280x720 pixels)",
                   command=lambda video=video: navigator(video, "720p", group, groupId)).grid(
                column=1, row=0, pady=5, padx=5)
            Button(curr_frame, text="480p (854x480 pixels)",
                   command=lambda video=video: navigator(video, "480p", group, groupId)).grid(
                column=2, row=0, pady=5, padx=5)
            Button(curr_frame, text="240p (426x240 pixels)",
                   command=lambda video=video: navigator(video, "240p", group, groupId)).grid(
                column=3, row=0, pady=5, padx=5)

            curr_frame.pack(fill=BOTH, expand='yes')
            cur_row += 1

        Button(self, text="Voltar", command=lambda: back(), padx=50).pack(pady=20)


class GroupManager(Frame):
    def __init__(self, link, back, navigator, quit_app, group, groupId):
        super().__init__(link)
        self.groupId = groupId
        self.group = group
        self.back = back
        self.link = link
        self.navigator = navigator
        self.quit_app = quit_app

        self.render_content()

    def add_user_dialog(self, link, navigator, event=None):
        self.modal = Toplevel(link)
        self.modal.transient(link)
        self.modal.grab_set()
        self.modal.title("Novo Usuario")
        Label(self.modal, text="Digite o nome do novo integrante do  grupo:", pady=5, padx=5).pack()
        self.input = Entry(self.modal)
        self.input.pack(padx=15)
        self.input.bind("<Escape>", self.close_modal)
        b = Button(self.modal, text="OK", command=lambda: self.add_to_group(navigator))
        b.pack(pady=5)

    def add_to_group(self, navigator):
        id = int(self.input.get())
        if id >= 0:
            req = {"request": "ADD_USUARIO_GRUPO", "gid": self.groupId, 'id': id}
            bytesToSend = json.dumps(req).encode()
            tcp_sock.sendall(bytesToSend)
            res = tcp_sock.recv(BUFF_SIZE)
            resAsJson = json.loads(res)
            print(resAsJson)
        self.close_modal()
        self.render_content()

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

    def remove_from_group(self, id):
        req = {"request": "REMOVER_USUARIO_GRUPO", "gid": self.groupId, "id": id}
        bytesToSend = json.dumps(req).encode()
        tcp_sock.sendall(bytesToSend)
        res = tcp_sock.recv(BUFF_SIZE)
        resAsJson = json.loads(res)
        print(resAsJson)
        self.render_content()

    def render_content(self):
        for widget in self.winfo_children():
            widget.destroy()
        req = {"request": "VER_GRUPO", "gid": self.groupId}
        bytesToSend = json.dumps(req).encode()
        tcp_sock.sendall(bytesToSend)
        res = tcp_sock.recv(BUFF_SIZE)
        resAsJson = json.loads(res)
        content = resAsJson["content"]
        members = content["members"]
        members_names = []
        for member in members:
            requestObj = {"request": "GET_USER_INFORMATION", "id": member}
            reqBytes = json.dumps(requestObj).encode()
            tcp_sock.sendall(reqBytes)
            result = tcp_sock.recv(BUFF_SIZE)
            resultAsJson = json.loads(result)
            members_names.append(resultAsJson["content"])
        title = Frame(self, pady=20, bd=0)
        title.pack()
        Label(self, text="Usuarios no grupo - " + self.group, font=("Arial", 25)).pack()
        cur_row = 0
        for u in members_names:
            curr_frame = Frame(self, pady=20, highlightbackground="#ffffff", highlightthickness=1, bd=0, relief=SUNKEN)
            Label(curr_frame, text=u["id"], width=30).grid(column=0, row=0, pady=5, padx=5)
            Label(curr_frame, text=u["name"], width=30).grid(column=1, row=0, pady=5, padx=5)
            Label(curr_frame, text=u["service"], width=30).grid(column=2, row=0, pady=5, padx=5)
            Button(curr_frame, text="Remover", command=lambda id=u["id"]: self.remove_from_group(id)).grid(column=3,
                                                                                                           row=0,
                                                                                                           pady=5,
                                                                                                           padx=5)
            curr_frame.pack(fill=BOTH, expand='yes')
            cur_row += 1
        Button(title, text="Trocar de grupo", command=lambda: self.back()).grid(column=1, row=0, pady=5, padx=5)
        Button(title, text="Adicionar ao grupo", command=lambda: self.add_user_dialog(self.link, self.navigator)).grid(
            column=1, row=0, pady=5, padx=5)
        Button(self, text="Voltar", command=lambda group=self.group: self.back(group, self.groupId), padx=50).pack(
            pady=20)


class VideoFrame(Frame):
    def __init__(self, link, videoname, quality, navigator, group, groupId):
        super().__init__(link)

        if current_user.get()["service"] == 'premium':
            # start socket comm
            req = {"request": "PLAY_VIDEO_TO_GROUP", "video": videoname, "quality": quality, "gid": groupId}
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

                    if key == ord('q') or cv2.getWindowProperty('RECEIVING VIDEO', cv2.WND_PROP_VISIBLE) < 1:
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
                    # break
            req = {"request": "PARAR_STREAMING"}
            bytesToSend = json.dumps(req).encode()
            udp.sendall(bytesToSend)
            Label(self, text="Fim da exibição de: " + videoname + " em " + quality).pack()
            Button(self, text="Voltar", command=lambda group=group: navigator(group, groupId)).pack(pady=20)
        else:
            Label(self, text="Você não tem permissão para reproduzir vídeos. Por favor, mude sua classificação.").pack()
            Button(self, text="Voltar", command=lambda group=group: navigator(group, groupId)).pack(pady=20)

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

    def list_videos(self, group, groupId):
        self.curr_frame.place_forget()
        self.curr_frame = ListVideosFrame(self, self.navigate_to_main, self.go_to_video, group, groupId,
                                          self.sair_da_app, self.manage_group)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)
        return

    def go_to_video(self, videoname, quality, group, groupId):
        self.curr_frame.place_forget()
        self.curr_frame = VideoFrame(self, videoname, quality, self.list_videos, group, groupId)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)
        return

    def manage_group(self, group, groupId):
        self.curr_frame.place_forget()
        self.curr_frame = GroupManager(self, self.list_videos, self.navigate_to_main, self.sair_da_app, group, groupId)
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
        tcp_sock.close()
        exit()


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except:
        app.sair_da_app()
        app.quit
