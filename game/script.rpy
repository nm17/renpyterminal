# Вы можете расположить сценарий своей игры в этом файле.

# Определение персонажей игры.
define e = Character('Эйлин', color="#c8ffc8")

# Вместо использования оператора image можете просто
# складывать все ваши файлы изображений в папку images.
# Например, сцену bg room можно вызвать файлом "bg room.png",
# а eileen happy — "eileen happy.webp", и тогда они появятся в игре.

# Игра начинается здесь:
label start:

    scene bg room

    show eileen happy

    $ terminal_zorder = -100
    $ terminal_modal = False
    show screen terminal("main",
    command_handler=None,
    font_size=24,
    fill_x=True,
    fill_y=False,
    width=80,
    height=24,
    print_motd=False,
    print_prompt=False,
    no_cursor=True,
    no_default_in_handling=True,
    print_prompt_on_start=False) as main_terminal
    $ terminal = get_terminal("main")
    # $ renpy.profile_screen("terminal", True, True, True, True, True, True, False)

    $ terminal.print("Hello, world!\r\n")
    
    e "Пример RenPyTerminal"
    $ terminal.print("Тест русского языка 123\r\n")

    e "Добавьте сюжет, изображения и музыку и отправьте её в мир!"
    
    hide screen main_terminal

    
    $ terminal_modal = True
    show screen terminal("other",
    command_handler=command_handler,
    font_size=24,
    fill_x=False,
    fill_y=False,
    width=60,
    height=16) as main_terminal

    e "Тест второго терминала с обычным функционалом"


    return
