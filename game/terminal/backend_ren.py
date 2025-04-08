"""renpy
init python:
"""

import pyte
import re

import copy

import subprocess
import shlex

import threading
import time

import functools

DEFAULT_MOTD = (
    f"{Colors.END}{Colors.BOLD}{Colors.GREEN}Ren'Py Terminal{Colors.END}{Colors.END}\r\n"
    + "Type 'help' for commands\r\n\r\n"
)
DEFAULT_PROMPT = (
    f"{Colors.GREEN}user@renpy{Colors.END}:{Colors.LIGHT_BLUE}~{Colors.END}$ "
)


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
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.fd = None
        self.proc = None
        self.update_timer = None
        self.barrier = None
        self.done_barrier = None
        self.running = False
        self.motd = motd
        self.frame = 0

        self.render_buffer = []

        self.reset()

        self.feed(motd)

        self.show_prompt()

    def update_bash_output(self):
        while self.proc and self.proc.running:
            try:
                while True:
                    output = self.proc.output_queue.get()
                    self.stream.feed(output)

                    self.render()
                    renpy.restart_interaction()
            except queue.Empty:
                pass

            time.sleep(0.1)

        self.render()

    def launch_program(self, cmd):
        """
        Launch a given program using
        """
        if not renpy.linux:
            return
        self.proc = BashProcess(self, cmd)
        self.proc.start()

        time.sleep(0.1)
        self.update_timer = threading.Thread(target=self.update_bash_output)
        self.update_timer.daemon = True
        self.update_timer.start()

    def bell(self, *args):
        renpy.sound.play(
            "terminal/audio/beep.wav", channel="sound", relative_volume=0.8
        )

    def toggle_cursor(self):
        self.cursor_visible = not self.cursor_visible
        try:
            char = self.render_buffer[self.cursor.y][self.cursor.x]
        except IndexError:
            return
        if self.cursor_visible:
            self.render_buffer[self.cursor.y][self.cursor.x] = {
                "data": " ",
                "background": to_hex_color("#ffffff", isFg=False),
                "foreground": to_hex_color("#000000", isFg=True),
            }
        else:
            self.render_buffer[self.cursor.y][self.cursor.x] = {
                "data": " ",
                "background": to_hex_color("#00000000", isFg=False),
                "foreground": to_hex_color("#ffffff", isFg=True),
            }

    def handle_backspace(self):
        if len(self.current_input) == 0:
            self.delete_characters(count=1)
            self.bell()
            return
        self.current_input = self.current_input[:-1]
        self.cursor_visible = True
        self.delete_characters(count=1)
        self.backspace()
        self.render()
        renpy.restart_interaction()

    def process_hidden_input(self, value):
        self.process_input(value[-1])
        self.hidden_input_value = ""

    def process_input(self, key):
        self.cursor = self.prompt_location

        self.current_input += key

        self.feed(key)

        # Reset cursor visibility when typing
        self.cursor_visible = True
        self.cursor_timer = 0.0

        renpy.restart_interaction()

    def handle_ctrlc(self):
        print("CTRL+C!")
        if self.proc and self.proc.running:
            self.proc.stop()
            self.proc = None
        self.show_prompt()

    def move_left(self):
        if self.proc is not None and self.proc.running:
            self.cursor_back()
        else:
            prompt_len = len(self.prompt)
            cursor_pos_x = self.cursor.x
            if cursor_pos_x <= prompt_len:
                return
            self.cursor_back()
        
    
    def move_right(self):
        if self.proc is not None and self.proc.running:
            self.cursor_forward()
        else:
            prompt_len = len(self.prompt)
            cursor_pos_x = self.cursor.x
            if cursor_pos_x <= prompt_len:
                return
            self.cursor_forward()

    def process_command(self):
        t = threading.Thread(target=self.process_command_inner, daemon=True)
        t.start()

    def process_command_inner(self):

        self.delete_characters(count=1)
        self.backspace()
        if len(self.current_input) == 0:
            self.show_prompt()
            renpy.restart_interaction()
            return

        if self.current_input == "exit" and self.proc:
            self.proc.stop()
            self.proc = None
            self.feed("Bash session terminated\r\n")

        self.command_history.append(self.current_input)
        self.history_index = len(self.command_history)
        self.feed("\r\n")

        (self.command_handler)(self)
        self.current_input = ""

        self.show_prompt()

    def show_prompt(self, linebreak_before=True):
        if linebreak_before:
            self.feed("\r\n")
        self.feed(self.prompt)
        self.prompt_location = copy.copy(self.cursor)
        self.cursor_visible = True

    def feed(self, data):
        """
        A wrapper method around the `self.stream.feed` function.
        Also calls the render function.
        """

        if not type(data) == str:
            raise RuntimeError(f"[[RenPyTerminal]] Invalid data type - {repr(data)}")
        self.stream.feed(data.encode("utf-8"))

        # self.dirty.clear()
        self.render()
        # renpy.restart_interaction()

    def get_visible_lines(self):
        res = []
        for i in range(0, self.height):
            res.append(self.format_line(self.frame, i))
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

                self.show_prompt(linebreak_before=False)
                self.feed(self.current_input)

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
                self.feed(self.current_input)
            else:
                self.current_input = ""

            # self.feed(self.prompt + self.current_input)

    def handle_char_click(self, x, y):
        """
        Handle a character click by moving the cursor to the given position
        """
        self.cursor_position(y, x)
        pass

    def handle_pageup(self):
        """
        Handle a PAGEUP key press. Scrolls the terminal to the top.
        """
        self.prev_page()

    def handle_pagedown(self):

        """
        Handle a PAGEDOWN key press. Scrolls the terminal to the bottom.
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
        formatted = []
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
            formatted.append({"data": text, "background": bg, "foreground": fg})

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
