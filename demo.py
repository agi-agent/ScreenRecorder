import tkinter as tk
from PIL import Image, ImageTk
import pyautogui
import sys
import time
import threading
import queue
import datetime
def log_queue(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {msg}")

class DiscreteScreenFilter:
    def enqueue_event(self, event_type, event_data):
        log_queue(f"Queue before adding: {list(self.event_queue.queue)}")
        self.event_queue.put((event_type, event_data))
        log_queue(f"Queue after adding: {list(self.event_queue.queue)}")


    def __init__(self):
        print("Creating discrete screen filter...")
        # Disable pyautogui failsafe
        pyautogui.FAILSAFE = False
        
        # Create window
        self.root = tk.Tk()
        self.root.title("Discrete Screen Filter")
        self.root.configure(bg='black')
        
        # Get screen dimensions
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        print(f"Screen size: {self.width}x{self.height}")
        
        # Make fullscreen
        self.root.geometry(f"{self.width}x{self.height}+0+0")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.root, 
            width=self.width, 
            height=self.height, 
            bg='black', 
            highlightthickness=0
        )
        self.canvas.pack()
        
        # State
        self.photo = None
        self.is_active = True
        self.passthrough_active = True
        
        # Event forwarding
        self.event_queue = queue.Queue()
        self.last_mouse_pos = (0, 0)
        
        # Bind all events to our handlers
        self.setup_event_capture()
        
        # Start event forwarding thread
        self.start_event_forwarding()
        
        print("Taking initial screenshot...")
        self.root.after(100, self.take_initial_screenshot)
        
    def setup_event_capture(self):
        """Capture mouse clicks and keyboard events (no mouse movement)"""
        # Capture mouse clicks only (not movement)
        self.root.bind('<Button-1>', self.on_mouse_event)
        self.root.bind('<Button-2>', self.on_mouse_event)  
        self.root.bind('<Button-3>', self.on_mouse_event)
        self.root.bind('<ButtonRelease-1>', self.on_mouse_event)
        self.root.bind('<ButtonRelease-2>', self.on_mouse_event)
        self.root.bind('<ButtonRelease-3>', self.on_mouse_event)
        self.root.bind('<MouseWheel>', self.on_mouse_wheel)
        
        # Capture keyboard events
        self.root.bind('<KeyPress>', self.on_key_event)
        self.root.bind('<KeyRelease>', self.on_key_event)
        
        self.root.focus_set()
    
    def on_mouse_event(self, event):
        """Handle mouse click events"""
        if not self.passthrough_active:
            return
            
        # Check for our control keys first
        if self.is_control_click(event):
            return
            
        # For clicks, use the current mouse position instead of event position
        # This prevents cursor jumping
        current_x, current_y = pyautogui.position()
        
        # Queue the mouse event for forwarding
        # self.event_queue.put(('mouse_click', {
        #     'button': event.num,
        #     'x': current_x,
        #     'y': current_y,
        #     'type': event.type
        # }))
        self.enqueue_event('mouse_click', {
            'button': event.num,
            'x': current_x,
            'y': current_y,
            'type': event.type
        })
    

    def on_mouse_wheel(self, event):
        """Handle mouse wheel events"""
        if not self.passthrough_active:
            return
            
        # self.event_queue.put(('mouse_scroll', {
        #     'delta': event.delta,
        #     'x': event.x_root,
        #     'y': event.y_root
        # }))
        self.enqueue_event('mouse_scroll', {
            'delta': event.delta,
            'x': event.x_root,
            'y': event.y_root
        })
    
    def on_key_event(self, event):
        """Handle keyboard events"""
        # Check for our control keys first
        if self.handle_control_keys(event):
            return
        
        if not self.passthrough_active:
            return
            
        # Queue keyboard event for forwarding  
        # self.event_queue.put(('key', {
        #     'key': event.keysym,
        #     'char': event.char,
        #     'type': event.type,
        #     'state': event.state
        # }))
        self.enqueue_event('key', {
            'key': event.keysym,
            'char': event.char,
            'type': event.type,
            'state': event.state
        })
    
    def is_control_click(self, event):
        """Check if this is a control area click"""
        # Define a small control area in top-left corner (100x50 pixels)
        if event.x < 100 and event.y < 50:
            if event.type == '4':  # ButtonPress
                self.show_control_menu(event.x, event.y)
            return True
        return False
    
    def show_control_menu(self, x, y):
        """Show a simple control menu"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Update Screen (F5)", command=self.update_screen)
        menu.add_command(label="Toggle Passthrough", command=self.toggle_passthrough)
        menu.add_command(label="Quit (Ctrl+Q)", command=self.quit_app)
        
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()
    
    def handle_control_keys(self, event):
        """Handle our control key combinations"""
        if event.type == '2':  # KeyPress
            # Ctrl+Q to quit
            if event.state & 0x4 and event.keysym.lower() == 'q':
                self.quit_app()
                return True
            # F5 to update
            elif event.keysym == 'F5':
                self.update_screen() 
                return True
            # F6 to toggle passthrough
            elif event.keysym == 'F6':
                self.toggle_passthrough()
                return True
        return False
    
    def start_event_forwarding(self):
        """Start the event forwarding thread"""
        def forward_events():
            while True:
                try:
                    print(f"Queue before removing: {list(self.event_queue.queue)}")
                    event_type, event_data = self.event_queue.get(timeout=0.1)
                    print(f"Dequeued: ({event_type}, {event_data})")
                    print(f"Queue after removing: {list(self.event_queue.queue)}")
                    
                    if event_type == 'mouse_click':
                        self.forward_mouse_click(event_data)
                    elif event_type == 'mouse_scroll':
                        self.forward_mouse_scroll(event_data)
                    elif event_type == 'key':
                        self.forward_key_event(event_data)
                        
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Event forwarding error: {e}")
        
        # Start forwarding thread
        self.forward_thread = threading.Thread(target=forward_events, daemon=True)
        self.forward_thread.start()
    
    def forward_mouse_click(self, event_data):
        """Forward mouse click using pyautogui"""
        try:
            x, y = event_data['x'], event_data['y']
            button = event_data['button']
            event_type = event_data['type']
            
            # Don't move mouse - just click at current position
            # This prevents cursor shaking
            
            # Determine button name
            button_map = {1: 'left', 2: 'middle', 3: 'right'}
            button_name = button_map.get(button, 'left')
            
            # Forward the click without moving mouse
            if str(event_type) == '4':  # ButtonPress
                pyautogui.mouseDown(button=button_name)
            elif str(event_type) == '5':  # ButtonRelease  
                pyautogui.mouseUp(button=button_name)
                
        except Exception as e:
            print(f"Mouse click forward error: {e}")
    
    def forward_mouse_scroll(self, event_data):
        """Forward mouse scroll using pyautogui"""
        try:
            # Don't move mouse for scrolling either - just scroll at current position
            delta = event_data['delta']
            pyautogui.scroll(delta // 120)  # Convert delta to scroll clicks
            
        except Exception as e:
            print(f"Mouse scroll forward error: {e}")
    
    def forward_key_event(self, event_data):
        """Forward keyboard event using pyautogui"""
        try:
            key = event_data['key']
            char = event_data['char']
            event_type = event_data['type']
            
            # Convert tkinter key names to pyautogui names
            key_map = {
                'Return': 'enter',
                'BackSpace': 'backspace', 
                'Tab': 'tab',
                'Escape': 'esc',
                'space': 'space',
                'Up': 'up',
                'Down': 'down', 
                'Left': 'left',
                'Right': 'right',
                'Control_L': 'ctrl',
                'Control_R': 'ctrl',
                'Alt_L': 'alt',
                'Alt_R': 'alt',
                'Shift_L': 'shift',
                'Shift_R': 'shift'
            }
            
            pyautogui_key = key_map.get(key, char if char.isprintable() else key.lower())
            
            if str(event_type) == '2':  # KeyPress
                pyautogui.keyDown(pyautogui_key)
            elif str(event_type) == '3':  # KeyRelease
                pyautogui.keyUp(pyautogui_key)
                
        except Exception as e:
            print(f"Key forward error: {e}")
    
    def take_initial_screenshot(self):
        """Take the first screenshot when starting up"""
        try:
            print("Taking initial screenshot...")
            
            # Show loading message
            self.canvas.delete("all")
            self.canvas.create_text(
                self.width//2, self.height//2,
                text="Loading initial view...",
                fill="white",
                font=("Arial", 20)
            )
            
            # Add control hint
            self.canvas.create_text(
                50, 25,
                text="Click here for controls",
                fill="gray",
                font=("Arial", 10),
                anchor="nw"
            )
            
            self.root.update()
            
            # Hide window
            self.root.withdraw()
            self.root.update()
            time.sleep(0.5)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            print(f"Initial screenshot captured: {screenshot.size}")
            # Calculate screen ratio if not already calculated
            if not hasattr(self, 'screen_ratio'):
                self.screen_ratio = screenshot.size[0] // self.width
                print(f"Screen ratio: {self.screen_ratio}")            
            
            # Show window
            self.root.deiconify()
            
            # Process and display
            # screenshot = screenshot.resize((self.width, self.height), Image.Resampling.LANCZOS)
            scaled_width = screenshot.size[0] // self.screen_ratio
            scaled_height = screenshot.size[1] // self.screen_ratio
            screenshot = screenshot.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
            print(f"Scaled screenshot size: {screenshot.size}")

            self.photo = ImageTk.PhotoImage(screenshot)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            # Add control hint overlay
            self.canvas.create_rectangle(0, 0, 100, 50, fill="black", stipple="gray25")
            self.canvas.create_text(
                50, 25,
                text="Controls",
                fill="white",
                font=("Arial", 10)
            )
            
            print("✅ Initial screenshot displayed!")
            print("Ready! All clicks and keys will be forwarded to applications")
            print("Controls:")
            print("  F5: Update screen")
            print("  F6: Toggle passthrough")
            print("  Ctrl+Q: Quit")
            print("  Click top-left corner for menu")
            
        except Exception as e:
            print(f"❌ Initial screenshot failed: {e}")
            import traceback
            traceback.print_exc()
    
    def update_screen(self):
        """Update the screen capture"""
        if not self.is_active:
            return
            
        try:            
            # Temporarily disable passthrough during update
            old_passthrough = self.passthrough_active
            self.passthrough_active = False
            
            # Hide window
            self.root.withdraw()
            self.root.update()
            time.sleep(0.5)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Show window
            self.root.deiconify()
            
            # Process and display new screenshot
            # screenshot = screenshot.resize((self.width, self.height), Image.Resampling.LANCZOS)
            scaled_width = screenshot.size[0] // self.screen_ratio
            scaled_height = screenshot.size[1] // self.screen_ratio
            screenshot = screenshot.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
            print(f"Scaled screenshot size: {screenshot.size}")

            self.photo = ImageTk.PhotoImage(screenshot)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            # Add control hint overlay
            self.canvas.create_rectangle(0, 0, 100, 50, fill="black", stipple="gray25")
            self.canvas.create_text(
                50, 25,
                text="Controls",
                fill="white",
                font=("Arial", 10)
            )
            
            # Restore passthrough
            self.passthrough_active = old_passthrough
            
            print("✅ Screen updated!")
            
        except Exception as e:
            print(f"❌ Update failed: {e}")
    
    def toggle_passthrough(self):
        """Toggle event passthrough"""
        self.passthrough_active = not self.passthrough_active
        status = "enabled" if self.passthrough_active else "disabled"
        print(f"Event passthrough {status}")
    
    def quit_app(self):
        """Exit application"""
        print("Shutting down...")
        self.root.quit()
        sys.exit(0)
    
    def run(self):
        """Start the main loop"""
        print("Starting filter with pyautogui event forwarding...")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()

def main():
    print("Discrete Screen Filter with Event Forwarding")
    print("=" * 45)
    
    try:
        filter_app = DiscreteScreenFilter()
        filter_app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()