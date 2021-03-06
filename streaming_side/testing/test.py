# This is client code to receive video frames over UDP
import json

import cv2, imutils, socket
import numpy as np
import time
import base64

BUFF_SIZE = 65536
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
host_name = socket.gethostname()
host_ip = 'localhost'  # socket.gethostbyname(host_name)
print(host_ip)
port = 5050
qualities = ["720p", "480p", "240p"]
msgFromClient = {"request": "PLAY_VIDEO_TO_GROUP", "quality": qualities[1], "video": "video2.mp4"}
message = json.dumps(msgFromClient).encode()

client_socket.sendto(message, (host_ip, port))
fps, st, frames_to_count, cnt = (0, 0, 300, 0)

while True:
    # video
    packet, _ = client_socket.recvfrom(BUFF_SIZE)
    data = base64.b64decode(packet, ' /')
    # audio
    # soundData, addr = client_socket.recvfrom(BUFF_SIZE)
    # frames.append(soundData)


    npdata = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(npdata, 1)
    frame = cv2.putText(frame, 'FPS: ' + str(fps), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.imshow("RECEIVING VIDEO", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        client_socket.close()
        break
    if cnt == frames_to_count:
        try:
            fps = round(frames_to_count / (time.time() - st))
            st = time.time()
            cnt = 0
        except:
            pass
    cnt += 1
