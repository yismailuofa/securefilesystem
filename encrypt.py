from cryptography.fernet import Fernet
import json


ENCRYPTION_PREFIX = "encrypted_"


# make a singleton Encryptor class
class Encryptor:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Encryptor, cls).__new__(cls)
            cls.__instance.fernet = Fernet(cls.__instance.key())
        return cls.__instance

    def key(self):
        with open("fernet.key", "r") as f:
            key = f.read()
            return key

    def encryptJson(self, data, outFile: str):
        data = json.dumps(data).encode()

        *path, fileName = outFile.split("/")

        if fileName.startswith(ENCRYPTION_PREFIX):
            fileName = fileName[len(ENCRYPTION_PREFIX) :]

        outFile = "/".join(path) + "/" + ENCRYPTION_PREFIX + fileName

        with open(outFile, "wb") as f:
            f.write(self.fernet.encrypt(data))

    def decryptJson(self, inFile: str) -> dict:
        with open(inFile, "rb") as f:
            data = f.read()

        return json.loads(self.fernet.decrypt(data))

    def encryptString(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decryptString(self, data: str) -> str:
        return self.fernet.decrypt(data.encode()).decode()

    def isEncrypted(self, filePath: str) -> bool:
        return filePath.split("/")[-1].startswith(ENCRYPTION_PREFIX)


if __name__ == "__main__":
    # initialize the encryptor
    encryptor = Encryptor()

    # encrypt the json files
    with open("json/permissions.example.json", "r") as f:
        data = json.load(f)
        encryptor.encryptJson(data, "json/permissions.json")

    with open("json/users.example.json", "r") as f:
        data = json.load(f)
        encryptor.encryptJson(data, "json/users.json")
