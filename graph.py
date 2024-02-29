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
        self, name: str, owner: str, isFolder: bool, allowedUsers=[], allowedGroups=[], children=[]
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
    
    def getReadableSubNodes(self, user: str, groups: list[str]) -> list[str]:
        "Returns list of subnodes that are readable for a specific user"
        readable = []
        for child in self.children:
            if child.isReadable(user, groups):
                readable.append(child.name)

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

        # not sure if this will recursively dump the whole graph
        out = {
            "name": self.root.name,
            "owner": self.root.owner,
            "isFolder": self.root.isFolder,
            "allowedUsers": [p.__dict__ for p in self.root.allowedUsers],
            "allowedGroups": [p.__dict__ for p in self.root.allowedGroups],
            "children": [c.__dict__ for c in self.root.children]
        }

        with open(self.jsonPath, "w") as f:
            json.dump(out, f, indent=4)

    def __del__(self):
        self.dump()

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
                raise ValueError(f"Path {path} not found")
    
        return node

    def createFolder(self, path: str, currentUser: str, currentGroups: list[str]) -> bool:
        "Creates a folder at a specific path"
        path = path.split("/")[1:]
        node = self.root
        for p in path:
            for child in node.children:
                if child.name == p:
                    node = child
                    break
            else:
                if not node.isWritable(currentUser, currentGroups):
                    return False
                else:
                    # create a new folder, copying permissions from parent
                    node.children.append(Node(p, node.owner, True, node.allowedUsers, node.allowedGroups))
                    node = node.children[-1]
        
        return True
    
    def createFile(self, path: str, currentUser: str, currentGroups: list[str]) -> bool:
        "Creates a file at a specific path"
        path = path.split("/")[1:]
        node = self.root
        for p in path:
            for child in node.children:
                if child.name == p:
                    node = child
                    break
            else:
                if not node.isWritable(currentUser, currentGroups):
                    return False
                else:
                    # create a new file, copying permissions from parent
                    node.children.append(Node(p, node.owner, False, node.allowedUsers, node.allowedGroups))
                    node = node.children[-1]
                    return True
        
        return False
    
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
                            child.allowedUsers.append(Permission(targetUser, True, False))
                    node = child
                    break
            else:
                raise ValueError(f"Path {path} not found")
        
        return True
    
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
                            child.allowedUsers.append(Permission(targetUser, True, False))
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
    
    def makeReadableForGroup(self, path: str, currentUser: str, targetGroup: str) -> bool:
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
                            child.allowedGroups.append(Permission(targetGroup, True, False))
                    node = child
                    break
            else:
                raise ValueError(f"Path {path} not found")
        
        return True
    
    def makeWritableForGroup(self, path: str, currentUser: str, targetGroup: str) -> bool:
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
                            child.allowedGroups.append(Permission(targetGroup, True, False))
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
if __name__ == "__main__":
    graph = Graph("json/permissions.example.json")
