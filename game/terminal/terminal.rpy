define config.preload_fonts += [
    "terminal/fonts/IosevkaTerm-Medium.ttf",
    "terminal/fonts/IosevkaTerm-Bold.ttf",
    "terminal/fonts/IosevkaTerm-MediumItalic.ttf",
    "terminal/fonts/IosevkaTerm-MediumOblique.ttf",
]
define config.default_textshader = None

# define config.optimize_text_rendering = True
# define config.texture_size_limit = 2048
define config.cache_surfaces = False

screen terminal(name, command_handler, width, height, font_size, fill_screen=False):
    $ terminal = get_terminal(name, command_handler, width, height)
    $ renpy.const("terminal")
    $ terminal.command_handler = command_handler
    # $ print("ASD")
    

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

                    for i in range(terminal.width):
                        $ ch = line[i]
                        $ bg = ch["background"]
                        $ fg = ch["foreground"]
                        $ data = ch["data"]
                        frame:
                            style "terminal__char_box"
                            modal False
                            padding (0, 0)
                            ysize font_size
                            xsize font_size_half
                            default_focus False
                            transclude
                            background Solid(bg)

                            text data:
                                default_focus False
                                ysize font_size
                                xsize font_size_half
                                color fg
                                size font_size
                                font "terminal"
                                hinting "none"
                                shaper "freetype"
                                justify False
    
    input:
        default_focus False
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
    key "K_LEFT" action Function(terminal.move_left)
    key "K_RIGHT" action Function(terminal.move_right)

    key "K_PAGEUP" action Function(terminal.handle_pageup)

    key "K_PAGEDOWN" action Function(terminal.handle_pagedown)
    key "ctrl_K_c" action Function(terminal.handle_ctrlc)

    timer 0.5 repeat True action Function(terminal.toggle_cursor)

    # timer 1/5 repeat True action Function(terminal.render)
    


screen terminal_sm(name, command_handler, width, height, font_size, fill_screen=False):
    python:
        screen = screens_by_name["terminal"][None]
        d = ScreenDisplayable(screen, None, None, scope={"_args": [name, command_handler, width, height, font_size, fill_screen]})

        def event(ev, x, y, at):
            global d
            return d.event(ev, x, y, at)

        sm = SpriteManager(update=(lambda at: 999999), ignore_time=True)
        spr = sm.create(d)
        spr.events = True
    
    add sm