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
DEFAULT_PROMPT_LEN = len("user@renpy:~$ ")



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
        prompt_len=DEFAULT_PROMPT_LEN,
        print_motd=True,
        print_prompt=True,
        print_prompt_on_start=True,
        no_default_in_handling=False,
        no_default_out_handling=False,
        width=80,
        height=24,
        **kwargs
    ):
        self.width = width
        self.height = height
        super().__init__(width, height, ratio=0.25, history=200)
        self.command_handler = command_handler
        self.stream = pyte.ByteStream(self)
        self.stream.attach(self)
        self.current_input = ""
        self.prompt = prompt
        self.prompt_len = DEFAULT_PROMPT_LEN
        self.command_history = []
        self.history_index = 0
        self.cursor_timer_visible = True
        self.cursor_user_visible = True
        self.cursor = pyte.screens.Cursor(0, 0)
        self.fd = None
        self.proc = None
        self.update_timer = None
        self.barrier = None
        self.done_barrier = None
        self.extra_state = {}
        self.running = False
        self.motd = motd
        self.frame = 0

        self.prev_data = defaultdict(lambda: defaultdict(lambda: " "))

        self.cursor_symbol_pos = copy.copy(self.cursor)
        self.cursor_symbol_prev = pyte.screens.Char(data=" ")

        self.pty_out_queue = queue.Queue()
        self.pty_in_queue = queue.Queue()

        self.render_buffer = self.get_empty_render_buffer()

        self.reset()

        self._queue_update_event = threading.Event()
        
        self.print_motd = print_motd
        if print_motd:
            self.print(motd)

        self.print_prompt_on_start = print_prompt_on_start
        self.print_prompt = print_prompt
        if print_prompt_on_start:
            self.show_prompt()

        self.default_in_handlers = [
            self.pty_render_handler,
            self.pty_default_process_command,
            self.pty_handle_backspace,
            self.pty_move_handler,
            self.pty_process_input,
        ]
        self.default_out_handlers = [self.pty_render_handler]

        
        if no_default_in_handling:
            self.default_in_handlers = []
        print(no_default_out_handling)
        if no_default_out_handling:
            self.default_out_handlers = []

        self.reset_handlers()
        self.queue_thread = threading.Thread(target=self.queue_thread_handler)
        self.queue_thread.daemon = True
        self.queue_thread.start()
    
    def __getstate__(self):
        return {
            "buffer": dict(self.buffer),
        }
    
    def __setstate__(self, data: dict):
        for (k, v) in data.items():
            self.__dict__[k] = v
    
    def print(self, val):
        if type(val) == bytes:
            pass
        else:
            val = val.encode("utf-8")
        self.put_output(val)

    @renpy.pure
    def get_empty_render_buffer(self):
        # return "\r\n".join([" " * self.width for i in range(self.height)])
        return ""

    def reset_handlers(self):
        self.in_handlers = copy.copy(self.default_in_handlers)
        self.out_handlers = copy.copy(self.default_out_handlers)

    def _set_update_event(self):
        self._queue_update_event.set()

    def put_output(self, out):
        rt_qth_logger.debug("PUT[out]: %s", repr(out))
        self.pty_out_queue.put(out)
        self._set_update_event()
        self.render()
        renpy.restart_interaction()

    def put_input(self, inp):
        rt_qth_logger.debug("PUT[in]: %s", repr(inp))
        self.pty_in_queue.put(inp)
        self._set_update_event()

    def queue_thread_handler(self):
        while True:
            self._queue_update_event.wait()
            self._queue_update_event.clear()
            try:
                while inp := self.pty_in_queue.get_nowait():
                    rt_qth_logger.debug("IN[%s]: %s", str(type(inp)), repr(inp))

                    for handler in self.in_handlers:
                        res = handler(terminal=self, inp=inp)
                        if res == RTSpecial.PTYHANDLER__PREVENT_DEFAULT:
                            break
            except queue.Empty:
                pass
            
            try:
                while out := self.pty_out_queue.get_nowait():
                    rt_qth_logger.debug("OUT[%s]: %s", str(type(out)), repr(out))

                    for handler in self.out_handlers:
                        res = handler(terminal=self, out=out)
                        if res == RTSpecial.PTYHANDLER__PREVENT_DEFAULT:
                            break
            except queue.Empty:
                pass

            self.frame += 1
            self.render()
            renpy.restart_interaction()

    def launch_program(self, cmd):
        """
        Launch a given program using
        """
        if not renpy.linux:
            rt_logger.warning(
                "Launching programs does not work on any OS besides windows yet!"
            )
            return
        if self.proc:
            self.proc.stop()

        self.proc = BashProcess(self, cmd)
        self.in_handlers = [self.proc.pty_bashprocess_handle_in]
        self.proc.start()

    def bell(self, *args):
        renpy.sound.play(
            "terminal/audio/beep.wav", channel="sound", relative_volume=0.8
        )

    def toggle_cursor(self, value=None):
        """
        Handle terminal cursor blinking and explict calls to show or hide it.
        """
        if value is None:
            self.cursor_timer_visible = not self.cursor_timer_visible
        else:
            self.cursor_timer_visible = value

        if self.cursor_timer_visible and self.cursor_user_visible:
            c = self.buffer[self.cursor.y][self.cursor.x]._asdict()
            c["blink"] = True
            self.buffer[self.cursor.y][self.cursor.x] = pyte.screens.Char(**c)
        else:
            c = self.buffer[self.cursor.y][self.cursor.x]._asdict()
            c["blink"] = False
            self.buffer[self.cursor.y][self.cursor.x] = pyte.screens.Char(**c)
        # print(lines)
        # self.render_buffer = "\r\n".join(list(map(lambda el: "".join(el), lines)))
        self.render()
        self.frame += 1
        renpy.restart_interaction()

    def handle_backspace(self):
        # Destructive backspace
        move_to = self.prompt_len + len(self.current_input)

        # print(self.cursor.x - move_to)
        if self.cursor.x - move_to < 0:
            self.cursor_position(self.cursor.y + 1, move_to + 1)
            self.bell()
            renpy.restart_interaction()
            return

        if len(self.current_input) == 0:
            
            # self.delete_characters(count=1)
            self.bell()
            return
        # print(self.current_input)
        self.put_input((pyte.control.BS + " " + pyte.control.BS).encode("utf-8"))

    def pty_handle_backspace(self, terminal, inp):
        if inp != (pyte.control.BS + " " + pyte.control.BS).encode("utf-8"):
            return

        move_to = self.prompt_len + len(self.current_input)


        if self.cursor.x - move_to < -1:
            self.cursor = self.prompt_location
            renpy.restart_interaction()
            return RTSpecial.PTYHANDLER__PREVENT_DEFAULT

        self.current_input = self.current_input[:-1]
        
        self.cursor_position(self.cursor.y + 1, move_to)

        if self.cursor.x - move_to > -1:
            renpy.restart_interaction()
            return RTSpecial.PTYHANDLER__PREVENT_DEFAULT
        
        
        self.prev_data[self.cursor.y - 1][self.cursor.x] = " "
        self.delete_characters(count=1)
        self.toggle_cursor(True)
        renpy.restart_interaction()
        return RTSpecial.PTYHANDLER__PREVENT_DEFAULT

    def process_hidden_input(self, value):
        # TODO: Remake this using a custom InputField class impl?
        val = value[-1]
        self.put_input(val.encode("utf-8"))

    def pty_process_input(self, terminal, inp):
        # self.cursor = self.prompt_location
        if type(inp) == int:
            return

        # self.carriage_return()
        # print(len(self.current_input))
        # self.cursor = self.prompt_location

        self.current_input += inp.decode("utf-8")

        # Reset cursor visibility when typing
        self.toggle_cursor(True)

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
        rt_logger.info("Got CTRL+C!")
        if self.proc and self.proc.running:
            self.proc.stop()
            self.proc = None
        # self.show_prompt()

    def move_left(self):
        self.put_input((pyte.control.ESC + "[1D").encode("utf-8"))

    def move_right(self):
        self.put_input((pyte.control.ESC + "[1C").encode("utf-8"))

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
        return RTSpecial.PTYHANDLER__PREVENT_DEFAULT

    def process_command(self):
        self.put_input(b"\r\n")
        self.put_input(RTSpecial.PTYEVENT__ENTER)

    def pty_default_process_command(self, terminal, inp):
        if inp != RTSpecial.PTYEVENT__ENTER:
            return

        if len(self.current_input) == 0:
            self.show_prompt()
            renpy.restart_interaction()
            self.current_input = ""
            return

        self.command_history.append(self.current_input)
        self.history_index = len(self.command_history)

        self.current_input = self.current_input.strip()
        rt_cmdhandler_logger.info(f"Called %s", self.current_input)

        if self.command_handler is None:
            self.current_input = ""
            self.show_prompt()
            rt_cmdhandler_logger.debug("self.command_handler is None!")
            return RTSpecial.PTYHANDLER__PREVENT_DEFAULT

        res = (self.command_handler)(self)

        self.current_input = ""

        if res != RTSpecial.CMDHANDLER__PREVENT_DEFAULT:
            self.show_prompt()

        return RTSpecial.PTYHANDLER__PREVENT_DEFAULT

    def show_prompt(self, linebreak_before=True):
        if not self.print_prompt:
            return
        if linebreak_before:
            self.put_output(b"\r")
            self.put_output(b"\n")
        self.put_output(self.prompt.encode("utf-8"))
        self.prompt_location = copy.copy(self.cursor)
        self.toggle_cursor(True)
        renpy.restart_interaction()

    def feed(self, data):
        """
        A wrapper method around the `self.stream.feed` function.
        Also calls the render function.
        """

        if type(data) == str:
            data = data.encode("utf-8")
        self.stream.feed(data)

        self.render()

    def get_visible_lines(self):

        res = self.get_empty_render_buffer()
        for i in range(0, self.height):
            res += (self.format_line(self.frame, i))
        return res

    def __eq__(self, other):
        if not isinstance(other, RenPyTerminal):
            return False

        return self.render_buffer is other.render_buffer


    def get_render(self, frame):
        return self.render_buffer


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
                self.put_output(self.current_input.encode("utf-8"))
            # renpy.restart_interaction()

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
                self.put_output(self.current_input.encode("utf-8"))
            else:
                self.current_input = ""

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
        formatted = ""
        for x, char in line.items():
            char_data = char.data

            fg = to_hex_color(char.fg, isFg=True)
            bg = to_hex_color(char.bg, isFg=False)

            if char.reverse:
                bg, fg = fg, bg

            char_data = char_data if char_data != "\x5b" else "\x5b\x5b"
            char_data = char_data if char_data != "\x7b" else "\x7b\x7b"


            if fg is None:
                fg = to_hex_color("default", isFg=True)
            if char.blink:
                self.prev_data[current_y][x] = char.data
                c = self.buffer[current_y][x]._asdict()
                assert char.data == c["data"]
                c["blink"] = False
                c["data"] = "█"
                self.buffer[current_y][x] = pyte.screens.Char(**c)
                char = self.buffer[current_y][x]
            elif char.data == "█":
                c = self.buffer[current_y][x]._asdict()
                assert char.data == c["data"]
                c["blink"] = False
                c["data"] = self.prev_data[current_y][x]
                self.buffer[current_y][x] = pyte.screens.Char(**c)

            text = ""
            if char.italics:
                text += "{i}"
            if char.bold:
                text += "{b}"
            if char.strikethrough:
                text += "{s}"
            if char.underscore:
                text += "{u}"
            
            text += "{color=" + fg + "}"
            text += char_data
            text += "{/color}"
            
            if char.bold:
                text += "{/b}"
            if char.strikethrough:
                text += "{/s}"
            if char.italics:
                text += "{/i}"
            if char.underscore:
                text += "{/u}"


            formatted += text

        # self.dirty.clear()
        return formatted.ljust(self.width, " ") + "\r\n"


class TermInputField(InputValue):
    """
    A nifty bodge to prevent the user from moving the cursor inside
    the hidden input field with something like CTRL+K_LEFT or CTRL+K_RIGHT
    """
    def __init__(self, terminal):
        super().__init__()

        self.terminal = terminal

    def get_text(self):
        return ""
    
    def set_text(self, s):
        # For some reason, InputValues in RenPy love to call set_text with
        # an empty value before calling it with what the user actually typed.
        # This prevents an empty string being handled as something that the user typed.
        if len(s) == 0:
            return
        self.terminal.process_hidden_input(s)


# Create terminal instance
# persistent._seen_ever = {}

_terminals = {}


# real_save_persistent = renpy.save_persistent

# def new_save_persistent():
#     return
#     if _terminal_states is None:
#         print("Nothing to do!")
#         real_save_persistent()
#         return
#     for (name, terminal) in terminals.items():
#         _terminal_states[name] = {}
    
#     real_save_persistent()

# renpy.save_persistent = new_save_persistent
# import json

# def jsoncallback(d):
#     print("TERMINAL STATES SAVE!!!")
#     store.terminal_states = dict([(k,v.__getstate__()) for (k,v) in _terminals.items()])
#     # print(store.terminal_states)
    

# config.save_json_callbacks.append(jsoncallback)


def get_terminal(name: str, command_handler=None, **kwargs) -> RenPyTerminal:
    """
    Gets a terminal with a given name or creates a new one
    """
    global _terminals
    # if store.terminal_states is None:
        
    #     store.terminal_states = {}
    terminal = _terminals.get(name, None)
    if terminal is None:
        terminal = RenPyTerminal(command_handler, **kwargs)
        _terminals[name] = terminal
    

    return terminal
