import base64
import pickle
import socket
import struct
import wave

import cv2, imutils, time
import queue as pyqueue
import os
import threading

import pyaudio

fullpath = "/home/yagorezende/VSCodeProjects/TCC00314-Streaming/streaming_side/videos/"  # os.path.abspath(os.getcwd()).replace("testing", "videos/")

# fila de frames, depois trocar isso para uma fila por cliente
queue = pyqueue.Queue(maxsize=30)
video_name = "KimiNoNaWa_240p.mp4"
filename = fullpath + video_name

# pegando audio
command = f"ffmpeg -i '{filename}' -ab 160k -ac 2 -ar 44100 -vn temp.wav"
os.system(command)

# [ SERVER CONFIG ]
# Configs do servidor UDP
BUFF_SIZE = 65536
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
host_name = socket.gethostname()
host_ip = 'localhost'  # socket.gethostbyname(host_name)
print(host_ip)
port = 9699
socket_address = (host_ip, port)
server_socket.bind(socket_address)
print('Listening at:', socket_address)
# [ ENDOF SERVER CONFIG ]

# [ VIDEO METADATA ]
vid = cv2.VideoCapture(filename)  # arquivo de video carregado
# pegando a taxa de frames do video
FPS = vid.get(cv2.CAP_PROP_FPS)  # fps desejado
print("FPS:", FPS)
TS = 1 / FPS  # tempo por frame, importante para a sync com audio
print("TS:", TS, "seconds")
BREAK = False  # TODO: descobrir oq é isso
print('FPS:', FPS, TS)
totalNoFrames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))  # quantidade de frames
durationInSeconds = float(totalNoFrames) / float(FPS)  # tempo de um frame
d = vid.get(cv2.CAP_PROP_POS_MSEC)  # TODO: descobrir oq é isso 2
print(durationInSeconds, d)


# [ EDOF VIDEO METADATA ]


# adicionando os frames lidos e processados na fila de envio
def video_stream_gen():
    """
    This function will deposit the video frames to a queue
    :return: None
    """
    WIDTH = 420
    while vid.isOpened():
        _, frame = vid.read()
        # frame = imutils.resize(frame, width=WIDTH)
        queue.put(frame)
        # Controle
        # print("Queue size:", queue.qsize())

    print('Player closed')
    BREAK = True
    vid.release()


def audio_stream():
    s = socket.socket()
    s.bind((host_ip, (port - 1)))

    s.listen(5)
    CHUNK = 1024 * 4
    wf = wave.open("temp.wav", 'rb')
    p = pyaudio.PyAudio()
    print('server listening at', (host_ip, (port - 1)))
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    input=True,
                    frames_per_buffer=CHUNK)

    client_socket, addr = s.accept()

    while True:
        if client_socket:
            while True:
                data = wf.readframes(CHUNK)
                a = pickle.dumps(data)
                message = struct.pack("Q", len(a)) + a
                client_socket.sendall(message)

# variáveis para manter a taxa de frames atual/corrente
fps, st, frames_to_count, cnt = (0, 0, 20, 0)
# thread para gerar os frames
t1 = threading.Thread(target=video_stream_gen)
t1.start()

# thread para gerar os audios
t2 = threading.Thread(target=audio_stream)
t2.start()

while True:
    msg, client_addr = server_socket.recvfrom(BUFF_SIZE)
    print('GOT connection from ', client_addr)
    WIDTH = 420
    # display video on server side
    while True:
        frame = queue.get()

        # envia pelo socket
        encoded, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        message = base64.b64encode(buffer)
        server_socket.sendto(message, client_addr)

        frame = cv2.putText(frame, f"FPS: {round(fps, 1)}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        # print(fps)  # variação do fps
        if cnt == frames_to_count:
            try:
                fps = (frames_to_count / (time.time() - st))
                st = time.time()  # guardando referencia para fazer o delta time
                cnt = 0
                # Pulo do gato, controle do frame rate
                if fps > FPS:
                    TS += 0.001  # acrescentando um delay de 1 millisec
                elif fps < FPS:
                    TS -= 0.001  # reduzindo o delay em 1 millisec
                else:
                    pass
            except:
                pass
        cnt += 1
        cv2.imshow(video_name, frame)
        # tempo que o frame fica na tela
        # Pulo do gato, delay para apresentar no frame rate correto
        key = cv2.waitKey(int(TS * 1000)) & 0xFF
        if key == ord("q"):
            TS = False
            os._exit(1)
            break
