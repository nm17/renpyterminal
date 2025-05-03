"""renpy
init python:
"""

import threading

typed_val = ""

def command_handler(self):
    if self.current_input == "help":
        self.print("Available commands: help, about, clear, exit")
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


        return -1
    elif self.current_input == "input":
        self.print("Test input: ")
        barrier = threading.Barrier(2)
        def pty_handler(terminal, inp):
            global typed_val
            
            if type(inp) != bytes:
                return
            if inp == b"\r\n":
                barrier.wait()
                return RTSpecial.PTYHANDLER__PREVENT_DEFAULT
            typed_val += inp.decode("utf-8")
        self.in_handlers = [pty_handler, self.pty_render_handler]
        def resp():
            global typed_val
            
            barrier.wait()
            self.reset_handlers()
            self.print(f"\r\nYou typed: {typed_val}")
            self.show_prompt()
        
        t = threading.Thread(target=resp)
        t.daemon = True
        t.start()
        return RTSpecial.CMDHANDLER__PREVENT_DEFAULT
        
    elif self.current_input == "about":
        self.print(f"{Colors.RED}Ren'Py Terminal Emulator{Colors.END}\r\n")
        self.print(f"{Colors.ITALIC}by nm17{Colors.END}\r\n")
        self.print(f"\r\n")
        self.print(f"{Colors.RED}Red{Colors.END}\r\n")
        self.print(f"{Colors.GREEN}Green{Colors.END}\r\n")
        self.print(f"{Colors.BLUE}Blue{Colors.END}\r\n")
        self.print(f"{Colors.PURPLE}Purple{Colors.END}\r\n")
        self.print(f"{Colors.CYAN}Cyan{Colors.END}\r\n")
        self.print(f"{Colors.BOLD}Bold text{Colors.END}\r\n")
        self.print(f"{Colors.CROSSED}Strikethrough text{Colors.END}\r\n")
        self.print(f"{Colors.UNDERLINE}Underlined text{Colors.END}\r\n")
        self.print(f"Hinting test: -> --> == !== ==>\r\n")
        self.print(f"\x5b\x5b\x5b\x5b\x5b\x5b\x5b\x5b\x5b test")
    elif self.current_input == "привет":
        self.print(f"{Colors.BLUE}Тест русского языка 123{Colors.END}")
    else:
        self.print("Unknown command")
