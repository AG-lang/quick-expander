"""
Expansion Engine Module
Listens to global keyboard input across the OS, matches triggers against registered snippets,
supports single instant expansion and multi-candidate floating popup selection.
"""

import time
import threading
import winsound
from typing import Callable, Optional
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

from .config import ConfigManager
from .variables import resolve_variables
from .sender import replace_text

VK_NUMPAD_MAP = {
    96: "0", 97: "1", 98: "2", 99: "3", 100: "4",
    101: "5", 102: "6", 103: "7", 104: "8", 105: "9",
    106: "*", 107: "+", 109: "-", 110: ".", 111: "/"
}


class ExpansionEngine:
    def __init__(self, config_mgr: ConfigManager):
        self.config_mgr = config_mgr
        self.buffer = ""
        self.max_buffer_len = 80
        self.is_expanding = False
        self.lock = threading.Lock()

        # Multi-candidate state
        self.candidate_mode = False
        self.active_candidates: list[dict] = []
        self.active_backspace_count = 0
        
        self.listener: Optional[keyboard.Listener] = None
        self.hotkey_listener: Optional[keyboard.GlobalHotKeys] = None
        self._running = False
        
        # State tracking
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.win_pressed = False

        # Callbacks for UI updates
        self.on_expanded: Optional[Callable[[dict, str], None]] = None
        self.on_status_changed: Optional[Callable[[bool], None]] = None
        self.on_show_candidates: Optional[Callable[[list[dict], str], None]] = None
        self.on_hide_candidates: Optional[Callable[[], None]] = None

    @property
    def is_enabled(self) -> bool:
        return self.config_mgr.config.get("enabled", True)

    @is_enabled.setter
    def is_enabled(self, value: bool):
        self.config_mgr.config["enabled"] = bool(value)
        self.config_mgr.save_config()
        self.buffer = ""
        self._cancel_candidates()
        if self.on_status_changed:
            self.on_status_changed(self.is_enabled)

    def toggle_enabled(self):
        """Toggles the global active state."""
        self.is_enabled = not self.is_enabled
        if self.config_mgr.config.get("play_sound", False):
            try:
                freq = 1500 if self.is_enabled else 800
                winsound.Beep(freq, 80)
            except Exception:
                pass

    def start(self):
        """Starts the keyboard listener and hotkey monitor."""
        if self._running:
            return
        self._running = True
        
        # Setup main keyboard listener
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
            suppress=False
        )
        self.listener.daemon = True
        self.listener.start()

        # Setup global hotkey
        self._setup_hotkey()

    def stop(self):
        """Stops listeners cleanly."""
        self._running = False
        self._cancel_candidates()
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None
            
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
            self.hotkey_listener = None

    def _setup_hotkey(self):
        """Registers the toggle hotkey from config."""
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
            self.hotkey_listener = None

        hotkey_str = self.config_mgr.config.get("hotkey_toggle", "<ctrl>+<alt>+s")
        if not hotkey_str:
            return

        try:
            self.hotkey_listener = keyboard.GlobalHotKeys({
                hotkey_str: self.toggle_enabled
            })
            self.hotkey_listener.daemon = True
            self.hotkey_listener.start()
        except Exception as e:
            print(f"[Engine] Failed to bind hotkey '{hotkey_str}': {e}")

    def update_hotkey(self, new_hotkey: str):
        """Updates and restarts the global toggle hotkey."""
        self.config_mgr.config["hotkey_toggle"] = new_hotkey
        self.config_mgr.save_config()
        self._setup_hotkey()

    def _extract_char(self, key) -> Optional[str]:
        """Extracts a printable character or control symbol from a key event."""
        if hasattr(key, "char") and key.char is not None:
            return key.char
        if hasattr(key, "vk") and key.vk in VK_NUMPAD_MAP:
            return VK_NUMPAD_MAP[key.vk]
        if key == Key.space:
            return " "
        if key == Key.tab:
            return "\t"
        if key == Key.enter:
            return "\n"
        return None

    def _cancel_candidates(self):
        """Cancels active candidate mode and hides popup."""
        if self.candidate_mode:
            self.candidate_mode = False
            self.active_candidates = []
            self.active_backspace_count = 0
            if self.on_hide_candidates:
                self.on_hide_candidates()

    def select_candidate_direct(self, snippet: dict):
        """Called when user clicks on a candidate in the popup window."""
        with self.lock:
            backspace_count = self.active_backspace_count
            self.candidate_mode = False
            self.active_candidates = []
            self.active_backspace_count = 0
            self.buffer = ""

            if self.on_hide_candidates:
                self.on_hide_candidates()

            self.is_expanding = True
            threading.Thread(
                target=self._execute_expansion,
                args=(snippet, backspace_count),
                daemon=True
            ).start()

    def _on_key_press(self, key):
        """Processes each key press globally."""
        if self.is_expanding:
            return

        # Track modifiers
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            self.ctrl_pressed = True
            self._cancel_candidates()
            return
        if key in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
            self.alt_pressed = True
            self._cancel_candidates()
            return
        if key in (Key.cmd, Key.cmd_l, Key.cmd_r):
            self.win_pressed = True
            self._cancel_candidates()
            return

        # If Ctrl/Alt/Win is currently pressed with another key, clear buffer
        if self.ctrl_pressed or self.alt_pressed or self.win_pressed:
            with self.lock:
                self.buffer = ""
                self._cancel_candidates()
            return

        # Handle Candidate Selection Mode (1-9 or Esc)
        if self.candidate_mode:
            char = self._extract_char(key)
            if char in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
                idx = int(char) - 1
                if idx < len(self.active_candidates):
                    chosen = self.active_candidates[idx]
                    self.select_candidate_direct(chosen)
                    return

            if key == Key.esc:
                self._cancel_candidates()
                return

            # Any other key cancels candidates mode and continues processing
            self._cancel_candidates()

        # Navigation / Reset keys clear the typing buffer
        if key in (Key.esc, Key.left, Key.right, Key.up, Key.down,
                   Key.home, Key.end, Key.page_up, Key.page_down,
                   Key.delete, Key.insert):
            with self.lock:
                self.buffer = ""
                self._cancel_candidates()
            return

        # Backspace pops the last typed character
        if key == Key.backspace:
            with self.lock:
                if self.buffer:
                    self.buffer = self.buffer[:-1]
                self._cancel_candidates()
            return

        # If globally disabled, do not process expansion
        if not self.is_enabled:
            return

        char = self._extract_char(key)
        if char is None:
            return

        with self.lock:
            self.buffer += char
            if len(self.buffer) > self.max_buffer_len:
                self.buffer = self.buffer[-self.max_buffer_len:]

            self._check_and_expand()

    def _on_key_release(self, key):
        """Tracks release of modifier keys."""
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            self.ctrl_pressed = False
        elif key in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
            self.alt_pressed = False
        elif key in (Key.cmd, Key.cmd_l, Key.cmd_r):
            self.win_pressed = False

    def _check_and_expand(self):
        """Checks if current buffer matches any active snippet triggers."""
        if not self.buffer:
            return

        enabled_snippets = self.config_mgr.get_enabled_snippets()
        if not enabled_snippets:
            return

        # Group matches by matched trigger
        matched_trigger = ""
        matched_snippets: list[dict] = []
        backspace_count = 0

        # Sort triggers by length descending to find the longest matching trigger first
        unique_triggers = sorted(
            list({s.get("trigger", "") for s in enabled_snippets if s.get("trigger")}),
            key=len,
            reverse=True
        )

        for trigger in unique_triggers:
            # Check instant match
            matched = False
            for s in enabled_snippets:
                if s.get("trigger") == trigger:
                    match_case = s.get("match_case", True)
                    mode = s.get("mode", "instant")

                    if mode == "instant":
                        if match_case and self.buffer.endswith(trigger):
                            matched = True
                        elif not match_case and self.buffer.lower().endswith(trigger.lower()):
                            matched = True
                    elif mode == "trigger_key":
                        if len(self.buffer) > len(trigger):
                            last_char = self.buffer[-1]
                            if last_char in (" ", "\t", "\n"):
                                preceding = self.buffer[:-1]
                                if match_case and preceding.endswith(trigger):
                                    matched = True
                                    backspace_count = len(trigger) + 1
                                elif not match_case and preceding.lower().endswith(trigger.lower()):
                                    matched = True
                                    backspace_count = len(trigger) + 1

            if matched:
                matched_trigger = trigger
                if backspace_count == 0:
                    backspace_count = len(trigger)
                # Find all snippets for this trigger
                matched_snippets = [s for s in enabled_snippets if s.get("trigger") == trigger]
                break

        if not matched_snippets:
            return

        # Case 1: Exactly 1 matching snippet -> Instant expansion!
        if len(matched_snippets) == 1:
            snippet = matched_snippets[0]
            self.is_expanding = True
            self.buffer = ""
            self._cancel_candidates()
            
            threading.Thread(
                target=self._execute_expansion,
                args=(snippet, backspace_count),
                daemon=True
            ).start()

        # Case 2: Multiple matching snippets -> Show Candidate Popup Window!
        else:
            self.candidate_mode = True
            self.active_candidates = matched_snippets
            self.active_backspace_count = backspace_count
            if self.on_show_candidates:
                self.on_show_candidates(matched_snippets, matched_trigger)

    def _execute_expansion(self, snippet: dict, backspace_count: int):
        """Executes the actual erasing and typing of replacement text."""
        try:
            raw_replacement = snippet.get("replacement", "")
            resolved_text, cursor_offset = resolve_variables(raw_replacement)
            
            method = snippet.get("method") or self.config_mgr.config.get("default_method", "auto")
            delay_ms = self.config_mgr.config.get("backspace_delay_ms", 5)

            # Perform text replacement
            replace_text(
                backspace_count=backspace_count,
                replacement_text=resolved_text,
                method=method,
                cursor_offset=cursor_offset,
                delay_ms=delay_ms
            )

            # Update notification immediately
            if self.on_expanded:
                self.on_expanded(snippet, resolved_text)

            # Update stats in background
            self.config_mgr.increment_use_count(snippet["id"])

            # Audio feedback if enabled
            if self.config_mgr.config.get("play_sound", False):
                try:
                    winsound.Beep(1800, 35)
                except Exception:
                    pass

        except Exception as e:
            print(f"[Engine] Expansion error for snippet '{snippet.get('trigger')}': {e}")
        finally:
            time.sleep(0.02)
            self.is_expanding = False
