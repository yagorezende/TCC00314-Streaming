import socket
from server_side.util.constants import CONTROLLER_PORT
import json


class API:
    def __init__(self):
        self.port = CONTROLLER_PORT
        self.host = ""

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
        _type = request["request"]
        if _type == "GET_USER_INFORMATION":
            return self._get_user_information(request)
        elif _type == "ENTRAR_NA_APP":
            return self._login_or_create_user(request)
        elif _type == "SAIR_DA_APP_":
            return self._logout_or_remove(request)

    def _get_user_information(self, request: dict) -> dict:
        _type = "USER_INFORMATION"
        return {"answer": _type}

    def _login_or_create_user(self, request: dict) -> dict:
        _type = ["ENTRAR_NA_APP_ACK", "STATUS_DO_USUARIO"]
        return {"answer": _type}

    def _logout_or_remove(self, request: dict) -> dict:
        _type = "SAIR_DA_APP_ACK"
        return {"answer": _type}


if __name__ == "__main__":
    API().run()
