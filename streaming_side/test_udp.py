import socket, json

msgFromClient = {"request": "LISTAR_VIDEOS"}

bytesToSend = json.dumps(msgFromClient).encode()

serverAddressPort = ("127.0.0.1", 5050)

bufferSize = 65536

# Create a UDP socket at client side
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Send to server using created UDP socket
UDPClientSocket.sendto(bytesToSend, serverAddressPort)

msgFromServer = UDPClientSocket.recvfrom(bufferSize)

msg = "Message from Server {}".format(msgFromServer[0])

print(msg)
