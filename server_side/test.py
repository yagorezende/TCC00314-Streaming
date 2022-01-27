# Echo client program
import socket, json, sys

HOST = 'localhost'
PORT_STREAMING = 5000
PORT_CLIENT = 6060

requests = [
    {"request": "ENTRAR_NA_APP", "name": "Yago", "service": "premium", "ip": "127.0.0.1"},  # "service" = "guest"
    {"request": "ENTRAR_NA_APP", "name": "Marcos", "service": "guest", "ip": "127.0.0.1"},  # "service" = "guest"
    {"request": "GET_USER_INFORMATION", "id": 0},
    {"request": "CRIAR_GRUPO", "id": 0, "name": "Amigos"},
    {"request": "ADD_USUARIO_GRUPO", "id": 1, "gid": 0},
    {"request": "VER_GRUPO", "gid": 0},
    {"request": "REMOVER_USUARIO_GRUPO", "id": 1, "gid": 0},
    {"request": "SAIR_DA_APP", "id": 0},
]


def tester(port):
    run = True
    while run:
        print("\nrequests")
        for i, request in enumerate(requests):
            print(f"{i} - {request}")
        print(f"{len(requests)} - exit")
        opt = eval(input("Escolha: "))
        if opt >= len(requests):
            run = False
        else:
            data = requests[opt]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, port))
                s.sendall(json.dumps(data).encode())
                response = s.recv(1024)
                if response:
                    print('Received', repr(response))
                if not run:
                    s.sendall(b'kill')
                s.shutdown(socket.SHUT_RDWR)


if __name__ == "__main__":
    print(sys.argv)
    tester(int(sys.argv[1]))
