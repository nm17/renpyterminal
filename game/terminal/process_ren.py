"""renpy
init python:
"""

import shlex
import queue
import subprocess
import os
import threading


class BashProcess:
    def __init__(self, terminal: RenPyTerminal, cmd: list[str]):
        self.terminal = terminal
        self.cmd = cmd
        self.process = None
        self.output_queue = terminal.pty_out_queue
        self.input_queue = terminal.pty_in_queue
        self.running = False
        self.stdout_thread = None
        self.stderr_thread = None
        self.stdin_thread = None

    def start(self):
        if self.running:
            raise RuntimeError("[Process] BashProcess is already running something!")
        if not renpy.windows:
            import pty

            self.running = True
            env = {
                "TERM": "xterm",
                "COLUMNS": str(self.terminal.width),
                "LINES": str(self.terminal.height),
                "LC_ALL": "en_US.UTF-8",
            }

            master_fd_i, slave_fd_i = pty.openpty()
            master_fd_o, slave_fd_o = pty.openpty()
            master_fd_e, slave_fd_e = pty.openpty()
            try:
                self.process = subprocess.Popen(
                    self.cmd,
                    stdin=slave_fd_i,
                    stdout=slave_fd_o,
                    stderr=slave_fd_e,
                    text=True,
                    bufsize=0,
                    universal_newlines=True,
                    env=env,
                    shell=False,
                )
            except FileNotFoundError as err:
                self.terminal.pty_out_queue.put(
                    f"{Colors.RED}{err}{Colors.END}".encode("utf-8")
                )

            # Start IO threads
            self.stdout_thread = threading.Thread(
                target=self.read_output, args=(master_fd_o,)
            )
            self.stderr_thread = threading.Thread(
                target=self.read_output, args=(master_fd_e,)
            )
            self.process_watchdog_thread = threading.Thread(
                target=self.process_watchdog,
            )
            # self.stdin_thread = threading.Thread(target=self.write_input)

            for thread in [
                self.stdout_thread,
                self.stderr_thread,
                self.process_watchdog_thread,
            ]:
                thread.daemon = True
                thread.start()

    def process_watchdog(self):
        while self.running:
            time.sleep(0.1)
            pass
        self.running = False
        self.terminal.reset_handlers()

    def read_output(self, stream: int):
        while self.running:
            try:
                line = os.read(stream, 2048)
                if line:
                    self.output_queue.put(line)
                else:
                    time.sleep(0.1)
            except (ValueError, IOError):
                print("!!!!!!!!!")
                self.terminal.reset_handlers()
                self.running = False
                break
        self.terminal.reset_handlers()
        self.running = False

    def handle_in(self, terminal, inp):
        try:
            self.process.stdin.write(inp)
            self.process.stdin.flush()
        except (queue.Empty, BrokenPipeError):
            pass
        except (IOError, ValueError, AttributeError):
            print("!!!!!!!!!")
            self.terminal.reset_handlers()
            self.running = False

    def send_command(self, cmd: str):
        """TODO: REMOVE"""
        if self.running:
            self.input_queue.put(cmd)

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
            self.process = None
            self.running = False

            self.terminal.reset_handlers()

        # Might cause problems?
        for thread in [self.stdout_thread, self.stderr_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=0.5)
