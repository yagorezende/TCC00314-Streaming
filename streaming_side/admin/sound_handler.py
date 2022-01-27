import queue
import sys
import threading
import time
import numpy as np
import moviepy.editor as mp
import pyaudio
import sounddevice as sd
import wave

# Set chunk size of 1024 samples per data frame
CHUNK = 1024


class AudioHandler:
    def __init__(self):
        self.stream = None
        self.audio_file = None
        self.player = None

    def open_audio(self, from_path):
        self.audio_file = wave.open(from_path, 'rb')

    def load(self):
        # Create an interface to PortAudio
        self.player = pyaudio.PyAudio()

        # Open a .Stream object to write the WAV file to
        # 'output = True' indicates that the sound will be played rather than recorded
        self.stream = self.player.open(format=self.player.get_format_from_width(self.audio_file.getsampwidth()),
                                       channels=self.audio_file.getnchannels(),
                                       rate=self.audio_file.getframerate(),
                                       output=True)
        return self

    def read_chunk(self):
        return self.audio_file.readframes(CHUNK)

    def play_audio(self, data):
        self.stream.write(data)

    def close(self):
        # Close and terminate the stream
        self.stream.close()
        self.player.terminate()

    @staticmethod
    def extract_audio(from_video: str):
        my_clip = mp.VideoFileClip(from_video)
        # extracting file_path
        file_path = "/".join(from_video.split("/")[:-1])
        # extracting file_name
        file_name = ((from_video.split("/")).pop().split("."))[0]
        file_path = f"{file_path}/{file_name}.wav"
        my_clip.audio.write_audiofile(file_path)
        return file_path


# if __name__ == "__main__":
#     file_path = AudioHandler.extract_audio("/home/yagorezende/VSCodeProjects/TCC00314-Streaming/streaming_side/videos/KimiNoNaWa_720p.mp4")
#     # audio_handler = AudioHandler()
#     # audio_handler.open_audio(file_path)
#     # audio_handler.load()
#     # # Read data in chunks
#     # data = audio_handler.read_chunk()
#     # # Play the sound by writing the audio data to the stream
#     # while data:
#     #     audio_handler.play_audio(data)
#     #     data = audio_handler.read_chunk()

#     audio_handler.close()