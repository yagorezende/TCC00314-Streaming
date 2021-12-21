import json
from os import listdir
from os.path import isfile, join
import cv2, imutils, socket, time, base64

BUFF_SIZE = 65536
host_ip = 'localhost'
port = 5050
WIDTH = 400


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
        elif request["request"] == "REPRODUZIR_VIDEO":
            start_stream(server_socket, client_addr,filename="videos/"+request["video"], width=request["quality"])
        elif request["request"] == "SAIR_DA_APP":
            msg = {"request": "SAIR_DA_APP_ACK"}
            server_socket.sendto(json.dumps(msg).encode(), client_addr)
        else:
            break


def list_videos(server_socket, client_addr):
    onlyfiles = [f for f in listdir("videos") if isfile(join("videos", f))]
    msg = {"request": "LISTA_DE_VIDEOS", "lista": onlyfiles}
    server_socket.sendto(json.dumps(msg).encode(), client_addr)


def start_stream(server_socket, client_addr, filename="videos/video1.mp4", quality="720p"):
    vid = cv2.VideoCapture(filename)  # vem do client qual video reproduzir
    fps, st, frames_to_count, cnt = (0, 0, 20, 0)

    while vid.isOpened():
        _, frame = vid.read()
        frame = imutils.resize(frame, width=get_width(quality))
        encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        message = base64.b64encode(buffer)
        server_socket.sendto(message, client_addr)
        frame = cv2.putText(frame, 'FPS: ' + str(fps), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow('Transmitindo vídeo', frame)
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


def get_width(quality):
	if(quality == "720p"):
		return 1280
	elif(quality == "480p"):
		return 854
	elif(quality == "240p"):
		return 426
	else:
		raise "quality not"

if __name__ == "__main__":
    open_server()
