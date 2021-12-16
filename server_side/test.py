# Echo client program
import socket, json

HOST = 'localhost'
PORT = 5000


def tester():
    run = True
    data = {"teste": 1}
    while run:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.send(json.dumps(data).encode())
            response = s.recv(1024)
            if response:
                print('Received', repr(response))
            run = input("Rodar de novo? (s/n) ") in ["s", "S"]
            if not run:
                s.sendall(b'kill')


if __name__ == "__main__":
    tester()
