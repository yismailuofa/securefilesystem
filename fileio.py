import os
from typing import Optional
from encrypt import encryptString, decryptString


FILE_PATH = "files/"


class PathReadResult:
    def __init__(self, maybeEncryptedName) -> None:
        self.encryptedName = maybeEncryptedName
        try:
            self.name = decryptString(maybeEncryptedName)
        except:
            self.name = maybeEncryptedName

    def __repr__(self) -> str:
        return f"PathReadResult(name={self.name}, encryptedName={self.encryptedName})"


def findPath(path: str, curr: str = FILE_PATH) -> Optional[str]:
    """Given path and current directory, return the encrypted path.
    Default current directory is the root file directory.
    If no match is found, return None
    """

    if not path:
        return curr

    first, *rest = [part for part in path.split("/") if part]
    for dir in os.listdir(curr):
        try:
            if decryptString(dir) == first:
                return findPath("/".join(rest), os.path.join(curr, dir))
        except:
            pass

    return None


def makePath(path: str, curr: str = FILE_PATH, isFile: bool = False) -> str:
    """Given a non-encrypted path, create the encrypted path and return it.
    If the parts of the path do not exist, create them"""

    if not path:
        return curr

    first, *rest = path.split("/")

    if not rest and isFile:
        return os.path.join(curr, encryptString(first))

    for dir in os.listdir(curr):
        try:
            if decryptString(dir) == first:
                return makePath("/".join(rest), os.path.join(curr, dir), isFile)
        except:
            pass

    newDir = os.path.join(curr, encryptString(first))
    os.mkdir(newDir)

    return makePath("/".join(rest), newDir, isFile)


def readFile(path: str) -> str:
    """Given a non-encrypted path, return the contents of the file"""

    if not (path := findPath(path)):
        raise FileNotFoundError
    elif os.path.isdir(path):
        raise IsADirectoryError

    with open(path, "rb") as f:
        return decryptString(f.read().decode())


def readPath(path: str) -> list[PathReadResult]:
    """Given a non-encrypted path, return the contents of the directory"""

    if not (path := findPath(path)):
        raise FileNotFoundError
    elif os.path.isfile(path):
        raise NotADirectoryError

    return [PathReadResult(encryptedName) for encryptedName in os.listdir(path)]


def writeFile(path: str, contents: str):
    """Given a non-encrypted path, write the contents to the file
    If the file or path does not exist, create it
    """

    if not (writePath := findPath(path)):
        writePath = makePath(path, isFile=True)

    with open(writePath, "wb") as f:
        f.write(encryptString(contents).encode())


def removeFile(path: str):
    """Given a non-encrypted path, remove the file
    If the file does not exist, raise FileNotFoundError
    """

    if not (path := findPath(path)):
        raise FileNotFoundError
    elif os.path.isdir(path):
        raise IsADirectoryError

    os.remove(path)


def removePath(path: str):
    """Given a non-encrypted path, remove the directory
    If the directory does not exist, raise FileNotFoundError
    The directory must be empty.
    """

    if not (path := findPath(path)):
        raise FileNotFoundError
    elif os.path.isfile(path):
        raise NotADirectoryError

    os.rmdir(path)


def renamePath(oldPath: str, name: str):
    """Given a non-encrypted old path and a non-encrypted new path, rename the directory
    If the directory does not exist, raise FileNotFoundError
    """

    if not (oldPath := findPath(oldPath)):
        raise FileNotFoundError

    encryptedName = encryptString(name)

    newPath = os.path.join(os.path.dirname(oldPath), encryptedName)

    os.rename(oldPath, newPath)


if __name__ == "__main__":
    writeFile("foo/test.txt", "Hello, World!")

    renamePath("foo/test.txt", "baz.txt")

    print(readPath("foo"))

    # print(readFile("foo/baz/test.txt"))

    removeFile("foo/baz.txt")

    removePath("foo")
