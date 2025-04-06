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


    show screen terminal("main", command_handler, 80, 24, 32)
    # $ renpy.profile_screen("terminal", True, True, True, True, True, True, False)

    e "Вы создали новую игру Ren'Py."

    show screen terminal("main", command_handler, 80, 24, 24)

    e "Добавьте сюжет, изображения и музыку и отправьте её в мир!"

    return
