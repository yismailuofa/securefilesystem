from cryptography.fernet import Fernet
import json


ENCRYPTION_PREFIX = "encrypted_"


def key():
    with open("fernet.key", "r") as f:
        key = f.read()
        return key


def encryptJson(data, outFile: str):
    fernet = Fernet(key())

    data = json.dumps(data).encode()

    *path, fileName = outFile.split("/")
    outFile = "/".join(path) + "/" + ENCRYPTION_PREFIX + fileName

    with open(outFile, "wb") as f:
        f.write(fernet.encrypt(data))


def decryptJson(inFile: str) -> dict:
    fernet = Fernet(key())

    with open(inFile, "rb") as f:
        data = f.read()

    return json.loads(fernet.decrypt(data))


def encryptString(data: str) -> str:
    fernet = Fernet(key())

    return fernet.encrypt(data.encode()).decode()


def decryptString(data: str) -> str:
    fernet = Fernet(key())

    return fernet.decrypt(data.encode()).decode()


def isEncrypted(filePath: str) -> bool:
    return filePath.split("/")[-1].startswith(ENCRYPTION_PREFIX)


if __name__ == "__main__":
    with open("json/permissions.example.json", "r") as f:
        data = json.load(f)
        encryptJson(data, "json/permissions.json")

    with open("json/users.example.json", "r") as f:
        data = json.load(f)
        encryptJson(data, "json/users.json")
