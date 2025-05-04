

define config.preload_fonts += [
    "terminal/fonts/IosevkaTerm-Medium.ttf",
    "terminal/fonts/IosevkaTerm-Bold.ttf",
    "terminal/fonts/IosevkaTerm-MediumItalic.ttf",
    "terminal/fonts/IosevkaTerm-MediumOblique.ttf",
]

define config.cache_surfaces = False
define config.keyword_after_python = True

define terminal_zorder = -100
define terminal_modal = False

screen terminal(
    name="main",
    command_handler=None,
    zorder=-100,
    modal=True,
    font_size=24,
    width=80,
    height=24,
    fill_x=True,
    fill_y=True,
    no_cursor=False,
    **properties
):
    
    zorder terminal_zorder
    modal terminal_modal

    $ terminal = get_terminal(name, command_handler, width=width, height=height, **properties)
    $ terminal.command_handler = command_handler    

    $ ysize_val = (font_size * height + 20 * 2 + 10) if not fill_y else None
    $ font_size_half = int(font_size / 2)
    

    frame:
        xfill fill_x
        yfill fill_y
        background to_hex_color("default", isFg=False)

        style "terminal"
        
        # text str(terminal.frame):
        #     xsize 0
        #     ysize 0

        padding (20, 20)
        vbox:
            spacing 0
            style "terminal__columns"
            # Existing terminal output

            text terminal.get_render(terminal.frame):
                default_focus False
                adjust_spacing False
                xfill True
                yfill True
                size font_size
                font "terminal"
                hinting "bytecode"
                shaper "harfbuzz"
                justify False
                layout "nobreak"
                line_leading 0
                line_spacing 0
                kerning 0

    
    input:
        value TermInputField(terminal)
        default_focus False
        # changed terminal.process_hidden_input
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

    if not no_cursor:
        timer 0.5 repeat True action Function(terminal.toggle_cursor)
    # else:
    #     timer 0.5 repeat True action Function(terminal.render)

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