"""renpy
init python:
"""

import shlex
import queue
import subprocess
import os
import threading


class BashProcess:
    def __init__(self, terminal, cmd):
        self.terminal = terminal
        self.cmd = cmd
        self.process = None
        self.output_queue = queue.Queue()
        self.input_queue = queue.Queue()
        self.running = False
        self.stdout_thread = None
        self.stderr_thread = None
        self.stdin_thread = None

    def start(self):
        if not renpy.windows:
            import pty
            self.running = True
            env = {
                "TERM": "xterm-256color",
                "COLUMNS": str(self.terminal.width),
                "LINES": str(self.terminal.height),
                "LC_ALL": "en_US.UTF-8"
            }

            master_fd_i, slave_fd_i = pty.openpty()
            master_fd_o, slave_fd_o = pty.openpty()
            master_fd_e, slave_fd_e = pty.openpty()
            
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

            # Start IO threads
            self.stdout_thread = threading.Thread(target=self.read_output, args=(master_fd_o,))
            self.stderr_thread = threading.Thread(target=self.read_output, args=(master_fd_e,))
            self.stdin_thread = threading.Thread(target=self.write_input)
            
            for thread in [self.stdout_thread, self.stderr_thread, self.stdin_thread]:
                thread.daemon = True
                thread.start()

            

            

    def read_output(self, stream):
        while self.running:
            try:
                line = os.read(stream, 2048)
                if line:
                    self.output_queue.put(line)
                else:
                    time.sleep(0.1)
            except (ValueError, IOError):
                break
            time.sleep(0.1)

    def write_input(self):
        while self.running:
            try:
                cmd = self.input_queue.get(block=True, timeout=1)
                if cmd is None:
                    continue
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
            except (queue.Empty, BrokenPipeError):
                continue
            except (IOError, ValueError):
                break
            time.sleep(0.1)

    def send_command(self, cmd):
        if self.running:
            self.input_queue.put(cmd)

    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
            self.process = None
        
        for thread in [self.stdout_thread, self.stderr_thread, self.stdin_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=0.5)