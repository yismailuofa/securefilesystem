import os
from encrypt import encryptString, decryptString


FILE_PATH = "files/"


def readPathContents(path) -> str:
    """Given a non-encrypted path, return the contents of the file
    Since encryption is non-deterministic, we can't check if a file is encrypted or not.
    We walk through the file and try to decrypt it, if it fails, we assume it's not encrypted
    """

    curr = FILE_PATH
    tok = path.split("/")

    for t in tok:
        for dir in os.listdir(curr):
            try:
                if decryptString(dir) == t:
                    curr = os.path.join(curr, dir)
                    break
            except:
                pass
        else:
            raise FileNotFoundError(f"Could not find {path}")

    with open(curr, "rb") as f:
        return decryptString(f.read())


def writePathContents(path: str, contents: str):
    """Given a non-encrypted path, write the contents to the file
    Since encryption is non-deterministic, we can't check if a file is encrypted or not.
    We walk through the file and try to decrypt it, if it fails, we assume it's not encrypted
    """

    curr = FILE_PATH
    tok = path.split("/")

    for i, t in enumerate(tok):
        for dir in os.listdir(curr):
            try:
                if decryptString(dir) == t:
                    curr = os.path.join(curr, dir)
                    break
            except:
                pass
        else:
            curr = os.path.join(curr, encryptString(t).decode())

            if i != len(tok) - 1:
                os.mkdir(curr)

    with open(curr, "wb") as f:
        f.write(encryptString(contents))


if __name__ == "__main__":
    writePathContents("foo/bar/test.txt", "Hello, World!")

    print(readPathContents("foo/bar/test.txt"))
