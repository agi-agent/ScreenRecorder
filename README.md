# ScreenRecorder

`demo.py` is basing on codes provided by Qin Zengyi

## Goal

- First of all, we only need one file.
- This file is supposed to be running locally, not on a server.
- Here is what we want to do in this file:
```
Initialize overlay window in fullscreen
Disable failsafe for mouse automation
Initialize action log: recorded_actions = []

loop forever:
    # Step 1: Capture and display screenshot
    screenshot = capture_screen()
    show_fullscreen_image(screenshot)
    
    # Step 2: Start recording annotation actions
    recorded_actions.clear()
    start_recording_mouse_and_keyboard(recorded_actions)
    
    wait until user presses 'Tab' key
    
    # Step 3: Finish annotation and hide screenshot
    stop_recording()
    hide_fullscreen_image()
    
    # Step 4: Replay recorded actions
    for action in recorded_actions:
        if action.type == 'move':
            move_mouse_to(action.position)
        elif action.type == 'click':
            perform_mouse_click(action.position)
        elif action.type == 'key':
            press_keyboard_key(action.key)
    
    # Step 5: Save actions to file
    save_actions_to_file(recorded_actions)
```

## Changelog

- Replaced Tkinter's key event bindings with `pynput` global keyboard listener as Tkinter fails on ratina displays.
- Added `start_keyboard_listener()` to handle global key presses and releases.
- Implemented `handle_control_keys_pynput()` to detect control keys like `F5`, `F6`, `Tab`, and `Ctrl+Q` with appropriate actions.
- Introduced `allow_forwarding` flag to delay event replay until user triggers it explicitly by pressing the `Tab` key.
- Logged and saved all queued events into a timestamped `.log` file before forwarding when `Tab` is pressed.
- Added `enqueue_event()` wrapper with queue state logging before and after adding events.
- Prevented event enqueueing when `allow_forwarding` is active to avoid mid-forwarding interference.
- Switched from `root.bind` to `canvas.bind` for mouse event capture to avoid interference from the full-screen overlay.
- Added runtime screen ratio detection (`screen_ratio`) based on the difference between physical screenshot size and canvas size.
- Resized screenshots using `Image.Resampling.LANCZOS` and calculated scaled width and height to match canvas properly.
- Hid the application window before taking screenshots and re-shown it afterward to avoid capturing the overlay itself.
- Used `focus_force()`, `lift()`, and `canvas.focus_set()` to ensure keyboard focus returns to the canvas after updates.
- Automatically updated the screenshot after event forwarding is finished and restored the overlay interface.

## TODO

In terms of the display of the screenshot, it moves slightly down below the original scene. Currently, I used `delta_fix` to correct position mismatch due to screen scaling or OS bars. I tried to use other packages, but leading to same issue. If you have any idea, please let me know.
