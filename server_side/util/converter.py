import os
import moviepy.editor as mpe
import moviepy.video.fx.resize as mpfr
from server_side.util.constants import QUALITY
import json


class Converter:
    def __init__(self, clip_path: str):
        self.clip_path = clip_path
        self.clip_dir = "/".join(clip_path.split("/")[:-1])
        self.file_name = clip_path.split("/").pop()
        self.ext = "mp4"  # self.file_name.split(".").pop()
        self.file_name = self.file_name.replace("." + self.ext, "")

    def convert_to(self, quality: str, saving_path=None):
        if not saving_path:
            saving_path = self.get_path()
        clip = mpe.VideoFileClip(self.clip_path)
        clip_resized = mpfr.resize(clip, width=QUALITY[quality])
        clip_resized.write_videofile(saving_path + self.file_name + "_" + quality + "." + self.ext)

    def get_path(self):
        if self.clip_dir:
            return self.clip_dir + "/"
        return ""

    def build_metadata(self) -> dict:
        keys = list(QUALITY.keys())
        return {self.file_name: [self.file_name + "_" + key + "." + self.ext for key in keys]}

    def save_metadata(self):
        json_content = json.dumps(self.build_metadata())
        file_path = self.clip_dir + "/metadata/" + self.file_name + ".json"
        print(file_path)
        with open(file_path, "w") as f:
            f.write(json_content)


if __name__ == "__main__":
    print(os.getcwd())
    FILE_PATH = "/home/yagorezende/VSCodeProjects/TCC00314-Streaming/streaming_side/videos/RealState.mp4"
    converter = Converter(FILE_PATH)
    converter.convert_to("720p", saving_path="../../streaming_side/videos/")
    converter.convert_to("480p", saving_path="../../streaming_side/videos/")
    converter.convert_to("240p", saving_path="../../streaming_side/videos/")
    print(converter.build_metadata())
    converter.save_metadata()
