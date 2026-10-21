# MAKE SURE TO READ README BEFORE USE
# Make sure to read the license

import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pynput.mouse import Controller, Button
from pynput import keyboard

# ============================================================
# Configuration
# ============================================================

MAX_CPS = 5000
MIN_CPS = 1

mouse = Controller()
running = threading.Event()
shutdown = threading.Event()
state_lock = threading.Lock()

target_cps = 300
toggle_key = keyboard.Key.f8
capture_mode = False

# ============================================================
# Click engine
# ============================================================

def click_worker():
    global target_cps

    next_click = time.perf_counter()

    while not shutdown.is_set():
        if not running.is_set():
            next_click = time.perf_counter()
            shutdown.wait(0.01)
            continue

        with state_lock:
            cps = target_cps

        interval = 1.0 / max(MIN_CPS, min(MAX_CPS, cps))
        now = time.perf_counter()

        if now >= next_click:
            try:
                mouse.click(Button.left, 1)
            except Exception as exc:
                print("Mouse error:", exc)
                running.clear()
                continue

            next_click += interval

            if now - next_click > interval * 2:
                next_click = now + interval
        else:
            shutdown.wait(min(next_click - now, 0.002))


# ============================================================
# Hotkey handling
# ============================================================

def key_name(key):
    """Convert pynput keys to consistent display names."""
    if isinstance(key, keyboard.KeyCode):
        if key.char:
            return key.char.upper()
        return None

    special_names = {
        keyboard.Key.space: "SPACE",
        keyboard.Key.enter: "ENTER",
        keyboard.Key.tab: "TAB",
        keyboard.Key.esc: "ESC",
        keyboard.Key.backspace: "BACKSPACE",
        keyboard.Key.delete: "DELETE",
        keyboard.Key.insert: "INSERT",
        keyboard.Key.home: "HOME",
        keyboard.Key.end: "END",
        keyboard.Key.page_up: "PAGE UP",
        keyboard.Key.page_down: "PAGE DOWN",
        keyboard.Key.up: "UP",
        keyboard.Key.down: "DOWN",
        keyboard.Key.left: "LEFT",
        keyboard.Key.right: "RIGHT",
        keyboard.Key.caps_lock: "CAPS LOCK",
        keyboard.Key.ctrl: "CTRL",
        keyboard.Key.ctrl_l: "CTRL LEFT",
        keyboard.Key.ctrl_r: "CTRL RIGHT",
        keyboard.Key.shift: "SHIFT",
        keyboard.Key.shift_l: "SHIFT LEFT",
        keyboard.Key.shift_r: "SHIFT RIGHT",
        keyboard.Key.alt: "ALT",
        keyboard.Key.alt_l: "ALT LEFT",
        keyboard.Key.alt_r: "ALT RIGHT",
        keyboard.Key.cmd: "WINDOWS",
        keyboard.Key.cmd_l: "WINDOWS LEFT",
        keyboard.Key.cmd_r: "WINDOWS RIGHT",
    }

    if key in special_names:
        return special_names[key]

    name = str(key).replace("Key.", "").upper()

    if name.startswith("F") and name[1:].isdigit():
        return name

    return None


def key_from_name(name):
    """Convert a display name back into a pynput key."""
    name = name.upper().strip()

    special_keys = {
        "SPACE": keyboard.Key.space,
        "ENTER": keyboard.Key.enter,
        "TAB": keyboard.Key.tab,
        "ESC": keyboard.Key.esc,
        "BACKSPACE": keyboard.Key.backspace,
        "DELETE": keyboard.Key.delete,
        "INSERT": keyboard.Key.insert,
        "HOME": keyboard.Key.home,
        "END": keyboard.Key.end,
        "PAGE UP": keyboard.Key.page_up,
        "PAGE DOWN": keyboard.Key.page_down,
        "UP": keyboard.Key.up,
        "DOWN": keyboard.Key.down,
        "LEFT": keyboard.Key.left,
        "RIGHT": keyboard.Key.right,
        "CAPS LOCK": keyboard.Key.caps_lock,
        "CTRL": keyboard.Key.ctrl,
        "CTRL LEFT": keyboard.Key.ctrl_l,
        "CTRL RIGHT": keyboard.Key.ctrl_r,
        "SHIFT": keyboard.Key.shift,
        "SHIFT LEFT": keyboard.Key.shift_l,
        "SHIFT RIGHT": keyboard.Key.shift_r,
        "ALT": keyboard.Key.alt,
        "ALT LEFT": keyboard.Key.alt_l,
        "ALT RIGHT": keyboard.Key.alt_r,
        "WINDOWS": keyboard.Key.cmd,
        "WINDOWS LEFT": keyboard.Key.cmd_l,
        "WINDOWS RIGHT": keyboard.Key.cmd_r,
    }

    if name in special_keys:
        return special_keys[name]

    if len(name) == 1 and name.isalnum():
        return keyboard.KeyCode.from_char(name.lower())

    if name.startswith("F") and name[1:].isdigit():
        number = int(name[1:])
        if 1 <= number <= 24:
            return getattr(keyboard.Key, name.lower(), None)

    return None


def toggle_clicker():
    if running.is_set():
        running.clear()
        status_var.set("Status: OFF")
        toggle_button.config(text=f"START ({hotkey_var.get()})")
    else:
        running.set()
        status_var.set("Status: ON")
        toggle_button.config(text=f"STOP ({hotkey_var.get()})")


def on_key_press(key):
    global toggle_key, capture_mode

    name = key_name(key)

    if capture_mode:
        if name is None:
            return

        def apply_capture():
            global toggle_key, capture_mode

            new_key = key_from_name(name)
            if new_key is not None:
                toggle_key = new_key
                hotkey_var.set(name)
                hotkey_label.config(text=f"Toggle key: {name}")
                toggle_button.config(text=f"START ({name})")
                status_var.set(f"Hotkey saved: {name}")

            capture_mode = False
            capture_button.config(text="Capture Key")
            root.deiconify()

        root.after(0, apply_capture)
        return

    if key == toggle_key:
        root.after(0, toggle_clicker)


def capture_key():
    global capture_mode

    capture_mode = True
    status_var.set("Press any key to assign it...")
    capture_button.config(text="Press a key...")
    root.lift()
    root.focus_force()


def save_hotkey():
    global toggle_key

    selected = hotkey_var.get().strip().upper()
    new_key = key_from_name(selected)

    if new_key is None:
        messagebox.showerror("Invalid key", "Please select a supported key.")
        return

    toggle_key = new_key
    hotkey_label.config(text=f"Toggle key: {selected}")
    toggle_button.config(text=f"START ({selected})")
    status_var.set(f"Hotkey saved: {selected}")


# ============================================================
# CPS slider
# ============================================================

def update_cps(value):
    global target_cps

    cps = int(float(value))

    with state_lock:
        target_cps = cps

    cps_label.config(text=f"Target CPS: {cps:,}")


# ============================================================
# GUI
# ============================================================

root = tk.Tk()
root.title("Python Auto-Clicker")
root.geometry("390x390")
root.resizable(False, False)
root.attributes("-topmost", True)

style = ttk.Style()
style.configure("TButton", padding=6)

ttk.Label(
    root,
    text="High-Speed Auto-Clicker",
    font=("Segoe UI", 13, "bold")
).pack(pady=(12, 8))

cps_label = ttk.Label(root, text="Target CPS: 300")
cps_label.pack()

cps_slider = tk.Scale(
    root,
    from_=MIN_CPS,
    to=MAX_CPS,
    orient="horizontal",
    length=340,
    resolution=1,
    command=update_cps
)
cps_slider.set(300)
cps_slider.pack()

toggle_button = ttk.Button(
    root,
    text="START (F8)",
    command=toggle_clicker
)
toggle_button.pack(pady=8)

status_var = tk.StringVar(value="Status: OFF")
ttk.Label(root, textvariable=status_var).pack()

hotkey_frame = ttk.Frame(root)
hotkey_frame.pack(pady=8)

hotkey_var = tk.StringVar(value="F8")

ttk.Label(hotkey_frame, text="Toggle key:").grid(
    row=0, column=0, padx=5, pady=4
)

key_options = (
    [chr(i) for i in range(ord("A"), ord("Z") + 1)]
    + [str(i) for i in range(10)]
    + [f"F{i}" for i in range(1, 25)]
    + [
        "SPACE", "ENTER", "TAB", "ESC", "BACKSPACE",
        "DELETE", "INSERT", "HOME", "END",
        "PAGE UP", "PAGE DOWN", "UP", "DOWN",
        "LEFT", "RIGHT", "CAPS LOCK",
        "CTRL", "SHIFT", "ALT", "WINDOWS"
    ]
)

hotkey_box = ttk.Combobox(
    hotkey_frame,
    textvariable=hotkey_var,
    values=key_options,
    state="readonly",
    width=12
)
hotkey_box.grid(row=0, column=1, padx=5, pady=4)

ttk.Button(
    hotkey_frame,
    text="Save",
    command=save_hotkey
).grid(row=0, column=2, padx=5, pady=4)

capture_button = ttk.Button(
    root,
    text="Capture Key",
    command=capture_key
)
capture_button.pack(pady=4)

hotkey_label = ttk.Label(root, text="Toggle key: F8")
hotkey_label.pack(pady=3)

ttk.Label(
    root,
    text="Actual CPS depends on Windows and game input handling.",
    font=("Segoe UI", 8),
    wraplength=350
).pack(pady=8)


# ============================================================
# Startup and cleanup
# ============================================================

worker = threading.Thread(target=click_worker, daemon=True)
worker.start()

listener = keyboard.Listener(
    on_press=on_key_press
)
listener.start()


def close_app():
    running.clear()
    shutdown.set()
    listener.stop()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
