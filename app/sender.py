"""
Sender Module
Handles erasing trigger characters via Backspace and injecting replacement text
using native Windows Win32 keybd_event (Unicode keystrokes) or Clipboard Paste.
"""

import time
import threading
import win32api
import win32con
import pyperclip

# Magic tag for dwExtraInfo to prevent the hook from capturing our simulated inputs
MAGIC_EXTRA_INFO = 0x414E5449  # ASCII for 'ANTI'

# Win32 Unicode Key Event flag (0x0004)
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = win32con.KEYEVENTF_KEYUP


def erase_characters(count: int):
    """Sends `count` backspaces to erase the typed trigger text."""
    if count <= 0:
        return
    for _ in range(count):
        win32api.keybd_event(win32con.VK_BACK, 0, 0, MAGIC_EXTRA_INFO)
        win32api.keybd_event(win32con.VK_BACK, 0, KEYEVENTF_KEYUP, MAGIC_EXTRA_INFO)


def send_unicode_text(text: str):
    """Sends text character-by-character using Win32 KEYEVENTF_UNICODE at maximum speed."""
    for char in text:
        if char == "\r":
            continue
        if char == "\n":
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, MAGIC_EXTRA_INFO)
            win32api.keybd_event(win32con.VK_RETURN, 0, KEYEVENTF_KEYUP, MAGIC_EXTRA_INFO)
        else:
            code = ord(char)
            win32api.keybd_event(0, code, KEYEVENTF_UNICODE, MAGIC_EXTRA_INFO)
            win32api.keybd_event(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, MAGIC_EXTRA_INFO)


def send_clipboard_paste(text: str):
    """Injects text by placing it onto the clipboard and sending Ctrl+V."""
    old_clip = None
    try:
        old_clip = pyperclip.paste()
    except Exception:
        pass

    try:
        pyperclip.copy(text)
    except Exception:
        send_unicode_text(text)
        return

    time.sleep(0.01)

    # Send Ctrl+V
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, MAGIC_EXTRA_INFO)
    win32api.keybd_event(ord("V"), 0, 0, MAGIC_EXTRA_INFO)
    win32api.keybd_event(ord("V"), 0, KEYEVENTF_KEYUP, MAGIC_EXTRA_INFO)
    win32api.keybd_event(win32con.VK_CONTROL, 0, KEYEVENTF_KEYUP, MAGIC_EXTRA_INFO)

    # Restore old clipboard in background thread after safe delay
    if old_clip is not None:
        def restore():
            time.sleep(0.3)
            try:
                pyperclip.copy(old_clip)
            except Exception:
                pass
        threading.Thread(target=restore, daemon=True).start()


def send_left_arrows(count: int):
    """Sends left arrow keys to reposition the cursor."""
    if count <= 0:
        return
    for _ in range(count):
        win32api.keybd_event(win32con.VK_LEFT, 0, 0, MAGIC_EXTRA_INFO)
        win32api.keybd_event(win32con.VK_LEFT, 0, KEYEVENTF_KEYUP, MAGIC_EXTRA_INFO)


def replace_text(
    backspace_count: int,
    replacement_text: str,
    method: str = "auto",
    cursor_offset: int = 0,
    delay_ms: int = 5,
):
    """
    Executes the full text replacement:
    1. Erases the typed trigger characters.
    2. Waits `delay_ms` milliseconds for target application to digest backspaces.
    3. Injects the replacement text via SendInput or Clipboard.
    4. Adjusts cursor if needed.
    """
    erase_characters(backspace_count)

    if delay_ms > 0:
        time.sleep(delay_ms / 1000.0)

    if method == "clipboard":
        send_clipboard_paste(replacement_text)
    elif method == "sendinput":
        send_unicode_text(replacement_text)
    else:  # "auto"
        if "\n" in replacement_text or len(replacement_text) > 80:
            send_clipboard_paste(replacement_text)
        else:
            send_unicode_text(replacement_text)

    if cursor_offset > 0:
        time.sleep(0.005)
        send_left_arrows(cursor_offset)
