from functools import wraps
import json

from encrypt import decryptJson, encryptJson, isEncrypted


class User:
    def __init__(self, name: str, password: str, joinedGroups=[]) -> None:
        self.name: str = name
        self.password: str = password
        self.joinedGroups: list[str] = joinedGroups
        self.isAdmin: bool = name == "admin"

    def __repr__(self) -> str:
        return f"User(name={self.name}, password={self.password}, joinedGroups={self.joinedGroups})"

    def dump(self) -> dict:
        "Dumps user to a file, should be called on exit"

        return {
            "name": self.name,
            "password": self.password,
            "joinedGroups": self.joinedGroups,
        }


class Users:
    def __init__(self, jsonPath: str) -> None:
        self.jsonPath = jsonPath
        self.isEncrypted = isEncrypted(jsonPath)

        with open(jsonPath, "r") as f:
            if self.isEncrypted:
                users = decryptJson(jsonPath)
            else:
                users = json.load(f)

            self.users = {user["name"]: User(**user) for user in users}

            print("Loaded users from users.json")

    def dump(self):
        "Dumps users to a file, should be called on exit"

        data = [user.dump() for user in self.users.items()]

        if self.isEncrypted:
            encryptJson(self.jsonPath, data)
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

    def getUsersInGroup(self, groupName: str):
        return [
            name for name, user in self.users.items() if groupName in user.joinedGroups
        ]

    @withDump
    def addUsersToGroup(self, groupName: str, added_users: list[str]):
        users_added = False
        for user in added_users:
            if user not in self.users:
                print(f"User {user} not found")
                continue

            if self.users[user].isAdmin and not users_added:
                print("No valid users provided, group creation failed")
                return False
            else:
                self.users[user].joinedGroups.append(groupName)
                users_added = True

            print(f"Added {user} to {groupName}")

        return True

    def deleteUsersFromGroup(self, groupName: str, deleted_users: list[str]):
        for user in deleted_users:
            if user not in self.users:
                print(f"User {user} not found")
                continue

            if groupName not in self.users[user].joinedGroups:
                print(f"User {user} is not in {groupName}")
                continue

            if self.users[user].isAdmin:
                print(f"User {user} is an admin and cannot be removed from {groupName}")
                continue

            self.users[user].joinedGroups.remove(groupName)
            print(f"Removed {user} from {groupName}")


if __name__ == "__main__":
    users = Users("json/users.example.json")
