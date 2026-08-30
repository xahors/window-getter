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


class WindowDetector:
    def __init__(self):
        self._backend = None
        self._detect_backend()

    def _detect_backend(self):
        """Auto-detect active window manager backend."""
        # 1. Hyprland
        if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE") or HyprlandBackend.is_available():
            self._backend = HyprlandBackend()
            self.backend_name = "Hyprland"
            return

        # 2. Sway / i3
        if os.environ.get("SWAYSOCK") or SwayBackend.is_available():
            self._backend = SwayBackend()
            self.backend_name = "Sway"
            return

        # 3. X11
        if os.environ.get("DISPLAY") and X11Backend.is_available():
            self._backend = X11Backend()
            self.backend_name = "X11"
            return

        # Fallback to Hyprland as default if hyprctl works
        self._backend = HyprlandBackend()
        self.backend_name = "Hyprland (Fallback)"

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
            return False, f"Window matching query '{query}' not found."

        # Try window manager close first
        success = self._backend.close_window(win.address)
        if success:
            return True, f"Closed window '{win.display_title}' (App ID: {win.display_app_id}, Address: {win.address})."

        # Fallback to graceful SIGTERM on PID
        if win.pid > 0:
            return self.kill_process(win.pid, sig=signal.SIGTERM)

        return False, f"Failed to close window '{win.display_title}'."

    def kill_process(self, pid: int, sig: int = signal.SIGKILL) -> Tuple[bool, str]:
        """Force kill or terminate process by PID."""
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

        # 2. Relaunch window command targeting same workspace
        return core_relaunch_window(
            cmdline=win.cmdline,
            exe_path=win.exe_path,
            app_id=win.app_id,
            cwd=win.cwd,
            custom_command=custom_command,
            target_workspace=str(win.workspace_name or win.workspace_id)
        )



    def focus_window(self, query: str) -> Tuple[bool, str]:
        """Bring window into focus."""
        win = self.find_window(query)
        if not win:
            return False, f"Window matching query '{query}' not found."

        success = self._backend.focus_window(win.address)
        if success:
            return True, f"Focused window '{win.display_title}'."
        return False, f"Failed to focus window '{win.display_title}'."

    def move_to_workspace(self, query: str, workspace: str) -> Tuple[bool, str]:
        """Move window to specified workspace."""
        win = self.find_window(query)
        if not win:
            return False, f"Window matching query '{query}' not found."

        if hasattr(self._backend, "move_to_workspace"):
            success = self._backend.move_to_workspace(win.address, workspace)
            if success:
                return True, f"Moved window '{win.display_title}' to workspace {workspace}."
        return False, f"Moving workspaces not supported by current backend."

    def toggle_floating(self, query: str) -> Tuple[bool, str]:
        """Toggle window floating state."""
        win = self.find_window(query)
        if not win:
            return False, f"Window matching query '{query}' not found."

        if hasattr(self._backend, "toggle_floating"):
            success = self._backend.toggle_floating(win.address)
            if success:
                return True, f"Toggled floating for window '{win.display_title}'."
        return False, "Toggle floating not supported by backend."

    def toggle_fullscreen(self, query: str) -> Tuple[bool, str]:
        """Toggle window fullscreen state."""
        win = self.find_window(query)
        if not win:
            return False, f"Window matching query '{query}' not found."

        if hasattr(self._backend, "toggle_fullscreen"):
            success = self._backend.toggle_fullscreen(win.address)
            if success:
                return True, f"Toggled fullscreen for window '{win.display_title}'."
        return False, "Toggle fullscreen not supported by backend."


# Global detector instance
_detector = WindowDetector()


def get_detector() -> WindowDetector:
    return _detector
