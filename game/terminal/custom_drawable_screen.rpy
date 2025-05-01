python early:
    import functools

    @renpy.pure
    def get_disp_term(name, command_handler, width, height, font_size, fill_screen=False):
        terminal = get_terminal(name, command_handler, width, height)
        d = RenPyTerminalDisplayable(name, command_handler, width, height, font_size, fill_screen)
        return d

screen test_scr(name, command_handler, width, height, font_size, fill_screen=False):
    

    vbox:
        add get_disp_term(name, command_handler, width, height, font_size, fill_screen=False)
        