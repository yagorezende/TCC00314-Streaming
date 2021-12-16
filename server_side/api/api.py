import socket
from server_side.util.constants import CONTROLLER_PORT
from server_side.util.http_parser import HTTPParser
import json


class API:
    def __init__(self):
        self.port = CONTROLLER_PORT
        self.host = ""
        self.parser = HTTPParser()

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            s.bind((self.host, self.port))
            s.listen(1)
            request = "running"
            while request != b'kill':
                conn, addr = s.accept()
                with conn:
                    print('Connected by', addr)
                    i = 1
                    while True:
                        request = conn.recv(1024)
                        print("request", i, ": ", request)
                        if not request or request == b'kill':
                            break
                        data = json.loads(request)
                        print("data: ", data)
                        response = self.endpoints(data)
                        conn.sendall(json.dumps(response).encode())
                        i += 1

    def endpoints(self, request: dict) -> dict:
        return {"TODO": True}


if __name__ == "__main__":
    API().run()
