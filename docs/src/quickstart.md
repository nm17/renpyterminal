# Quickstart

A quick guide on how to integrate RenPyTerminal into your code.

  + Copy the `terminal` folder
  + Add the following lines to your `script.rpy`:
    ```renpy
    show screen terminal("main", command_handler=None, width=80, height=24, font_size=24, fill_screen=True)
    ```