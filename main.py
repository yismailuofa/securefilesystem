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
    curr_dir = "/"
    users = Users("json/users.example.json")

    def convertToAbsolutePath(self, path: str) -> str:
        # convert to absolute path by accounting for ../ and ./
        if path.startswith("/"):
            return path
        else:
            if self.curr_dir == "/":
                temp = f"/{path}"
            else:
                temp = f"{self.curr_dir}/{path}"
            # split the path into parts
            parts = temp.split("/")
            # remove any ./
            parts = [part for part in parts if part != "."]
            # pop previous directory if we encounter a ../
            for i in range(len(parts)):
                if parts[i] == "..":
                    parts.pop(i)
                    parts.pop(i - 1)
                    break

            return "/".join(parts)

    def with_user(f):
        def wrapper(self, line):
            if self.user is None:
                print("Please login first")
                return
            return f(self, line)

        return wrapper

    def with_admin(f):
        def wrapper(self, line):
            if self.user is None or not self.user.isAdmin:
                print("You need to be an admin to run this command")
                return
            return f(self, line)

        return wrapper

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
        self.curr_dir = f"/{self.user.name}" if not self.user.isAdmin else "/"
        self.prompt = prompt_template.format(
            user=self.user.name, curr_dir=self.curr_dir
        )

        print(f"Logged in as {self.user.name}")

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

    @with_user
    def do_ls(self, _):
        "List files in the current directory"
        node = self.graph.getNodeFromPath(self.curr_dir)
        print(
            *node.getReadableSubNodes(
                self.user.name, self.user.joinedGroups, self.curr_dir
            ),
            sep="\n",
        )

    @with_user
    def do_cd(self, line):
        "Change the current directory"
        parser = argparse.ArgumentParser(prog="cd")
        parser.add_argument("path", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        if (node := self.graph.getNodeFromPath(args.path)) is None:
            print("Invalid path")
            return

        path = self.convertToAbsolutePath(args.path)

        if (node := self.graph.getNodeFromPath(path)) is None:
            print("Invalid path")
            return
        # now check if the user has access to the new directory
        if not node.isReadable(self.user.name, self.user.joinedGroups):
            print("Access denied")
            return

        # now check if the node is a directory
        if not node.isFolder:
            print("Not a directory")
            return

        self.curr_dir = path
        self.prompt = prompt_template.format(
            user=self.user.name, curr_dir=self.curr_dir
        )

    @with_admin
    def do_create_group(self, line):
        "Create a new group. Usage: create_group <group_name>"
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

    @with_admin
    def do_delete_group(self, line):
        "Delete a group. Usage: delete_group <group_name>"
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

    @with_user
    def do_pwd(self, _):
        "Print the current working directory"
        print(self.curr_dir)

    @with_user
    def do_cat(self, line):
        "Read the contents of a file. Usage: cat <file_path>"
        parser = argparse.ArgumentParser(prog="cat")
        parser.add_argument("file_path", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        path = self.convertToAbsolutePath(args.file_path)

        if (node := self.graph.getNodeFromPath(path)) is None:
            print("Invalid path")
            return

        if not node.isReadable(self.user.name, self.user.joinedGroups):
            print("Access denied")
            return

        print(readFile(path))

    @with_user
    def do_mv(self, line):
        "Rename a file or directory. Usage: mv <source> <name>"
        parser = argparse.ArgumentParser(prog="mv")
        parser.add_argument("source", type=str)
        parser.add_argument("name", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        source = self.convertToAbsolutePath(args.source)

        if (node := self.graph.getNodeFromPath(source)) is None:
            print("Invalid source path")
            return

        if not node.isWritable(self.user.name, self.user.joinedGroups):
            print("Access denied")
            return

        self.graph.renameNode(source, args.name)

    @with_user
    def do_mkdir(self, line):
        "Create a new directory. Usage: mkdir <dir_name>"
        parser = argparse.ArgumentParser(prog="mkdir")
        parser.add_argument("dir_name", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        path = self.convertToAbsolutePath(args.dir_name)

        if self.graph.getNodeFromPath(path) is not None:
            print("Directory already exists")
            return

        self.graph.createFolder(path, self.user.name, self.user.joinedGroups)
        
    @with_user
    def do_touch(self, line):
        "Create a new directory. Usage: touch <file_path>"
        parser = argparse.ArgumentParser(prog="mkdir")
        parser.add_argument("file_path", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        path = self.convertToAbsolutePath(args.file_path)

        if self.graph.getNodeFromPath(path) is not None:
            print("File already exists")
            return

        self.graph.createFile(path, self.user.name, self.user.joinedGroups)

    @with_admin
    def do_update_group(self, line):
        "Update an existing group. Usage update_group <group_name>"
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
