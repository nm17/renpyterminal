# CMDHandler

CMDHandler, or command handler - is a way to add custom command logic into your terminals. It's just a function that you have to pass into the RenPyTerminal class, that accepts only one argument - `self` (which refers to the `RenPyTerminal` that called it). 

Outputting stuff to the terminal is done through the `self.print` function.

Currently, handling input is a quite a bit more difficult, but that will change with the introduction of higher level `CMDHandler` API, that should be easier to work with.
