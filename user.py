import json


class User:
    def __init__(self, name: str, password: str, joinedGroups=[]) -> None:
        self.name: str = name
        self.password: str = password
        self.joinedGroups: list[str] = joinedGroups

    def __repr__(self) -> str:
        return f"User(name={self.name}, password={self.password}, joinedGroups={self.joinedGroups}, ownedGroups={self.ownedGroups})"


class Users:
    def __init__(self, jsonPath="json/users.json"):
        self.jsonPath = jsonPath

        with open(jsonPath, "r") as f:
            users = json.load(f)

            self.users = {name: User(name, **user) for name, user in users.items()}

            print("Loaded users from users.json")
            print(self.users)

    def dump(self):
        "Dumps users to a file, should be called on exit"

        print("Dumping users to ", self.jsonPath)

    def __del__(self):
        self.dump()


if __name__ == "__main__":
    users = Users("json/users.example.json")
