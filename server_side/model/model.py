import random
from typing import List

from server_side.util.constants import Service


class User:
    def __init__(self, _id=1, service=Service.PREMIUM):
        self.id = _id
        self.passcode = random.randint(1000, 9999)
        self.service = service
        self.group: List[int] = []  # list of ids

    def save(self):
        pass
