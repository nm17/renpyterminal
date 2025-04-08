# Backend Architecture

The `RenPyTerminal` class is what glues `pyte` and RenPy together. It derives the `pyte.HistoryScreen` class.

If you want to draw something on the screen (or change the screen somehow), you should figure out a way to do that using the `feed` function, since that what it was meant for.

## TL;DR: What is this?

It's just the code that handles the quirks of the RenPy world and the `pyte` terminal emulator world.

## Rendering pipeline

```mermaid
flowchart TD;
    R[/**RenPy screen renderer**
      On each frame... /] -->|For each line...| gvl[*terminal.get_line_from_render* function];

    Re[/**RenPy event**/]-->EC{What kind of event?};
    EC-->CT[Cursor timer];
    EC-->IE[Input event];
    EC-->EE[Enter pressed];
    EE -->|Calls...| CH[User provided *command_handler* function] --> feed;
    PF[Process output feed thread];
    CT -->|Modifies the buffer directly in order to avoid a full re-render| RB[*terminal.render_buffer*];
    ReRen[*terminal.render* function];
    
    IE -->|If there was a character key pressed...| phi[*terminal.process_hidden_input* function];
    phi --> feed;
    PF --> feed;
    feed -->|Then calls...| ReRen;
    Other[*Other possible callers...*] --> feed[*feed* function];

    feed -->|First, it writes bytes to...| pyteStream[pyte's underlying Stream];
    pyteStream -->|Handles terminal emulation logic| pyteBuffer[pyte Buffer object, that stores what's displayed on the screen];
    pyteBuffer -->|Used by...| ReRen;

    gvl -->|Gets the needed rendered line from the buffer or an empty list| RB;
    ReRen -->|Formats each character as needed and stores the result| RB;
```

## See also

  - [`pyte` documentation](https://pyte.readthedocs.io/en/latest/)
  - [`pyte.Screen` API reference](https://pyte.readthedocs.io/en/latest/api.html#pyte-screens-screen) (you're going to need it, trust me)
  - [`pyte.HistoryScreen` API reference](https://pyte.readthedocs.io/en/latest/api.html#pyte-screens-historyscreen)