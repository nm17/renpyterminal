# Breakdown of a sample input handler 

This example shows you how to prompt the user into typing in a single line and then using that information somehow, only using primitive RenPyTerminal API.

Quick note: self.extra_state is just a dict where you can put anything you wish to associate with the current terminal instance, so that you wouldn't need to use global variables, which can be a problem if you want to have multiple terminals at the same time.

```python
def command_handler(self):
    # Check for "input" command
    if self.current_input == "input":
        self.print("Test input: ")

        # Reset the value.
        self.extra_state.typed_val = ""

        # Create an Event synchronization semaphore, so that 
        # our `resp` function will get the input only when the user
        # has finished typing. 
        value_entered_event = threading.Event()

        # A custom pty handler function that will take care of
        # recording character inputs.
        def pty_handler(terminal, inp):
            global typed_val
            # Some events in the pty_in_queue are not bytes.
            # They represent internal events and are of no use to us here.
            if type(inp) != bytes:
                return
            
            # Check if enter has been pressed.
            if inp == b"\r\n":
                # Signal that we have finished listening to the user's key strokes.
                value_entered_event.set()
                return -1
            self.extra_state.typed_val += inp.decode("utf-8")
        
        # Set our in_handlers accordingly
        # self.pty_render_handler is a generic handler that takes care of actually
        # showing the stuff that we type in.
        self.in_handlers = [pty_handler, self.pty_render_handler]

        # Function that handles what the user has typed
        def resp():
            value_entered_event.wait()
            self.reset_handlers()
            # ...Any custom logic that you wish to implement goes here...
            self.print(f"\r\nYou typed: {self.extra_state.typed_val}")

        t = threading.Thread(target=resp)
        t.daemon = True
        # This thread is started in the background,
        # to prevent the pty handlers from being blocked from doing
        # their job.
        t.start()

        # Return CMDHANDLER__PREVENT_DEFAULT so that the prompt won't show
        # after our command handler returns.
        return RTSpecial.CMDHANDLER__PREVENT_DEFAULT
```