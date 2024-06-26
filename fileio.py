import os
from typing import Optional
from encrypt import Encryptor



FILE_PATH = "files/"
encryptor = Encryptor()


class PathReadResult:
    def __init__(self, maybeEncryptedName, isFolder=False) -> None:
        self.encryptedName = maybeEncryptedName
        self.isFolder = isFolder
        try:
            self.name = encryptor.decryptString(maybeEncryptedName)
        except:
            self.name = maybeEncryptedName

    def __repr__(self) -> str:
        return f"PathReadResult(name={self.name}, encryptedName={self.encryptedName}) isFolder={self.isFolder}"


def findPath(path: str, curr: str = FILE_PATH) -> Optional[str]:
    """Given path and current directory, return the encrypted path.
    Default current directory is the root file directory.
    If no match is found, return None
    """

    if not path or path == "/":
        return curr

    first, *rest = [part for part in path.split("/") if part]
    for dir in os.listdir(curr):
        try:
            if encryptor.decryptString(dir) == first:
                return findPath("/".join(rest), os.path.join(curr, dir))
        except:
            pass

    return None


def isFolder(path) -> bool:
    """Given a non-encrypted path, return True if the path is a directory
    If the path does not exist, return False
    """

    if not (path := findPath(path)):
        return False

    return os.path.isdir(path)


def makePath(path: str, curr: str = FILE_PATH, isFile: bool = False) -> str:
    """Given a non-encrypted path, create the encrypted path and return it.
    If the parts of the path do not exist, create them"""

    if not path:
        return curr

    first, *rest = path.split("/")

    if not rest and isFile:
        return os.path.join(curr, encryptor.encryptString(first))

    for dir in os.listdir(curr):
        try:
            if encryptor.decryptString(dir) == first:
                return makePath("/".join(rest), os.path.join(curr, dir), isFile)
        except:
            pass

    newDir = os.path.join(curr, encryptor.encryptString(first))
    os.mkdir(newDir)

    return makePath("/".join(rest), newDir, isFile)


def readFile(path) -> str:
    """Given a non-encrypted path, return the contents of the file"""

    if not (path := findPath(path)):
        raise FileNotFoundError
    elif os.path.isdir(path):
        raise IsADirectoryError

    with open(path, "rb") as f:
        return encryptor.decryptString(f.read().decode())


def readPath(path) -> list[PathReadResult]:
    """Given a non-encrypted path, return the contents of the directory"""

    if not (path := findPath(path)):
        raise FileNotFoundError
    elif os.path.isfile(path):
        raise NotADirectoryError

    return [PathReadResult(dir.name, dir.is_dir()) for dir in os.scandir(path)]


def writeFile(path: str, contents: str):
    """Given a non-encrypted path, write the contents to the file
    If the file or path does not exist, create it
    """

    if not (writePath := findPath(path)):
        writePath = makePath(path, isFile=True)

    with open(writePath, "wb") as f:
        f.write(encryptor.encryptString(contents).encode())


def removeFile(path):
    """Given a non-encrypted path, remove the file
    If the file does not exist, raise FileNotFoundError
    """

    if not (path := findPath(path)):
        raise FileNotFoundError
    elif os.path.isdir(path):
        raise IsADirectoryError

    os.remove(path)


def removePath(path):
    """Given a non-encrypted path, remove the directory
    If the directory does not exist, raise FileNotFoundError
    The directory must be empty.
    """

    if not (path := findPath(path)):
        raise FileNotFoundError
    elif os.path.isfile(path):
        raise NotADirectoryError

    os.rmdir(path)


def renamePath(oldPath, name: str):
    """Given a non-encrypted old path and a non-encrypted new path, rename the directory
    If the directory does not exist, raise FileNotFoundError
    """

    if not (oldPath := findPath(oldPath)):
        raise FileNotFoundError

    encryptedName = encryptor.encryptString(name)

    newPath = os.path.join(os.path.dirname(oldPath), encryptedName)

    os.rename(oldPath, newPath)
