import cmd
import argparse

from util import tryParse


class CLI(cmd.Cmd):
    # These are automatically set by cmd.Cmd
    intro = "Welcome to the Secure File System CLI. Type help or ? to list commands.\n"
    prompt = "sfs> "

    user = None

    def do_login(self, line):
        if self.user:
            print(f"You are already logged in as {self.user}")
            return

        parser = argparse.ArgumentParser(prog="login")
        parser.add_argument("username", type=str)
        parser.add_argument("password", type=str)
        if (args := tryParse(parser, line)) is None:
            return

        self.user = args.username

        print(f"Logged in as {self.user}")

    def do_quit(self, line):
        "Quit the CLI"
        return True

    def do_EOF(self, line):
        "Quit the CLI"
        return True


if __name__ == "__main__":
    CLI().cmdloop()
