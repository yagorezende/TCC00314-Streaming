from server_side.api.api import API
from server_side.model.node import Node
from server_side.util.constants import CONTROLLER_PORT_CLIENT, CONTROLLER_PORT_STREAMING


class Main(Node):
    def __init__(self):
        super().__init__()
        self.steaming_api = API(CONTROLLER_PORT_STREAMING)
        self.client_api = API(CONTROLLER_PORT_CLIENT)
        self.add_child(self.steaming_api)
        self.add_child(self.client_api)

    def start(self):
        self.steaming_api.run()
        self.client_api.run()
        return self

    def run(self):
        try:
            while True:
                opt = input("opt: ")
                if opt == "exit":
                    self.close()
                    exit(0)
        except Exception as e:
            print(e)
        finally:
            self.close()
            exit(1)
        print("running")


if __name__ == "__main__":
    Main().start().run()
