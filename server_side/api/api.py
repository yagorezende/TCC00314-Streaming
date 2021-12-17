import socket
import json
import threading

from server_side.model.node import Node


class API(Node):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.host = ""
        self._server_thread = None
        self.request = None
        self.server = None

    def run(self):
        self._server_thread = threading.Thread(target=self._open_server)
        self._server_thread.start()

    def _open_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            s.bind((self.host, self.port))
            s.listen(1)
            self.server = s
            self.request = "running"
            while self.request != b'kill':
                conn, addr = s.accept()
                with conn:
                    print('Connected by', addr)
                    i = 1
                    while True:
                        self.request = conn.recv(1024)
                        print("request", i, ": ", self.request)
                        if not self.request or self.request == b'kill':
                            break
                        data = json.loads(self.request)
                        print("data: ", data)
                        response = self.endpoints(data)
                        conn.sendall(json.dumps(response).encode())
                        i += 1

    def endpoints(self, request: dict) -> dict:
        try:
            _type = request["request"]
            if _type == "GET_USER_INFORMATION":
                return self._get_user_information(request)
            elif _type == "ENTRAR_NA_APP":
                return self._login_or_create_user(request)
            elif _type == "SAIR_DA_APP":
                return self._logout_or_remove(request)
        except Exception as e:
            print(e)

    def _get_user_information(self, request: dict) -> dict:
        _type = "USER_INFORMATION"
        return {"answer": _type}

    def _login_or_create_user(self, request: dict) -> dict:
        _type = ["ENTRAR_NA_APP_ACK", "STATUS_DO_USUARIO"]
        return {"answer": _type}

    def _logout_or_remove(self, request: dict) -> dict:
        _type = "SAIR_DA_APP_ACK"
        return {"answer": _type}

    def close(self):
        if self._server_thread:
            self.request = b'kill'
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            self._server_thread.join()
        print("Server closed")


if __name__ == "__main__":
    API(5000).run()
