import json


class Permission:
    def __init__(self, name, isRead, isWrite) -> None:
        self.name: str = name
        self.isRead: bool = isRead
        self.isWrite: bool = isWrite

    def __repr__(self) -> str:
        return f"Permission(name={self.name}, isRead={self.isRead}, isWrite={self.isWrite})"


class Node:

    def __init__(
        self, name: str, isFolder: bool, allowedUsers=[], allowedGroups=[], children=[]
    ) -> None:
        self.name = name
        self.children = [Node(**child) for child in children]
        self.isFolder = isFolder
        self.allowedUsers: list[Permission] = [
            Permission(**user) for user in allowedUsers
        ]
        self.allowedGroups: list[Permission] = [
            Permission(**group) for group in allowedGroups
        ]

    def __repr__(self) -> str:
        return f"Node(name={self.name}, isFolder={self.isFolder}, allowedUsers={[p.name for p in self.allowedUsers]}, allowedGroups={[p.name for p in self.allowedGroups]}, children={[c.name for c in self.children]})"


class Graph:
    def __init__(self, jsonPath="json/permissions.json"):
        self.jsonPath = jsonPath

        with open(jsonPath, "r") as f:
            graph = json.load(f)

            self.root = Node(**graph)

            print("Loaded graph from permissions.json")
            print(self.root)

    def dump(self):
        "Dumps graph to a file, should be called on exit"

        print("Dumping graph to ", self.jsonPath)

    def __del__(self):
        self.dump()


if __name__ == "__main__":
    graph = Graph("json/permissions.example.json")
