from fileinput import filename
from tkinter import *
from tkinter import filedialog
from pathlib import Path
import numpy as np
import tqdm
import os
from os import listdir
from os.path import isfile, join
from converter import Converter
from sound_handler import AudioHandler
import os
import glob

# from converter import Converter
# from sound_handler import AudioHandler

VIDEO_BUFFER_SIZE = 4096


class ListVideosFrame(Frame):
    def __init__(self, link, quit_app):
        super().__init__(link)
        self.video_location = Path('../streaming_side/videos/metadata').resolve()
        self.quit_app = quit_app
        self.render_things()
        


    def open_file(self):
        file_path = filedialog.askopenfile(mode='r', filetypes=[('Video Files', '*mp4')])
        if file_path is not None:
            return file_path
            pass
    
    def upload_video(self):
        file_path = self.open_file()
        if file_path != None:
            full_filename_path = file_path.name
            filesize = os.path.getsize(full_filename_path)
            filename = os.path.basename(full_filename_path)
            storage_path = Path('../streaming_side/videos/' + filename).resolve()
            progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
            with open(storage_path, "wb") as fw, open(full_filename_path, "rb") as fr:
                while True:
                    # read the bytes from the file
                    bytes_read = fr.read(VIDEO_BUFFER_SIZE)
                    if not bytes_read:
                        # file transmitting is done
                        break
                    # update the progress bar
                    fw.write(bytes_read)
                    progress.update(len(bytes_read))
            
            converter = Converter(str(storage_path))
            converted_path = str(Path('../streaming_side/videos/').resolve())
            print(converted_path)
            
            converter.convert_to("720p")
            converter.convert_to("480p")
            converter.convert_to("240p")
            print(converter.build_metadata())
            converter.save_metadata()
            AudioHandler.extract_audio(str(storage_path))
            self.render_things()

    def delete_video(self, videoname):
        path = str(Path('../streaming_side/**/').resolve()) + '/' + videoname + '*'
        fileList = glob.glob(path, recursive = True)
        for filePath in fileList:
            try:
                os.remove(filePath)
            except:
                print("Error while deleting file : ", filePath)
        self.render_things()

    def render_things(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.videos = [f.replace(".json", "") for f in listdir(self.video_location) if isfile(join(self.video_location, f))]
        self.videos.sort()
        cur_row = 0
        title = Label(self, text="Lista de vídeos disponiveis", pady=10, font=("Arial", 25))
        title.pack()
        for video in self.videos:
            curr_frame = Frame(self, pady=20, highlightbackground="#ffffff", highlightthickness=1, bd=0, relief=SUNKEN)
            Label(curr_frame, text=video, width=30).grid(column=0, row=0, pady=5, padx=5)
            Label(curr_frame, text="720p (1280x720 pixels)").grid(column=1, row=0, pady=5, padx=5)
            Label(curr_frame, text="480p (854x480 pixels)").grid(column=2, row=0, pady=5, padx=5)
            Label(curr_frame, text="240p (426x240 pixels)").grid(column=3, row=0, pady=5, padx=5)
            Button(curr_frame, text="Excluir video", command=lambda video=video: self.delete_video(video)).grid(column=4, row=0, pady=5, padx=5)
            curr_frame.pack(fill=BOTH, expand='yes')
            cur_row += 1
        Button(self, text="Adicionar novo video", command=lambda: self.upload_video(), padx=50).pack(pady=20)
        Button(self, text="sair", command=lambda: self.quit_app(), padx=50).pack(pady=20)

class App(Tk):
    def __init__(self):
        super().__init__()
        self.title("Admin")
        self.geometry("1280x1024")
        self.curr_frame = ListVideosFrame(self, self.sair_da_app)
        self.curr_frame.place(in_=self, anchor="c", relx=.5, rely=.5)

    def sair_da_app(self):
        quit()


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except:
        app.quit
