from typing import List


class Node:
    def __init__(self):
        self._parent: Node = self
        self._children: List[Node] = []

    def add_child(self, child):
        child.set_parent(self)
        self._children.append(child)

    def set_parent(self, parent):
        self._parent = parent

    def get_parent(self):
        return self._parent

    def get_child(self, child_cls: object):
        for child in self._children:
            if child.__class__.__name__ == child_cls.__name__:
                return child
        return None

    def get_children(self):
        return self._children

    def close(self):
        for child in self._children:
            child.close()
