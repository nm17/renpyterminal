# RenPyTerminal

A powerful terminal plugin for RenPy that supports VT100/ANSI escape codes. 

Based upon the `pyte` Python library. It's not included in the code for legal reasons. You need to install it by calling:

```
pip install --target game/python-packages pyte`
```

This repo is not just the library itself. It's a demo RenPy game that contains the library itself (most of the files are in `game/terminal`).

## TODO:

  - Optimize performance (currently consumes ~20% CPU in normal use and ~120% while running `top`)
  - Documentation
  - Prettier command handling(?)
  - Send up and down key events to the terminal, but also support command history.
  - Make the code look better
