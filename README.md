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