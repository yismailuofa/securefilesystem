import cmd
import argparse
import fileio
import bcrypt
import getpass
from graph import Graph
from user import Users
from fileio import readFile

from util import tryParse

prompt_template = "sfs> {user}@{curr_dir}$ "


class CLI(cmd.Cmd):
    # These are automatically set by cmd.Cmd
    intro = "Welcome to the Secure File System CLI. Type help or ? to list commands.\n"
    prompt = "sfs> "

    user = None
    graph = Graph("json/permissions.example.json")
    # graph = Graph("json/encrypted_permissions.json")
    curr_dir = ""
    users = Users("json/users.example.json")
    # users = Users("json/encrypted_users.json")

    def convertToAbsolutePath(self, path: str) -> str:
        "Converts a relative path to an absolute path"
        "tilde (~) will reset to the root directory"
        "otherwise, it will append to the current directory"

        if path.startswith("~"):
            path = path[1:]
        else:
            path = f"{self.curr_dir}/{path}"

        parts = [p for p in path.split("/") if p]
        out = []

        for part in parts:
            if part == ".." and out:
                out.pop()
            elif part != ".":
                out.append(part)

        return "/".join(out)

    def do_login(self, _):
        "Login to the system. Usage: login"

        if self.user:
            print("Please logout first")
            return

        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")

        if username not in self.users.users:
            print("User not found")
            return

        if not bcrypt.checkpw(
            password.encode(), self.users.users[username].password.encode()
        ):
            print("Invalid password")
            return

        self.user = self.users.users[username]
        self.curr_dir = f"{self.user.name}" if not self.user.isAdmin else ""
        self.prompt = prompt_template.format(
            user=self.user.name, curr_dir=self.curr_dir
        )

        print(f"Logged in as {self.user.name}")

        failures = self.graph.checkPathIntegrity(self.curr_dir)

        if failures:
            for failure in failures:
                print(f"File {failure} is corrupted ❌")
        else:
            print("No corrupted files found ✅")

    def do_register(self, _):
        "Register a new user. Usage: register"

        if self.user:
            print("Please logout first")
            return

        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if username in self.users.users:
            print("User already exists")
            return

        if password != confirm_password:
            print("Passwords don't match")
            return

        hashedPass = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.users.createUser(username, hashedPass.decode())

        self.user = self.users.users[username]

        self.curr_dir = f"/{self.user.name}" if not self.user.isAdmin else "/"
        self.prompt = prompt_template.format(
            user=self.user.name, curr_dir=self.curr_dir
        )

        self.graph.initUserDirectory(self.user.name)

        print(f"User {username} registered and logged in")

    def do_logout(self, _):
        "Logout of the system"
        self.user = None
        self.curr_dir = "/"
        self.prompt = "sfs> "
        print("Logged out")

    def do_quit(self, _):
        "Quit the CLI"
        return True

    def do_ls(self, _):
        "List files in the current directory"
        if self.user is None:
            print("Please login first")
            return

        print(
            *self.graph.listDirectory(self.curr_dir, self.user),
            sep="\n",
        )

    def do_cd(self, line):
        "Change the current directory"
        if self.user is None:
            print("Please login first")
            return

        parser = argparse.ArgumentParser(prog="cd")
        parser.add_argument("path", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        path = self.convertToAbsolutePath(args.path)

        if not (node := self.graph.getNodeFromPath(path)):
            print("Invalid path")
            return

        # now check if the user has access to the new directory
        if not node.isReadable(self.user):
            print("Access denied")
            return

        # now check if the node is a directory
        if not fileio.isFolder(path):
            print("Not a directory")
            return

        self.curr_dir = path
        self.prompt = prompt_template.format(
            user=self.user.name, curr_dir=self.curr_dir
        )

    def do_create_group(self, line):
        "Create a new group. Usage: create_group <group_name>"
        if self.user is None or not self.user.isAdmin:
            print("You need to be an admin to run this command")
            return
        parser = argparse.ArgumentParser(prog="create_group")
        parser.add_argument("group_name", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        if args.group_name in self.user.joinedGroups:
            print("Group already exists")
            return

        added_users = input(
            "Enter the names of the users to add to the group. Separate with a space: "
        ).split()
        added_users.append(self.user.name)

        if self.users.addUsersToGroup(args.group_name, added_users):
            print(
                f"Group {args.group_name} created with users: {self.users.getUsersInGroup(args.group_name)}"
            )

    def do_delete_group(self, line):
        "Delete a group. Usage: delete_group <group_name>"
        if self.user is None or not self.user.isAdmin:
            print("You need to be an admin to run this command")
            return
        parser = argparse.ArgumentParser(prog="create_group")
        parser.add_argument("group_name", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        if args.group_name not in self.user.joinedGroups:
            print("Group doesn't exist")
            return

        self.users.deleteUsersFromGroup(
            args.group_name, self.users.getUsersInGroup(args.group_name)
        )
        self.graph.deleteGroup(args.group_name)
        print(f"Group {args.group_name} deleted")

    def do_pwd(self, _):
        "Print the current working directory"
        if self.user is None:
            print("Please login first")
            return
        print(self.curr_dir)

    def do_cat(self, line):
        "Read the contents of a file. Usage: cat <file_path>"
        if self.user is None:
            print("Please login first")
            return
        parser = argparse.ArgumentParser(prog="cat")
        parser.add_argument("file_path", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        path = self.convertToAbsolutePath(args.file_path)

        if (node := self.graph.getNodeFromPath(path)) is None:
            print("Invalid path")
            return

        if not node.isReadable(self.user):
            print("Access denied")
            return

        print(readFile(path))

    def do_mv(self, line):
        "Rename a file or directory. Usage: mv <source> <name>"
        if self.user is None:
            print("Please login first")
            return

        parser = argparse.ArgumentParser(prog="mv")
        parser.add_argument("source", type=str)
        parser.add_argument("name", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        source = self.convertToAbsolutePath(args.source)

        if (node := self.graph.getNodeFromPath(source)) is None:
            print("Invalid source path")
            return

        if not node.isWritable(self.user):
            print("Access denied")
            return

        self.graph.renameNode(source, args.name)

    def do_mkdir(self, line):
        "Create a new directory. Usage: mkdir <dir_name>"
        if self.user is None:
            print("Please login first")
            return

        parser = argparse.ArgumentParser(prog="mkdir")
        parser.add_argument("dir_name", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        path = self.convertToAbsolutePath(args.dir_name)

        if self.graph.getNodeFromPath(path) is not None:
            print("Directory already exists")
            return

        self.graph.createFolder(path, self.user)

    def do_touch(self, line):
        "Create a new directory. Usage: touch <file_path>"
        if self.user is None:
            print("Please login first")
            return

        parser = argparse.ArgumentParser(prog="mkdir")
        parser.add_argument("file_path", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        path = self.convertToAbsolutePath(args.file_path)

        if self.graph.getNodeFromPath(path) is not None:
            print("File already exists")
            return

        if not self.graph.createFile(path, self.user):
            print("File creation failed")

    def do_echo(self, line):
        "Overwrite a file. Usage: echo <file_path> <content>"
        if self.user is None:
            print("Please login first")
            return

        parser = argparse.ArgumentParser(prog="echo")
        parser.add_argument("file_path", type=str)
        parser.add_argument("content", nargs="+", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        content = " ".join(args.content)
        path = self.convertToAbsolutePath(args.file_path)

        if (node := self.graph.getNodeFromPath(path)) is None:
            print("File does not exist")
            return

        if not node.isWritable(self.user):
            print("Access denied")
            return

        fileio.writeFile(path, content)
        print(f"Content written to {args.file_path}")

    def do_chp(self, line):
        "Change a file's permissions. Usage: chp <file_path>"
        if self.user is None:
            print("Please login first")
            return

        parser = argparse.ArgumentParser(prog="chp")
        parser.add_argument("file_path", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        path = self.convertToAbsolutePath(args.file_path)

        if (node := self.graph.getNodeFromPath(path)) is None:
            print("File does not exist")
            return

        if not node.isOwner(self.user):
            print("You are not the owner of this file.")
            return

        print("Change file permissions:")
        print("1. Only the owner can read/write.")
        print("2. All groups that the owner is a part of can read/write.")
        print("3. All users can read/write.")

        while (choice := input("Enter choice: ")) not in ["1", "2", "3"]:
            print("Invalid choice")

        self.graph.changePermissions(choice, path, self.user)

        self.graph.dump()

    def do_update_group(self, line):
        "Update an existing group. Usage update_group <group_name>"
        if self.user is None or not self.user.isAdmin:
            print("You need to be an admin to run this command")
            return
        parser = argparse.ArgumentParser(prog="create_group")
        parser.add_argument("group_name", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        if args.group_name not in self.user.joinedGroups:
            print("Group doesn't exist")
            return

        # while loop to update
        print(
            "Enter add <usernames> to add a user to the group. Separate usernames by a space"
        )
        print(
            "Enter remove <usernames> to remove a user from the group. Separate usernames by a space"
        )
        print("Enter done to finish")
        while True:
            print(
                f"Current users in {args.group_name}: {self.users.getUsersInGroup(args.group_name)}"
            )

            cmd, *users = input("Enter command: ").split()

            if cmd == "add":
                self.users.addUsersToGroup(args.group_name, users)
            elif cmd == "remove":
                self.users.deleteUsersFromGroup(args.group_name, users)
            elif cmd == "done":
                break
            else:
                print("Invalid command")
                continue

        print(f"Group {args.group_name} updated")

    def do_EOF(self, _):
        "Quit the CLI"
        return True


if __name__ == "__main__":
    CLI().cmdloop()
