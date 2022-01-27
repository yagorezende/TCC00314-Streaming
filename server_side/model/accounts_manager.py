from typing import List

from model.model import User, Group
from model.node import Node


class AccountsManager(Node):
    users: List[User] = []
    groups: List[Group] = []

    def __init__(self):
        super().__init__()

    def add_user(self, name) -> User:
        user = User(name, _id=len(self.users))
        self.users.append(user)
        return user

    def get_user(self, _id) -> User:
        return self.users[_id]

    def get_user_by_name(self, user_name):
        for user in self.users:
            if user.name == user_name:
                return user
        return None

    def remove_user(self, _id):
        user = self.users.pop(_id)
        for group in user.groups:
            self.remove_group_member(group, user.id)

    def upgrade_user(self, _id):
        self.users[_id].upgrade_user()

    def add_group(self, group_name) -> int:
        group = Group(group_name, _id=len(self.groups))
        self.groups.append(group)
        return group.id

    def get_groups(self) -> int:
        return self.groups

    def get_user_from_group(self, gid: int):
        return self.groups[gid]

    def add_user_to_group(self, group_id, user_id):
        self.groups[group_id].members.append(user_id)
        self.users[user_id].groups.append(group_id)

    def remove_group_member(self, _gid: int, _uid: int):
        self.groups[_gid].remove_member(_uid)
        self.users[_uid].remove_group(_gid)