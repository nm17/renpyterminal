# Architecture Overview

  - `terminal/`
    - `audio/`
        - A folder to store audio files, currenty only `beep.wav`
    - `fonts/`
        - A folder to store all the fonts in, which will be later used in `settings_ren.py`
    - `backend_ren.py`
        - Contains the main `RenPyTerminal` class
        - See also: [Backend Architecture](backend_overview.md)
    - `process_ren.rpy`
        - Code related to setting up pty's and spawning processes 
    - `settings_ren.py`
        - Global settings that apply to all terminals. Currently it's only responsible for setting up fonts. 
    - `styles.rpy`
        - A placeholder file for storing RenPy styles. Currently unimplemented.
    - `terminal.rpy`
        - The definitions for the `terminal` screen UI. 
    - `utils_ren.rpy`
        - Various utilities that are of general use.