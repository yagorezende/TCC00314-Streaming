import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STREAMING_PORT = 6000
CONTROLLER_PORT = 5000
DATABASE = {
    "path":  os.path.join(BASE_DIR, 'db.sqlite3')
}


class Service:
    PREMIUM = 1
    GUEST = 2


if __name__ == "__main__":
    print("db path ->", DATABASE['path'])
