define config.preload_fonts += [
    "terminal/fonts/IosevkaTerm-Medium.ttf",
    "terminal/fonts/IosevkaTerm-Bold.ttf",
    "terminal/fonts/IosevkaTerm-MediumItalic.ttf",
    "terminal/fonts/IosevkaTerm-MediumOblique.ttf",
]
define config.default_textshader = None

screen terminal(name, command_handler, width, height, font_size, fill_screen=False):
    $ terminal = get_terminal(name, command_handler, width, height)
    $ renpy.const("terminal")
    $ terminal.command_handler = command_handler
    

    zorder 100
    modal True

    $ ysize_val = (font_size * height + 20 * 2 + 10) if not fill_screen else None
    $ font_size_half = int(font_size / 2)
    

    frame:
        xfill True
        yfill False
        ysize ysize_val

        style "terminal"
        

        padding (20, 20)
        vbox:
            spacing 0
            style "terminal__columns"
            # Existing terminal output
            for y in range(terminal.height):
                $ line = terminal.get_line_from_render(terminal.frame, y)
                hbox:
                    style "terminal__lines"

                    for x in range(len(line)):
                        $ ch = line[x]
                        $ bg = ch["background"]
                        $ fg = ch["foreground"]
                        $ data = ch["data"]
                        window:
                            style "terminal__char_box"
                            modal False
                            background bg
                            padding (0, 0)
                            ysize font_size
                            xsize font_size_half

                            text data:

                                ysize font_size
                                xsize font_size_half
                                color fg
                                size font_size
                                font "terminal"
                                hinting "none"
                                shaper "freetype"
                                justify False
    
    input:
        changed terminal.process_hidden_input
        color "#ff000000"
        xsize 0
        ysize 0

    key "K_RETURN" action Function(terminal.process_command)
    key "K_BACKSPACE" action Function(terminal.handle_backspace)
    key "ctrl_K_BACKSPACE" action Function(terminal.handle_backspace)
    key "K_UP" action Function(terminal.terminal_history_up)
    key "K_DOWN" action Function(terminal.terminal_history_down)
    key "ctrl_K_LEFT" action Function(terminal.move_left)
    key "ctrl_K_RIGHT" action Function(terminal.move_right)

    key "K_PAGEUP" action Function(terminal.handle_pageup)

    key "K_PAGEDOWN" action Function(terminal.handle_pagedown)
    key "ctrl_K_c" action Function(terminal.handle_ctrlc)

    timer 0.5 repeat True action Function(terminal.toggle_cursor)

    # timer 1/5 repeat True action Function(terminal.render)
