import socket
import json
import threading

from model.node import Node


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
            s.listen(10)
            self.server = s
            self.request = "running"
            while self.request != b'kill':
                conn, addr = s.accept()
                threading.Thread(target=self._process_connection, args=(conn, addr)).start()

    def endpoints(self, request: dict) -> dict:
        try:
            _type = request["request"]
            if _type == "GET_USER_INFORMATION":
                return self._get_user_information(request)
            elif _type == "ENTRAR_NA_APP":
                return self._login_or_create_user(request)
            elif _type == "SAIR_DA_APP":
                return self._logout_or_remove(request)
            elif _type == "CRIAR_GRUPO":
                return self._create_group(request)
            elif _type == "GET_GRUPOS":
                return self._get_groups(request)
            elif _type == "ADD_USUARIO_GRUPO":
                return self._add_user_to_group(request)
            elif _type == "VER_GRUPO":
                return self._get_group(request)
            elif _type == "REMOVER_USUARIO_GRUPO":
                return self._remove_user_from_group(request)
        except Exception as e:
            raise e

    def _get_user_information(self, request: dict) -> dict:
        _type = "USER_INFORMATION"
        user = self.get_parent().AM.get_user(request.get("id"))
        return {"answer": _type, "content": user.to_dict()}

    def _login_or_create_user(self, request: dict) -> dict:
        _type = ["ENTRAR_NA_APP_ACK", "STATUS_DO_USUARIO"]
        user = self.get_parent().AM.get_user_by_name(request.get("name"))
        if user is None:
            user = self.get_parent().AM.add_user(request.get("name"))
            if request.get("service") == "premium":
                self.get_parent().AM.upgrade_user(user.id)
            return {"answer": _type[0], "content": user.to_dict()}
        return {"answer": _type[1], "content": user.to_dict()}

    def _logout_or_remove(self, request: dict) -> dict:
        _type = "SAIR_DA_APP_ACK"
        self.get_parent().AM.remove_user(request.get("id"))
        return {"answer": _type}

    def _create_group(self, request: dict) -> dict:
        _type = "CRIAR_GRUPO_ACK"
        gid = self.get_parent().AM.add_group(request.get("name"))
        self.get_parent().AM.add_user_to_group(gid, request.get("id"))
        return {"answer": _type, "content": {"gid": gid}}

    def _get_groups(self, request: dict) -> dict:
        _type = "GET_GRUPOS_ACK"
        groups = self.get_parent().AM.get_groups()
        formatted = []
        for group in groups:
            formatted.append(group.to_dict())
        return {"answer": _type, "content": {"groups": formatted}}

    def _add_user_to_group(self, request: dict) -> dict:
        _type = "ADD_USUARIO_GRUPO_ACK"
        self.get_parent().AM.add_user_to_group(request.get("gid"), request.get("id"))
        return {"answer": _type}

    def _get_group(self, request: dict) -> dict:
        _type = "VER_GRUPO"
        group = self.get_parent().AM.get_user_from_group(request.get("gid"))
        return {"answer": _type, "content": group.to_dict()}

    def _remove_user_from_group(self, request: dict) -> dict:
        _type = "REMOVER_USUARIO_GRUPO_ACK"
        self.get_parent().AM.remove_group_member(request.get("gid"), request.get("id"))
        return {"answer": _type}

    def _process_connection(self, conn, addr):
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
                print("response: ", response)
                conn.sendall(json.dumps(response).encode())
                i += 1

    def close(self):
        if self._server_thread:
            self.request = b'kill'
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            self._server_thread.join()
        print("Server closed")


if __name__ == "__main__":
    API(5000).run()
