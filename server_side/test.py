# Echo client program
import socket, json, sys

HOST = 'localhost'
PORT_STREAMING = 5000
PORT_CLIENT = 6060

LOGIN_DATA = {"request": "GET_USER_INFORMATION", "id": 1}


def tester(port):
    run = True
    data = LOGIN_DATA
    while run:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, port))
            s.send(json.dumps(data).encode())
            response = s.recv(1024)
            if response:
                print('Received', repr(response))
            run = input("Rodar de novo? (s/n) ") in ["s", "S"]
            if not run:
                s.sendall(b'kill')
            s.shutdown(socket.SHUT_RDWR)


if __name__ == "__main__":
    print(sys.argv)
    tester(int(sys.argv[1]))
