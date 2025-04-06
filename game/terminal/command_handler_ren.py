"""renpy
init python:
"""

import threading

def command_handler(self):
    if self.current_input == "help":
        self.feed("Available commands: help, about, clear, exit\r\n")
    elif self.current_input == "clear":
        self.reset()

    elif self.current_input == "exit":
        renpy.hide_screen("terminal")
        return
    elif self.current_input.startswith("run"):
        # print("got run command")

        asd = shlex.split(self.current_input)[1:]
        print("TODO", asd)

        self.launch_program(asd)
    elif self.current_input == "about":
        self.feed(f"{Colors.RED}Ren'Py Terminal Emulator{Colors.END}\r\n")
        self.feed(f"{Colors.ITALIC}by nm17{Colors.END}\r\n")
        self.feed(f"\r\n")
        self.feed(f"{Colors.RED}Red{Colors.END}\r\n")
        self.feed(f"{Colors.GREEN}Green{Colors.END}\r\n")
        self.feed(f"{Colors.BLUE}Blue{Colors.END}\r\n")
        self.feed(f"{Colors.PURPLE}Purple{Colors.END}\r\n")
        self.feed(f"{Colors.CYAN}Cyan{Colors.END}\r\n")
        self.feed(f"{Colors.BOLD}Bold text{Colors.END}\r\n")
        self.feed(f"{Colors.CROSSED}Strikethrough text{Colors.END}\r\n")
        self.feed(f"{Colors.UNDERLINE}Underlined text{Colors.END}\r\n")
        self.feed(f"{Colors.NEGATIVE}Negative text{Colors.END}\r\n")
        self.feed(f"\x5B\x5B\x5B\x5B\x5B\x5B\x5B\x5B\x5B test")
    elif self.current_input == "привет":
        self.feed(f"{Colors.BLUE}Тест русского языка 123{Colors.END}")
    else:
        self.feed("Unknown command")
