import json
import threading
from os import listdir
from os.path import isfile, join
import cv2, imutils, socket, time, base64

BUFF_SIZE = 65536
host_ip = 'localhost'
port = 5050
WIDTH = 400
QUALITY = {"720p": 1280, "480p": 854, "240p": 426}


def open_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    socket_address = (host_ip, port)
    server_socket.bind(socket_address)

    print('Escutando em: ', socket_address)
    running = True
    while running:
        msg, client_addr = server_socket.recvfrom(BUFF_SIZE)
        print('Conexão de: ', client_addr)
        request = json.loads(msg)
        if request.get("request") == "LISTAR_VIDEOS":
            list_videos(server_socket, client_addr)
        elif request.get("request") == "REPRODUZIR_VIDEO":
            video_name = request.get("video")
            quality = QUALITY[request.get("quality")]
            threading.Thread(target=start_stream, args=(server_socket, client_addr),
                             kwargs=dict(width=quality, filename=video_name)).start()
        else:
            break


def list_videos(server_socket, client_addr):
    onlyfiles = [f for f in listdir("videos") if isfile(join("videos", f))]
    msg = {"request": "LISTA_DE_VIDEOS", "lista": onlyfiles}
    server_socket.sendto(json.dumps(msg).encode(), client_addr)


def start_stream(server_socket, client_addr, filename="video1.mp4", width=400):
    vid = cv2.VideoCapture("videos/" + filename)  # vem do client qual video reproduzir
    fps, st, frames_to_count, cnt = (0, 0, 300, 0)

    while vid.isOpened():
        ret, frame = vid.read()
        if not ret:
            message = b'FIM'
            server_socket.sendto(message, client_addr)
            break
        frame = imutils.resize(frame, width=width)
        encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        message = base64.b64encode(buffer)
        server_socket.sendto(message, client_addr)
        # frame = cv2.putText(frame, 'FPS: ' + str(fps), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        # cv2.imshow('Transmitindo video', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            server_socket.close()
            break
        if cnt == frames_to_count:
            try:
                fps = round(frames_to_count / (time.time() - st))
                st = time.time()
                cnt = 0
            except:
                pass
        cnt += 1
    print("thread finalizada")


if __name__ == "__main__":
    open_server()
