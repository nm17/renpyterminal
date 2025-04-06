# RenPyTerminal

A powerful terminal plugin for RenPy that supports VT100/ANSI escape codes. 

Based upon the `pyte` Python library.

This repo is not just the library itself. It's a demo RenPy game that contains the library itself (most of the files are in `game/terminal`).

## TODO:

  - Optimize performance (currently consumes ~20% CPU in normal use and ~120% while running `top`)
  - Documentation
  - Prettier command handling(?)
  - Figure out what the hell I should use instead of pyte, considering that it's GPL 3?