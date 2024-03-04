import json
from encrypt import decryptJson, encryptJson, isEncrypted, encryptString
from functools import wraps
import copy
import fileio


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
        isFolder: bool,
        allowedUsers: list[dict] = [],
        allowedGroups: list[dict] = [],
        children=[],
    ) -> None:
        self.name = name
        self.owner = owner
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

    def dump(self) -> dict:
        "Dumps node to a dictionary"

        return {
            "name": self.name,
            "owner": self.owner,
            "isFolder": self.isFolder,
            "allowedUsers": [p.dump() for p in self.allowedUsers],
            "allowedGroups": [p.dump() for p in self.allowedGroups],
            "children": [c.dump() for c in self.children],
        }

    def getReadableSubNodes(self, user: str, groups: list[str], path: str) -> list[str]:
        "Returns list of subnodes that are readable for a specific user"
        results = {p.name: p for p in fileio.readPath(path)}

        readable = []
        for child in self.children:
            if child.isReadable(user, groups):
                # if child is a folder, add a / to the end
                if child.isFolder:
                    readable.append(child.name + "/")
                else:
                    readable.append(child.name)
            else:
                readable.append(results[child.name].encryptedName)

        return readable

    def isReadable(self, user: str, groups: list[str]) -> bool:
        "Returns if a node is readable for a specific user"
        for permission in self.allowedUsers:
            if permission.name == user and permission.isRead:
                return True

        for permission in self.allowedGroups:
            if permission.name in groups and permission.isRead:
                return True

        return False

    def isWritable(self, user: str, groups: list[str]) -> bool:
        "Returns if a node is writable for a specific user"
        for permission in self.allowedUsers:
            if permission.name == user and permission.isWrite:
                return True

        for permission in self.allowedGroups:
            if permission.name in groups and permission.isWrite:
                return True

        return False

    def isOwner(self, user: str) -> bool:
        "Returns if a user is the owner of a node"
        return self.owner == user


class Graph:
    def __init__(self, jsonPath: str):
        self.jsonPath = jsonPath
        self.isEncrypted = isEncrypted(jsonPath)

        with open(jsonPath, "r") as f:
            if self.isEncrypted:
                graph = decryptJson(jsonPath)
            else:
                graph = json.load(f)

            self.root = Node(**graph)

    def dump(self):
        "Dumps graph to a file, should be called on exit"

        data = self.root.dump()

        if self.isEncrypted:
            encryptJson(data, self.jsonPath)
        else:
            with open(self.jsonPath, "w") as f:
                json.dump(data, f, indent=2)

    def withDump(func):
        "Decorator to dump graph after function call"

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.dump()
            return result

        return wrapper

    @withDump
    def getNodeFromPath(self, path: str) -> Node:
        "Returns node from path"

        if path == "/":
            return self.root

        path = path.split("/")[1:]
        node = self.root
        for p in path:
            for child in node.children:
                if child.name == p:
                    node = child
                    break
            else:
                return None

        return node

    @withDump
    def createFolder(
        self, path: str, currentUser: str, currentGroups: list[str]
    ) -> bool:
        "Creates a folder at a specific path"
        path = [part for part in path.split("/") if part]
        os_path = ""
        node = self.root
        for p in path:
            for child in node.children:
                if child.name == p:
                    node = child
                    os_path += node.name + "/"
                    break
            else:
                if not node.isWritable(currentUser, currentGroups):
                    return False
                else:
                    # create a new folder, copying permissions from parent
                    child = copy.deepcopy(node)
                    child.name = p
                    child.children.clear()
                    child.allowedGroups.clear()
                    node.children.append(child)
                    node = node.children[-1]
                    
                    # create path in OS
                    os_path += node.name
                    fileio.makePath(os_path)
                    os_path += "/"

        return True

    @withDump
    def initUserDirectory(self, user: str):
        "Initializes the user directory"
        self.root.children.append(
            Node(user, user, True, [Permission(user, True, True).dump()], [])
        )
        fileio.makePath(user, isFile=False)

    @withDump
    def createFile(self, path: str, currentUser: str, currentGroups: list[str]) -> bool:
        "Creates a file at a specific path"
        path = [part for part in path.split("/") if part]
        node = self.root
        os_path = ""
        for i in range(len(path)):
            p = path[i]
            print(f"os path: {os_path}")
            print(f"node: {node}")
            for child in node.children:
                if child.name == p:
                    node = child
                    os_path += node.name + "/"
                    break
            else:
                if not node.isWritable(currentUser, currentGroups):
                    return False
                else:
                    # create a new file, copying permissions from parent
                    child = copy.deepcopy(node)
                    child.name = p
                    child.children.clear()
                    child.isFolder = False if i == (len(path) - 1) else True
                    node.children.append(child)
                    node = node.children[-1]
                    
                    # create path in OS
                    os_path += node.name
                    fileio.makePath(os_path, isFile = True if i == (len(path) - 1) else False)
                    os_path += "/"
                    return True

        return False

    @withDump
    def makeReadableForUser(self, path: str, currentUser: str, targetUser: str) -> bool:
        "Makes a node readable for a specific user"
        # travel down the path and make nodes readable on the way
        path = path.split("/")[1:]
        node = self.root
        for p in path:
            for child in node.children:
                if child.name == p:
                    if not child.isOwner(currentUser):
                        return False
                    else:
                        for permission in child.allowedUsers:
                            if permission.name == targetUser:
                                permission.isRead = True
                                return True
                        else:
                            child.allowedUsers.append(
                                Permission(targetUser, True, False)
                            )
                    node = child
                    break
            else:
                raise ValueError(f"Path {path} not found")

        return True

    @withDump
    def makeWritableForUser(self, path: str, currentUser: str, targetUser: str) -> bool:
        "Makes a node writable for a specific user"
        # travel down the path and make nodes readable on the way
        path = path.split("/")[1:]
        node = self.root
        for p in path:
            for child in node.children:
                if child.name == p:
                    if not child.isOwner(currentUser):
                        return False
                    else:
                        for permission in child.allowedUsers:
                            if permission.name == targetUser:
                                permission.isRead = True
                                return True
                        else:
                            child.allowedUsers.append(
                                Permission(targetUser, True, False)
                            )
                    node = child
                    break
            else:
                raise ValueError(f"Path {path} not found")

        # make the last node writable
        for permission in node.allowedUsers:
            if permission.name == targetUser:
                permission.isWrite = True
                return True
        else:
            node.allowedUsers.append(Permission(targetUser, True, True))
            return True

    @withDump
    def makeReadableForGroup(
        self, path: str, currentUser: str, targetGroup: str
    ) -> bool:
        "Makes a node readable for a specific group"
        # travel down the path and make nodes readable on the way
        path = path.split("/")[1:]
        node = self.root
        for p in path:
            for child in node.children:
                if child.name == p:
                    if not child.isOwner(currentUser):
                        return False
                    else:
                        for permission in child.allowedGroups:
                            if permission.name == targetGroup:
                                permission.isRead = True
                                return True
                        else:
                            child.allowedGroups.append(
                                Permission(targetGroup, True, False)
                            )
                    node = child
                    break
            else:
                raise ValueError(f"Path {path} not found")

        return True

    @withDump
    def makeWritableForGroup(
        self, path: str, currentUser: str, targetGroup: str
    ) -> bool:
        "Makes a node writable for a specific group"
        # travel down the path and make nodes readable on the way
        path = path.split("/")[1:]
        node = self.root
        for p in path:
            for child in node.children:
                if child.name == p:
                    if not child.isOwner(currentUser):
                        return False
                    else:
                        for permission in child.allowedGroups:
                            if permission.name == targetGroup:
                                permission.isRead = True
                                return True
                        else:
                            child.allowedGroups.append(
                                Permission(targetGroup, True, False)
                            )
                    node = child
                    break
            else:
                raise ValueError(f"Path {path} not found")

        # make the last node writable
        for permission in node.allowedGroups:
            if permission.name == targetGroup:
                permission.isWrite = True
                return True
        else:
            node.allowedGroups.append(Permission(targetGroup, True, True))
            return True

    @withDump
    def deleteGroup(self, groupName: str) -> bool:
        "Deletes a group from all nodes"

        def deleteGroupFromNode(node: Node):
            for permission in node.allowedGroups:
                if permission.name == groupName:
                    node.allowedGroups.remove(permission)
                    print("Deleted group from ", node)
                    break
            for child in node.children:
                deleteGroupFromNode(child)

        deleteGroupFromNode(self.root)

    @withDump
    def renameNode(self, path: str, newName: str) -> bool:
        "Renames a node"
        tok = path.split("/")[1:]
        node = self.root
        for p in tok:
            for child in node.children:
                if child.name == p:
                    node = child
                    break
            else:
                return False

        node.name = newName

        fileio.renamePath(path, newName)

        return True


if __name__ == "__main__":
    graph = Graph("json/permissions.example.json")