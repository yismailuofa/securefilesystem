import cmd
import argparse
from graph import Graph
from user import Users

from util import tryParse

prompt_template = "sfs> {user}@{curr_dir}$ "

class CLI(cmd.Cmd):
    # These are automatically set by cmd.Cmd
    intro = "Welcome to the Secure File System CLI. Type help or ? to list commands.\n"

    user = None
    graph = Graph("json/permissions.example.json")
    curr_dir = "/"
    prompt = "sfs> "
    users = Users()

    def do_login(self, line):
        parser = argparse.ArgumentParser(prog="login")
        parser.add_argument("username", type=str)
        parser.add_argument("password", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        if args.username not in CLI.users.users:
            print("User not found")
            return
        if CLI.users.users[args.username].password != args.password:
            print("Invalid password")
            return
            
        CLI.user = CLI.users.users[args.username]
        CLI.curr_dir = f"/{self.user.name}"
        CLI.prompt = prompt_template.format(user=CLI.user.name, curr_dir=CLI.curr_dir)

        print(f"Logged in as {self.user}")

    def do_quit(self, _):
        "Quit the CLI"
        return True

    def do_ls(self, _):
        "List files in the current directory"
        node = CLI.graph.getNodeFromPath(CLI.curr_dir)
        print(node.getReadableSubNodes(CLI.user.name, CLI.user.joinedGroups))

    def do_cd(self, line):
        "Change the current directory"
        parser = argparse.ArgumentParser(prog="cd")
        parser.add_argument("path", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        if (node := CLI.graph.getNodeFromPath(args.path)) is None:
            print("Invalid path")
            return

        temp = ''
        # convert to absolute path by accounting for ../ and ./
        if args.path.startswith("/"):
            temp = args.path
        else:
            temp = f"{CLI.curr_dir}/{args.path}"
            # split the path into parts
            parts = temp.split("/")
            # remove any ./
            parts = [part for part in parts if part != "."]
            # pop previous directory if we encounter a ../
            for i in range(len(parts)):
                if parts[i] == "..":
                    parts.pop(i)
                    parts.pop(i-1)
                    break

            temp = "/".join(parts)
        
        if (node := CLI.graph.getNodeFromPath(temp)) is None:
            print("Invalid path")
            return
        # now check if the user has access to the new directory
        if not node.isReadable(CLI.user.name, CLI.user.joinedGroups):
            print("Access denied")
            return
        CLI.curr_dir = temp
        CLI.prompt = prompt_template.format(user=CLI.user.name, curr_dir=CLI.curr_dir)

    def do_EOF(self, _):
        "Quit the CLI"
        return True


if __name__ == "__main__":
    CLI().cmdloop()
