from tkinter import *
import socket
import json

BUFF_SIZE = 65536
HOST = '127.0.0.1'
PORT= 5050
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = (HOST, PORT)
udp.connect(dest)
class InitialFrame(Frame):
    def __init__(self, link, navigator, quit_app):
        super().__init__(link)
        self.main_label = Label(self, text="UFFlix", font=("Arial", 25))
        self.login_btn = Button(self, text="Entrar na app!", command=navigator, width=20)
        self.quit_button = Button(self, text="Sair!", command=lambda: quit_app(), width=20)
        self.username_label = Label(self, text="username", pady=10, padx=10).grid(row=1, column=0)
        self.username_entry = Entry(self, width=20)
        self.password_label = Label(self, text="password", pady=10, padx=10).grid(row=2, column=0)
        self.password_entry = Entry(self, width=20)
        self.main_label.grid(column=0, row=0, columnspan=2)
        self.username_entry.grid(column=1, row=1)
        self.password_entry.grid(column=1, row=2)
        self.login_btn.grid(column=0, row=3, columnspan=2, pady=10)
        self.quit_button.grid(column=0, row=4, columnspan=2)

class ListVideosFrame(Frame):
    def __init__(self, link, navigator, quit_app):
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
        title = Label(self, text="Lista de vídeos disponiveis", pady=10, font=("Arial", 25))
        title.pack()
        for video in self.videos:
            curr_frame = Frame(self, pady=20,highlightbackground="#ffffff", highlightthickness=1, bd= 0, relief=SUNKEN)
            Label(curr_frame, text=video, width=30).grid(column=0, row=0, pady=5, padx=5)
            Button(curr_frame, text="720p (1280x720 pixels)", command=lambda video=video: navigator(video, "720p")).grid(column=1, row=0, pady=5, padx=5)
            Button(curr_frame, text="480p (854x480 pixels)", command=lambda video=video: navigator(video, "480p")).grid(column=2, row=0, pady=5, padx=5)
            Button(curr_frame, text="240p (426x240 pixels)", command=lambda video=video: navigator(video, "240p")).grid(column=3, row=0, pady=5, padx=5)

            curr_frame.pack(fill=BOTH, expand='yes')
            cur_row += 1
        
        Button(self, text="sair", command=lambda: quit_app(), padx=50).pack(pady=20)

class VideoFrame(Frame):
    def __init__(self, link, videoname, quality, navigator):
        super().__init__(link)
        
        # start socket comm
        # req = {"request": "REPRODUZIR_VIDEO", "video": videoname, "quality": quality}
        # bytesToSend = json.dumps(req).encode()
        # udp.sendall(bytesToSend)
        # res = udp.recv(BUFF_SIZE)
        # resAsJson = json.loads(res)
        # end socket comm

        Label(self, text="Voce esta assistindo a: " + videoname + " em " + quality).pack()
        Button(self, text="Voltar", command=navigator).pack(pady=20)

class App(Tk):
    def __init__(self):
        super().__init__()
        self.title("Trabalho streaming de video")
        self.geometry("1280x1024")
        self.curr_frame = InitialFrame(self, self.navigate_to_main, self.sair_da_app)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)


    def navigate_to_main(self):
        self.curr_frame.place_forget()
        self.curr_frame = ListVideosFrame(self, self.go_to_video, self.sair_da_app)
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
    app = App()
    app.mainloop()



