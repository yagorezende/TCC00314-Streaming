import json, os
import pickle
import struct
import threading
import wave
from os import listdir
from os.path import isfile, join
import cv2, imutils, socket, time, base64
import zlib
import queue as pyqueue
import tqdm

import pyaudio

BUFF_SIZE = 65536
SEND_VIDEO_BUFFER_SIZE = 4096
FRAME_SIZE = BUFF_SIZE - 2 ** 10
host_ip = 'localhost'
port = 5050
WIDTH = 400
QUALITY = {"720p": 1280, "480p": 854, "240p": 426}


def open_server():
    # video server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    socket_address = (host_ip, port)
    server_socket.bind(socket_address)

    # Audio server
    audio_server = socket.socket()
    audio_server.bind((host_ip, (port - 1)))
    audio_server.listen(10)
    threading.Thread(target=audio_stream, args=(audio_server,)).start()

    grupos = {}

    print('Escutando em: ', socket_address)
    running = True
    while running:
        msg, client_addr = server_socket.recvfrom(BUFF_SIZE)
        print('Conexão de: ', client_addr)
        request = json.loads(msg)
        print(request)
        request_type  = request.get("request")
        if request_type == "LISTAR_VIDEOS":
            list_videos(server_socket, client_addr)
        elif request_type == "STREAMAR_MEMBRO_GRUPO":
            # TODO: checar com o servidor de controle se o usuário está no grupo
            grupo_id = request.get("video")
            grupos[grupo_id].append(client_addr)
        elif request_type == "REPRODUZIR_VIDEO":
            try:

                # TODO: mudar para grupos
                video_name = request.get("video") + "_" + request.get("quality") + ".mp4"
                quality = QUALITY[request.get("quality")]
                threading.Thread(target=start_stream, args=(server_socket, client_addr),
                                kwargs=dict(width=quality, filename=video_name)).start()
            except:
                print("error ocurred")
        elif request_type == "ADICIONAR_VIDEO":
            try:
                filename = request.get("filename")
                filesize = request.get("filesize")
                # start receiving the file from the socket
                # and writing to the file stream
                progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
                with open(filename, "wb") as f:
                    while True:
                        # read 1024 bytes from the socket (receive)
                        bytes_read = server_socket.recv(SEND_VIDEO_BUFFER_SIZE)
                        if not bytes_read:    
                            # nothing is received
                            # file transmitting is done
                            break
                        # write to the file the bytes we just received
                        f.write(bytes_read)
                        # update the progress bar
                        progress.update(len(bytes_read))

                
                
            except:
                print("error adding video")
        else:
            break
    audio_server.close()


def list_videos(server_socket, client_addr):
    onlyfiles = [f.replace(".json", "") for f in listdir("videos/metadata") if isfile(join("videos/metadata", f))]
    msg = {"request": "LISTA_DE_VIDEOS", "lista": onlyfiles}
    server_socket.sendto(json.dumps(msg).encode(), client_addr)


# adicionando os frames lidos e processados na fila de envio
def video_stream_gen(queue, vid):
    """
    This function will deposit the video frames to a queue
    :return: None
    """
    while vid.isOpened():
        _, frame = vid.read()
        queue.put(frame)
        # Controle
        # print("Queue size:", queue.qsize())

    print('Player closed')
    vid.release()


def audio_stream(server_socket: socket.socket):
    while server_socket.fileno() > 0:
        try:
            client_socket, addr = server_socket.accept()
            msg = client_socket.recv(4 * 1024)
            request = json.loads(msg)
            if request.get("request") == "GET_AUDIO":                    
                video_name = request.get("video")
                t = threading.Thread(target=audio_stream_sender, args=(client_socket, video_name))
                t.start()
        except:
            print("error_audio_sending")
            break


def audio_stream_sender(client_socket, audio_name):
    CHUNK = 1024 * 4
    wf = wave.open("videos/"+audio_name+".wav", 'rb')
    print('server listening at', (host_ip, (port - 1)))
    while True:
        if client_socket:
            while True:
                try:
                    data = wf.readframes(CHUNK)
                    a = pickle.dumps(data)
                    message = struct.pack("Q", len(a)) + a
                    client_socket.sendall(message)
                except:
                    raise
                    


def start_stream(server_socket, client_addr, filename="video1.mp4", width=400):
    vid = cv2.VideoCapture("videos/" + filename)  # vem do client qual video reproduzir
    FPS = vid.get(cv2.CAP_PROP_FPS)  # fps desejado
    TS = 1 / FPS  # tempo por frame, importante para a sync com audio
    fps, st, frames_to_count, cnt = (0, 0, int(vid.get(cv2.CAP_PROP_FRAME_COUNT)), 0)

    queue = pyqueue.Queue(maxsize=10)
    queue_thread = threading.Thread(target=video_stream_gen, args=(queue, vid))
    queue_thread.start()

    while True:
        try:
            frame = queue.get()

            # frame = imutils.resize(frame, width=width)
            encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            # message = base64.b64encode(buffer)
            message = pickle.dumps(buffer)
            compressed = zlib.compress(message, 9)
            # print("Message Size:", len(compressed))
            data = {"frame": cnt, "len": len(compressed)}
            server_socket.sendto(json.dumps(data).encode(), client_addr)
            starting_point = 0
            file_size = 0
            while starting_point < len(compressed):
                # splitting the data
                data = compressed[starting_point: int(starting_point + FRAME_SIZE)]
                file_size += len(data)
                # print("Sending Message:", len(data), "sent ->", file_size)
                server_socket.sendto(data, client_addr)
                starting_point += FRAME_SIZE

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
            time.sleep(TS)
            key = cv2.waitKey(int(TS * 1000)) & 0xFF
            if key == ord("q"):
                TS = False
                os._exit(1)
                break
        except:

            print('error')
            break

    print("thread finalizada")


if __name__ == "__main__":
    open_server()
