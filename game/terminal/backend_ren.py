"""renpy
init python:
"""

import pyte
import re

import copy
import queue

import subprocess
import shlex

import threading
import time

import functools

from sys import getsizeof

DEFAULT_MOTD = (
    f"{Colors.END}{Colors.BOLD}{Colors.GREEN}Ren'Py Terminal{Colors.END}{Colors.END}\r\n"
    + "Type 'help' for commands\r\n\r\n"
)
DEFAULT_PROMPT = (
    f"{Colors.GREEN}user@renpy{Colors.END}:{Colors.LIGHT_BLUE}~{Colors.END}$ "
)

PREVENT_DEFAULT = -1
ENTER_EVENT = -2

from collections import defaultdict

import sys


def get_size(obj, seen=None):
    """Recursively finds size of objects"""

    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0

    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)

    if isinstance(obj, (dict, defaultdict)):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, "__dict__"):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])

    return size


class RenPyTerminal(pyte.HistoryScreen):
    def __init__(
        self,
        command_handler,
        motd=DEFAULT_MOTD,
        prompt=DEFAULT_PROMPT,
        width=80,
        height=24,
    ):
        self.width = width
        self.height = height
        super().__init__(width, height, ratio=0.25, history=200)
        self.command_handler = command_handler
        self.stream = pyte.ByteStream(self)
        self.stream.attach(self)
        self.current_input = ""
        self.prompt = prompt
        self.command_history = []
        self.history_index = 0
        self.cursor_timer_visible = True
        self.cursor_user_visible = True
        self.fd = None
        self.proc = None
        self.update_timer = None
        self.barrier = None
        self.done_barrier = None
        self.running = False
        self.motd = motd
        self.frame = 0

        self.pty_out_queue = queue.Queue()
        self.pty_in_queue = queue.Queue()

        self.render_buffer = self.get_empty_render_buffer()

        self.reset()

        self.feed(motd)

        self.show_prompt()

        self.default_in_handlers = [
            self.pty_render_handler,
            self.pty_handle_backspace,
            self.pty_default_process_command,
            self.pty_move_handler,
            self.pty_process_input,
        ]
        self.default_out_handlers = [self.pty_render_handler]
        self.reset_handlers()
        self.queue_thread = threading.Thread(target=self.queue_thread_handler)
        self.queue_thread.daemon = True
        self.queue_thread.start()

    @renpy.pure
    def get_empty_render_buffer(self):
        return defaultdict(
            default_factory=lambda: defaultdict(
                default_factory=lambda: {
                    "data": "",
                    "background": "default",
                    "foreground": "default",
                }
            )
        )

    def reset_handlers(self):
        self.in_handlers = copy.copy(self.default_in_handlers)
        self.out_handlers = copy.copy(self.default_out_handlers)

    def queue_thread_handler(self):
        while True:
            if self.pty_in_queue.empty() and self.pty_out_queue.empty():
                time.sleep(0.025)
                continue
            try:
                inp = self.pty_in_queue.get_nowait()
                print("[IN]", inp, sep="\t")
                for handler in self.in_handlers:
                    res = handler(terminal=self, inp=inp)
                    if res == PREVENT_DEFAULT:
                        break
            except queue.Empty:
                pass

            try:
                out = self.pty_out_queue.get_nowait()

                print("[OUT]", out, sep="\t")
                # self.feed(out)

                for handler in self.out_handlers:
                    res = handler(terminal=self, out=out)
                    if res == PREVENT_DEFAULT:
                        break
            except queue.Empty:
                pass

            self.frame += 1

    # def update_bash_output(self):
    #     while self.proc and self.proc.running:
    #         try:
    #             while True:
    #                 output = self.proc.output_queue.get()
    #                 self.stream.feed(output)

    #                 self.render()
    #                 renpy.restart_interaction()
    #         except queue.Empty:
    #             pass

    #         time.sleep(0.1)

    #     self.render()

    def launch_program(self, cmd):
        """
        Launch a given program using
        """
        if not renpy.linux:
            return
        if self.proc:
            self.proc.stop()
            self.reset_handlers()

        self.proc = BashProcess(self, cmd)
        self.in_handlers = [self.proc.handle_in]
        # self.in_handlers.remove(self.proc.handle_in)
        self.proc.start()

    def bell(self, *args):
        renpy.sound.play(
            "terminal/audio/beep.wav", channel="sound", relative_volume=0.8
        )

    def toggle_cursor(self):
        self.cursor_timer_visible = not self.cursor_timer_visible
        # try:
        #     self.render_buffer[self.cursor.y]
        # except IndexError:
        #     self.render_buffer[self.cursor.y] = []
        if self.cursor_timer_visible and self.cursor_user_visible:
            self.render_buffer[self.cursor.y][self.cursor.x] = {
                "data": " ",
                "background": to_hex_color("#00000000", isFg=False),
                "foreground": to_hex_color("#ffffff", isFg=True),
            }
        else:
            self.render_buffer[self.cursor.y][self.cursor.x] = {
                "data": " ",
                "background": to_hex_color("#ffffff", isFg=False),
                "foreground": to_hex_color("#000000", isFg=True),
            }
        self.frame += 1
        renpy.restart_interaction()

    def handle_backspace(self):
        # Destructive backspace
        if len(self.current_input) == 0:
            # self.delete_characters(count=1)
            self.bell()
            return
        print(self.current_input)
        self.pty_in_queue.put((pyte.control.BS + " " + pyte.control.BS).encode("utf-8"))

    def pty_handle_backspace(self, terminal, inp):
        if inp != (pyte.control.BS + " " + pyte.control.BS).encode("utf-8"):
            return
        print("BS!")

        self.current_input = self.current_input[:-1]
        self.cursor_timer_visible = True
        renpy.restart_interaction()
        return PREVENT_DEFAULT

    def process_hidden_input(self, value):
        # TODO: Remake this using a custom InputField class impl?
        val = value[-1]
        self.pty_in_queue.put(val.encode("utf-8"))

    def pty_process_input(self, terminal, inp):
        # self.cursor = self.prompt_location
        if type(inp) == int:
            return

        # self.carriage_return()
        # print(len(self.current_input))
        # self.cursor = self.prompt_location

        self.current_input += inp.decode("utf-8")

        # Reset cursor visibility when typing
        self.cursor_timer_visible = True

        renpy.restart_interaction()

    def pty_render_handler(self, terminal, inp=None, out=None):

        if inp is not None:
            to_feed = inp
        else:
            to_feed = out

        if type(to_feed) == str:
            raise RuntimeError(
                f"Using strings in the pty_in_queue is forbidden! Use bytes. Got {to_feed!r}"
            )

        if type(to_feed) != bytes:
            return

        self.feed(to_feed)

    def handle_ctrlc(self):
        print("CTRL+C!")
        if self.proc and self.proc.running:
            self.proc.stop()
            self.proc = None
        self.show_prompt()

    def move_left(self):
        self.pty_in_queue.put((pyte.control.ESC + "[1D").encode("utf-8"))

    def move_right(self):
        self.pty_in_queue.put((pyte.control.ESC + "[1C").encode("utf-8"))

    def pty_move_handler(self, terminal, inp):
        if not (
            type(inp) == bytes
            and len(inp) == 4
            and inp[0] == 0x1B
            and inp[3] in b"ABCD"
        ):
            return

        prompt_len = len(self.prompt)
        cursor_pos_x = self.cursor.x
        return PREVENT_DEFAULT

    def process_command(self):
        self.pty_in_queue.put(b"\r\n")
        self.pty_in_queue.put(ENTER_EVENT)

    def pty_default_process_command(self, terminal, inp):
        if inp != ENTER_EVENT:
            return

        if len(self.current_input) == 0:
            self.show_prompt()
            renpy.restart_interaction()
            self.current_input = ""
            return

        # if self.current_input == "exit" and self.proc:
        #     self.proc.stop()
        #     self.proc = None
        #     self.pty_out_queue.put("Bash session terminated\r\n")

        self.command_history.append(self.current_input)
        self.history_index = len(self.command_history)
        # self.pty_out_queue.put(b"\r\n")

        self.current_input = self.current_input.strip()
        print(f"[CMDHandler]\t{self.current_input!r}")

        (self.command_handler)(self)
        self.current_input = ""

        self.show_prompt()

        return

    def show_prompt(self, linebreak_before=True):
        if linebreak_before:
            self.pty_out_queue.put(b"\r\n")
        self.pty_out_queue.put(self.prompt.encode("utf-8"))
        self.prompt_location = copy.copy(self.cursor)
        self.cursor_timer_visible = True
        renpy.restart_interaction()

    def feed(self, data):
        """
        A wrapper method around the `self.stream.feed` function.
        Also calls the render function.
        """

        if type(data) == str:
            data = data.encode("utf-8")
        self.stream.feed(data)

        # self.dirty.clear()
        self.render()
        # renpy.restart_interaction()

    def get_visible_lines(self):

        res = self.get_empty_render_buffer()
        for i in range(0, self.height):
            res[i] = self.format_line(self.frame, i)
        return res

    def __eq__(self, other):
        if not isinstance(other, RenPyTerminal):
            return False

        return self.render_buffer is other.render_buffer

    @renpy.pure
    def get_line_from_render(self, frame, y):
        try:
            return self.render_buffer[y]
        except IndexError:
            return []

    def terminal_history_up(self):
        """
        Get the previously used command and send it to the prompt
        """
        if self.command_history and (self.proc is None or self.proc.running == False):
            self.history_index = max(0, self.history_index - 1)
            self.delete_lines(1)
            self.erase_in_display(how=0)
            if self.history_index < len(self.command_history):
                self.current_input = self.command_history[self.history_index]
                self.current_input = self.current_input.strip()
                self.show_prompt(linebreak_before=False)
                self.pty_out_queue.put(self.current_input.encode("utf-8"))
            renpy.restart_interaction()

    def terminal_history_down(self):
        """
        Get the afterwards used command and show it in prompt
        """
        if self.command_history and (self.proc is None or self.proc.running == False):
            self.history_index = min(len(self.command_history), self.history_index + 1)

            self.delete_lines(1)
            self.erase_in_display(how=0)
            self.show_prompt(linebreak_before=False)

            if self.history_index < len(self.command_history):
                self.current_input = self.command_history[self.history_index]
                self.current_input = self.current_input.strip()
                self.pty_out_queue.put(self.current_input.encode("utf-8"))
            else:
                self.current_input = ""
            renpy.restart_interaction()

            # self.feed(self.prompt + self.current_input)

    def handle_char_click(self, x, y):
        """
        Handle a character click by moving the cursor to the given position
        TODO: Rewrite as pty_handler
        """
        self.cursor_position(y, x)
        pass

    def handle_pageup(self):
        """
        Handle a PAGEUP key press. Scrolls the terminal to the top.
        TODO: Rewrite as pty_handler
        """
        self.prev_page()

    def handle_pagedown(self):
        """
        Handle a PAGEDOWN key press. Scrolls the terminal to the bottom.
        TODO: Rewrite as pty_handler
        """
        self.next_page()

    def render(self):
        """
        Sets the `render_buffer` to the output of `get_visible_lines`.

        TODO: Maybe also add partial rendering of lines?
        """
        self.render_buffer = self.get_visible_lines()
        self.frame += 1

    @renpy.pure
    def format_line(self, frame, current_y):
        line = self.buffer[current_y]
        # Convert pyte characters to styled text
        formatted = defaultdict(
            lambda: {"data": "", "background": "#00000000", "foreground": "#00000000"}
        )
        for x, char in line.items():
            char_data = char.data

            fg = to_hex_color(char.fg, isFg=True)
            bg = to_hex_color(char.bg, isFg=False)

            if char.reverse:
                bg, fg = fg, bg

            char_data = char_data if char_data != "\x5b" else "\x5b\x5b"
            char_data = char_data if char_data != "\x7b" else "\x7b\x7b"

            text = ""
            if char.italics:
                text += "{i}"
            if char.bold:
                text += "{b}"
            if char.strikethrough:
                text += "{s}"
            if char.underscore:
                text += "{u}"
            text += char_data
            if char.bold:
                text += "{/b}"
            if char.strikethrough:
                text += "{/s}"
            if char.italics:
                text += "{/i}"
            if char.underscore:
                text += "{/u}"

            if bg == "#000000":
                # Make transparent
                bg = "#00000000"
            if bg is None:
                bg = to_hex_color("default", isFg=False)

            # if fg == "#000000":
            #     # Make transparent
            #     fg = "#00000000"
            if fg is None:
                fg = to_hex_color("default", isFg=True)

            formatted[x] = {"data": text, "background": bg, "foreground": fg}

        # self.dirty.clear()
        return formatted


# Create terminal instance
terminals = {}


@renpy.pure
def get_terminal(name: str, command_handler, width, height) -> RenPyTerminal:
    """
    Gets a terminal with a given name or creates a new one
    """
    terminal = terminals.get(name, None)
    if terminal is None:
        terminal = RenPyTerminal(command_handler, width=width, height=height)
        terminals[name] = terminal
    return terminal
