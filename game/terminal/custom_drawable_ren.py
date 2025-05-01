"""renpy
init -100 python:
"""

import pygame
from renpy.display.screen import screens_by_name, ScreenDisplayable

GLOBAL_LAST_FRAME = None
GLOBAL_DISP_CACHE = {}

import copy


class RenPyTerminalDisplayable(renpy.Displayable):

    def __init__(
        self, name, command_handler, width, height, font_size, fill_screen, **kwargs
    ):
        global GLOBAL_DISP_CACHE
        # Pass additional properties on to the renpy.Displayable
        # constructor.
        super(RenPyTerminalDisplayable, self).__init__(**kwargs)

        # The child.
        # print("CREATED")

        self.screen = screens_by_name["terminal"][None]
        self.name = name
        self.command_handler = command_handler
        self.width = width
        self.height = height

        self.last_render_frame = -1

        # renpy.display.render.per_frame = False
        if GLOBAL_DISP_CACHE.get(self.name) is None:
            GLOBAL_DISP_CACHE[self.name] = ScreenDisplayable(
                self.screen,
                None,
                None,
                scope={
                    "_args": [
                        name,
                        command_handler,
                        width,
                        height,
                        font_size,
                        fill_screen,
                    ]
                },
            )
        # GLOBAL_DISP_CACHE[self.name].sensitive = False
        # renpy.stop_predict_screen("terminal")

    @renpy.pure
    def get_current_terminal(self):
        return get_terminal(self.name, self.command_handler, self.width, self.height)

    @renpy.pure
    def render(self, width, height, st, at):
        global GLOBAL_LAST_FRAME, GLOBAL_DISP_CACHE

        terminal_screen = GLOBAL_DISP_CACHE[self.name]
        # Create a transform, that can adjust the alpha channel of the
        # child.
        if GLOBAL_LAST_FRAME is None:
            GLOBAL_LAST_FRAME = renpy.render(terminal_screen, width, height, st, at)
            return GLOBAL_LAST_FRAME

        # print(self.last_render_frame, self.get_current_terminal().frame)
        if self.last_render_frame == self.get_current_terminal().frame:
            # print("IGNORED")
            return GLOBAL_LAST_FRAME

        # Create a render from the child.
        GLOBAL_LAST_FRAME = renpy.render(terminal_screen, width, height, st, at)
        self.last_render_frame = self.get_current_terminal().frame

        # Return the render.
        return GLOBAL_LAST_FRAME

    def event(self, ev, x, y, st):
        global GLOBAL_LAST_FRAME, GLOBAL_DISP_CACHE

        terminal_screen = GLOBAL_DISP_CACHE[self.name]

        if ev.type in [pygame.ACTIVEEVENT, pygame.MOUSEMOTION]:

            raise renpy.IgnoreEvent()

        if ev.type == pygame.USEREVENT and ev.__dict__.get("code") is None:
            raise renpy.IgnoreEvent()
        # print(ev.type, ev, sep="\t")

        # Pass the event to our child.
        return terminal_screen.event(ev, x, y, st)

    def visit(self):
        global GLOBAL_LAST_FRAME, GLOBAL_DISP_CACHE

        terminal_screen = GLOBAL_DISP_CACHE[self.name]
        return [terminal_screen]
