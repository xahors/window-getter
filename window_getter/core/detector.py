"""
Window detector manager and unified interface across Hyprland, Sway, and X11 backends.
"""

import os
import signal
import subprocess
from typing import List, Optional, Tuple, Dict
from window_getter.core.models import WindowInfo, WorkspaceInfo
from window_getter.core.hyprland import HyprlandBackend
from window_getter.core.sway import SwayBackend
from window_getter.core.x11 import X11Backend
from window_getter.core.launcher import relaunch_window as core_relaunch_window, launch_new_command


class GenericBackend:
    """Fallback backend when no supported window manager IPC is active."""
    @staticmethod
    def is_available() -> bool:
        return True

    def get_windows(self) -> List[WindowInfo]:
        return []

    def get_active_window(self) -> Optional[WindowInfo]:
        return None

    def close_window(self, address: str) -> bool:
        return False

    def focus_window(self, address: str) -> bool:
        return False


class WindowDetector:
    def __init__(self):
        self._backend = None
        self._detect_backend()

    def _detect_backend(self):
        """Auto-detect active window manager backend."""
        # 1. Hyprland (Check signature first, or verify hyprctl returns 0)
        if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE") and HyprlandBackend.is_available():
            self._backend = HyprlandBackend()
            self.backend_name = "Hyprland"
            return
        elif HyprlandBackend.is_available():
            self._backend = HyprlandBackend()
            self.backend_name = "Hyprland"
            return

        # 2. Sway / i3 (Check socket or swaymsg tree)
        if (os.environ.get("SWAYSOCK") or os.environ.get("I3SOCK")) and SwayBackend.is_available():
            self._backend = SwayBackend()
            self.backend_name = "Sway"
            return
        elif SwayBackend.is_available():
            self._backend = SwayBackend()
            self.backend_name = "Sway"
            return

        # 3. X11 (Check DISPLAY and X11 tools)
        if os.environ.get("DISPLAY") and X11Backend.is_available():
            self._backend = X11Backend()
            self.backend_name = "X11"
            return

        # 4. Generic fallback when no supported WM is active
        self._backend = GenericBackend()
        self.backend_name = "Generic / Unsupported"

    def get_windows(self) -> List[WindowInfo]:
        """Fetch all managed GUI windows."""
        if not self._backend:
            return []
        return self._backend.get_windows()

    def get_active_window(self) -> Optional[WindowInfo]:
        """Fetch the currently active/focused window."""
        if not self._backend:
            return None
        return self._backend.get_active_window()

    def get_workspaces(self) -> List[WorkspaceInfo]:
        """Group windows into workspace summaries."""
        windows = self.get_windows()
        workspaces_map: Dict[str, WorkspaceInfo] = {}

        for w in windows:
            ws_key = str(w.workspace_name or w.workspace_id)
            if ws_key not in workspaces_map:
                try:
                    ws_id = int(w.workspace_id)
                except Exception:
                    ws_id = 1
                workspaces_map[ws_key] = WorkspaceInfo(
                    id=ws_id,
                    name=ws_key,
                    windows_count=0,
                    has_active=False
                )

            ws_info = workspaces_map[ws_key]
            ws_info.windows_count += 1
            if w.is_active:
                ws_info.has_active = True

        return sorted(list(workspaces_map.values()), key=lambda x: x.id)

    def find_window(self, query: str) -> Optional[WindowInfo]:
        """
        Search for a window by 'active', address, PID, title, or app_id substring.
        """
        if not query or not query.strip():
            return self.get_active_window()

        q = query.strip()
        if q.lower() == "active":
            return self.get_active_window()

        windows = self.get_windows()

        # 1. Match address
        for w in windows:
            if w.address.lower() == q.lower():
                return w

        # 2. Match exact PID
        if q.isdigit():
            pid_target = int(q)
            for w in windows:
                if w.pid == pid_target:
                    return w

        # 3. Match app_id substring
        for w in windows:
            if q.lower() in w.app_id.lower():
                return w

        # 4. Match title substring
        for w in windows:
            if q.lower() in w.title.lower():
                return w

        return None

    def close_window(self, query: str) -> Tuple[bool, str]:
        """Close window by query (active, address, PID, app_id, title)."""
        win = self.find_window(query)
        if not win:
            if query.isdigit():
                return self.kill_process(int(query), sig=signal.SIGTERM)
            return False, f"Window matching query '{query}' not found."

        # 1. Try window manager close first
        if self._backend:
            success = self._backend.close_window(win.address)
            if success:
                return True, f"Closed window '{win.display_title}' (App ID: {win.display_app_id}, Address: {win.address})."

        # 2. Fallback to graceful SIGTERM on PID
        if win.pid > 0:
            return self.kill_process(win.pid, sig=signal.SIGTERM)

        return False, f"Failed to close window '{win.display_title}'."

    def kill_process(self, pid: int, sig: int = signal.SIGKILL) -> Tuple[bool, str]:
        """Force kill or terminate process by PID using POSIX signals."""
        try:
            if pid <= 0:
                return False, "Invalid Process ID."
            os.kill(pid, sig)
            sig_name = "SIGKILL" if sig == signal.SIGKILL else "SIGTERM"
            return True, f"Sent {sig_name} to process PID {pid}."
        except ProcessLookupError:
            return False, f"Process PID {pid} no longer exists."
        except PermissionError:
            return False, f"Permission denied to kill PID {pid}."
        except Exception as e:
            return False, f"Error killing PID {pid}: {str(e)}"

    def relaunch_window(self, query: str, custom_command: str = "") -> Tuple[bool, str]:
        """Safely close target window and relaunch application."""
        win = self.find_window(query)
        if not win:
            # If query is a custom command string, attempt launching it directly
            if custom_command:
                return launch_new_command(custom_command)
            elif query and not query.isdigit() and not query.startswith("0x"):
                return launch_new_command(query)
            return False, f"Window matching query '{query}' not found."

        # 1. Safely close active window
        self.close_window(win.address)
        import time
        time.sleep(0.15)

        # 2. Relaunch window command
        return core_relaunch_window(
            cmdline=win.cmdline,
            exe_path=win.exe_path,
            app_id=win.app_id,
            cwd=win.cwd,
            custom_command=custom_command
        )

    def focus_window(self, query: str) -> Tuple[bool, str]:
        """Bring window into focus."""
        win = self.find_window(query)
        if not win:
            return False, f"Window matching query '{query}' not found."

        if self._backend:
            success = self._backend.focus_window(win.address)
            if success:
                return True, f"Focused window '{win.display_title}'."
        return False, f"Failed to focus window '{win.display_title}'."


# Global singleton helper
_detector_instance: Optional[WindowDetector] = None


def get_detector() -> WindowDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = WindowDetector()
    return _detector_instance
