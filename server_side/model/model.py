from util.constants import Service


class User:
    def __init__(self, name: str, _id=1, service=Service.GUEST):
        self.id = _id
        self.name = name
        self.service = service
        self.groups = []

    def upgrade_user(self):
        self.service = Service.PREMIUM

    def to_dict(self):
        answer = self.__dict__
        answer["service"] = Service.to_string(self.service)
        return answer

    def remove_group(self, gid):
        self.groups.remove(gid)


class Group:
    def __init__(self, name, _id=1):
        self.name = name
        self.id = _id
        self.members = []

    def remove_member(self, member_id: int):
        self.members.remove(member_id)

    def add_member(self, member_id: int):
        self.members.append(member_id)

    def to_dict(self):
        return self.__dict__
