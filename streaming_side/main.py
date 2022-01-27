import json, os
import pickle
import struct
import threading
import wave
from os import listdir
from os.path import isfile, join
import cv2, imutils, socket, time, base64
from cv2 import add
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
streaming = []
streaming_thread = {}


def open_server():
    # get all groups
    grupos_info_req = {"request": "GET_GRUPOS"}
    grupos_info = message_server(grupos_info_req)
    grupos = grupos_info['content']['groups']

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

        elif request.get("request") == "GET_GRUPO_ATUAL":
            for group in grupos:
                if client_addr in group['usuarios']:
                    send_message = {"request": "GET_GRUPO_ATUAL", "has_group": True, "grupo": group['nome']}
                    server_socket.sendto(json.dumps(send_message).encode(), client_addr)
                else:
                    send_message = {"request": "GET_GRUPO_ATUAL", "has_group": False}
                    server_socket.sendto(json.dumps(send_message).encode(), client_addr)

        elif request.get("request") == "LISTAR_GRUPOS":
            user_id = request.get("userId")

            grupos_info_req = {"request": "GET_GRUPOS"}
            grupos_info = message_server(grupos_info_req) #atualiza os grupos
            grupos = grupos_info['content']['groups']
            grupos_pertence = [d for d in grupos if user_id in d['members']]
            send_message = {"request": "LISTAR_GRUPOS", "grupos": grupos_pertence}
            server_socket.sendto(json.dumps(send_message).encode(), client_addr)

        elif request.get("request") == "CRIAR_GRUPO":
            user_id = request.get("userId")
            group_name = request.get("groupName")
            create_request = {"request": "CRIAR_GRUPO", "id": user_id, "name": group_name}
            create = message_server(create_request)
            group_id = create['content']['gid']
            send_message = {"request": "CRIAR_GRUPO", "gid": group_id}
            server_socket.sendto(json.dumps(send_message).encode(), client_addr)

        elif request.get("request") == "REPRODUZIR_VIDEO":
            groupId = request.get("groupId")
            if groupId in streaming_thread.keys():
                send_message = {"request": "REPRODUZIR_VIDEO", "streaming_is_on": True}
                server_socket.sendto(json.dumps(send_message).encode(), client_addr)
                streaming_thread[groupId].append(client_addr)
            else:
                send_message = {"request": "REPRODUZIR_VIDEO", "streaming_is_on": False}
                server_socket.sendto(json.dumps(send_message).encode(), client_addr)


        elif request.get("request") == "PLAY_VIDEO_TO_GROUP":
            groupId = request.get("groupId")
            # current_group_req = {"request": "VER_GRUPO", "gid": groupId}
            # current_group = message_server(current_group_req)
            # print("\n*\n")
            # print("grupo: \n")
            # print(current_group)
            # print("\n*\n")
            streaming_thread[groupId] = [client_addr, ]
            try:
                video_name = request.get("video") + "_" + request.get("quality") + ".mp4"
                quality = QUALITY[request.get("quality")]
                if not client_addr in streaming:
                    streaming.append(client_addr)
                threading.Thread(target=start_stream, args=(server_socket, client_addr, groupId),
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

        elif request.get("request") == "PARAR_STREAMING":
            streaming.remove(client_addr)

        else:
            break
    audio_server.close()

def message_server(data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host_ip, 6060))
        s.sendall(json.dumps(data).encode())
        response = s.recv(1024)
        if response:
            return json.loads(response)
        s.shutdown(socket.SHUT_RDWR)


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
                t = threading.Thread(target=audio_stream_sender, args=(client_socket, addr, video_name))
                t.start()
        except:
            print("error_audio_sending")
            break


def audio_stream_sender(client_socket, addr, audio_name):
    CHUNK = 1024 * 4
    wf = wave.open("videos/"+audio_name+".wav", 'rb')
    print('server listening at', (host_ip, (port - 1)))
    while True:
        if client_socket:
            while addr in streaming:
                try:
                    data = wf.readframes(CHUNK)
                    a = pickle.dumps(data)
                    message = struct.pack("Q", len(a)) + a
                    client_socket.sendall(message)
                except:
                    return


def start_stream(server_socket, client_addr, groupId, filename="video1.mp4", width=400):
    vid = cv2.VideoCapture("videos/" + filename)  # vem do client qual video reproduzir
    FPS = vid.get(cv2.CAP_PROP_FPS)  # fps desejado
    TS = 1 / FPS  # tempo por frame, importante para a sync com audio
    fps, st, frames_to_count, cnt = (0, 0, int(vid.get(cv2.CAP_PROP_FRAME_COUNT)), 0)

    queue = pyqueue.Queue(maxsize=10)
    queue_thread = threading.Thread(target=video_stream_gen, args=(queue, vid))
    queue_thread.start()

    while client_addr in streaming:
        try:
            frame = queue.get()

            # frame = imutils.resize(frame, width=width)
            encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            # message = base64.b64encode(buffer)
            message = pickle.dumps(buffer)
            compressed = zlib.compress(message, 9)
            # print("Message Size:", len(compressed))
            data = {"frame": cnt, "len": len(compressed)}
            for addr in streaming_thread[groupId]:
                server_socket.sendto(json.dumps(data).encode(), addr)
            starting_point = 0
            file_size = 0
            while starting_point < len(compressed) and client_addr in streaming:
                # splitting the data
                data = compressed[starting_point: int(starting_point + FRAME_SIZE)]
                file_size += len(data)
                # print("Sending Message:", len(data), "sent ->", file_size)
                for addr in streaming_thread[groupId]:
                    server_socket.sendto(data, addr)
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
