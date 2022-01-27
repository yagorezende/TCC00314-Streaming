import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STREAMING_PORT = 6000
CONTROLLER_PORT_STREAMING = 5000
CONTROLLER_PORT_CLIENT = 6060
QUALITY = {"720p": 1280, "480p": 854, "240p": 426}
DATABASE = {
    "path":  os.path.join(BASE_DIR, 'db.sqlite3')
}


class Service:
    PREMIUM = 1
    GUEST = 2

    def to_string(value):
        if isinstance(value, int):
            return {Service.PREMIUM: "premium", Service.GUEST: "guest"}[value]
        return value

if __name__ == "__main__":
    print("db path ->", DATABASE['path'])
