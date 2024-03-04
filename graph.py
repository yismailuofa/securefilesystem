import json
from typing import Optional
from encrypt import decryptJson, encryptJson, isEncrypted
import fileio
from user import User


class Permission:
    def __init__(self, name, isRead, isWrite) -> None:
        self.name: str = name
        self.isRead: bool = isRead
        self.isWrite: bool = isWrite

    def __repr__(self) -> str:
        return f"Permission(name={self.name}, isRead={self.isRead}, isWrite={self.isWrite})"

    def dump(self) -> dict:
        return {
            "name": self.name,
            "isRead": self.isRead,
            "isWrite": self.isWrite,
        }


class Node:

    def __init__(
        self,
        name: str,
        owner: str,
        allowedUsers: list[dict] = [],
        allowedGroups: list[dict] = [],
    ) -> None:
        self.name = name
        self.owner = owner
        self.allowedUsers: list[Permission] = [
            Permission(**user) for user in allowedUsers
        ]
        self.allowedGroups: list[Permission] = [
            Permission(**group) for group in allowedGroups
        ]

    def __repr__(self) -> str:
        return f"Node(name={self.name}, allowedUsers={[p.name for p in self.allowedUsers]}, allowedGroups={[p.name for p in self.allowedGroups]}"

    def dump(self) -> dict:
        "Dumps node to a dictionary"

        return {
            "name": self.name,
            "owner": self.owner,
            "allowedUsers": [p.dump() for p in self.allowedUsers],
            "allowedGroups": [p.dump() for p in self.allowedGroups],
        }

    def isReadable(self, user: User) -> bool:
        "Returns if a node is readable for a specific user"
        if self.isOwner(user) or user.isAdmin:
            return True

        for permission in self.allowedUsers:
            if permission.name in [user.name, "all"] and permission.isRead:
                return True

        for permission in self.allowedGroups:
            if permission.name in user.joinedGroups and permission.isRead:
                return True

        return False

    def isWritable(self, user: User) -> bool:
        "Returns if a node is writable for a specific user"
        if self.isOwner(user) or user.isAdmin:
            return True

        for permission in self.allowedUsers:
            if permission.name in [user.name, "all"] and permission.isWrite:
                return True

        for permission in self.allowedGroups:
            if permission.name in user.joinedGroups and permission.isWrite:
                return True

        return False

    def isOwner(self, user: User) -> bool:
        "Returns if a user is the owner of a node"
        return self.owner == user.name
    
    def addGroup(self, groupName: str, isRead: bool, isWrite: bool):
        self.allowedGroups.append(
            Permission(groupName, isRead=isRead, isWrite=isWrite)
        )
        
    def addUser(self, user: str, isRead: bool, isWrite: bool):
        self.allowedUsers.append(
            Permission(user, isRead=isRead, isWrite=isWrite)
        )


class Graph:
    def __init__(self, jsonPath: str):
        self.jsonPath = jsonPath
        self.isEncrypted = isEncrypted(jsonPath)

        with open(jsonPath, "r") as f:
            if self.isEncrypted:
                graph = decryptJson(jsonPath)
            else:
                graph = json.load(f)

            self.nodes = {node["name"]: Node(**node) for node in graph}

    def dump(self):
        "Dumps graph to a file, should be called on exit"

        data = [node.dump() for node in self.nodes.values()]

        if self.isEncrypted:
            encryptJson(data, self.jsonPath)
        else:
            with open(self.jsonPath, "w") as f:
                json.dump(data, f, indent=2)

    def getNodeFromPath(self, path: str) -> Optional[Node]:
        "Returns node from path"

        return self.nodes.get(path, None)

    def listDirectory(self, path: str, user: User) -> list[str]:
        "Lists the directory at a specific path"

        if not (node := self.getNodeFromPath(path)):
            return []

        if not node.isReadable(user):
            return []

        results = fileio.readPath(path)
        out = []
        for res in results:
            resNode = self.getNodeFromPath("/".join(p for p in [path, res.name] if p))

            if resNode:
                name = ""
                if resNode.isReadable(user):
                    name = res.name
                else:
                    name = res.encryptedName

                if res.isFolder:
                    name += "/"

                out.append(name)

        return out

    def initUserDirectory(self, user: str):
        "Initializes the user directory"

        self.nodes[user] = Node(user, user, [Permission(user, True, True).dump()])

        fileio.makePath(user)

        self.dump()

    def createFile(self, path: str, user: User) -> bool:
        "Creates a file at a specific path"

        parentPath = "/".join(path.split("/")[:-1])

        if not (parent := self.getNodeFromPath(parentPath)):
            return False

        if not parent.isWritable(user):
            return False

        fileio.writeFile(path, "")

        allowedGroups = []
        allowedUsers = [
            Permission(user.name, True, True).dump(),
            Permission(parent.owner, True, True).dump(),
        ]

        self.nodes[path] = Node(path, user.name, allowedUsers, allowedGroups)

        self.dump()

        return True

    def createFolder(self, path: str, user: User) -> bool:
        "Creates a folder at a specific path"

        parentPath = "/".join(path.split("/")[:-1])

        if not (parent := self.getNodeFromPath(parentPath)):
            return False

        if not parent.isWritable(user):
            return False

        fileio.makePath(path, isFile=False)

        allowedGroups = []
        allowedUsers = [
            Permission(user.name, True, True).dump(),
            Permission(parent.owner, True, True).dump(),
        ]

        self.nodes[path] = Node(path, user.name, allowedUsers, allowedGroups)

        self.dump()

        return True

    def deleteGroup(self, groupName: str):
        "Deletes a group from all nodes"

        for k, v in self.nodes.items():
            for permission in v.allowedGroups:
                if permission.name == groupName:
                    self.nodes[k].allowedGroups.remove(permission)
                    print("Deleted group from ", v)

        self.dump()

    def renameNode(self, path: str, newName: str) -> bool:
        "Renames a node"

        if not (node := self.getNodeFromPath(path)):
            return False

        prePath = "/".join(path.split("/")[:-1])
        node.name = f"{prePath}/{newName}"

        self.nodes[node.name] = node
        del self.nodes[path]

        fileio.renamePath(path, newName)

        self.dump()

        return True


if __name__ == "__main__":
    graph = Graph("json/permissions.example.json")
