from cryptography.fernet import Fernet
import json


def key():
    with open("fernet.key", "r") as f:
        key = f.read()
        return key


def encryptJson(data: dict, outFile: str) -> bytes:
    fernet = Fernet(key())

    data = json.dumps(data).encode()

    with open("encrypted_" + outFile, "wb") as f:
        f.write(fernet.encrypt(data))


def decryptJson(inFile: str) -> dict:
    fernet = Fernet(key())

    with open(inFile, "rb") as f:
        data = f.read()

    return json.loads(fernet.decrypt(data))


if __name__ == "__main__":
    with open("json/permissions.example.json", "r") as f:
        data = json.load(f)

    encryptJson(data, "permissions.json")

    decoded = decryptJson("encrypted_permissions.json")

    assert data == decoded
    print("Success")
