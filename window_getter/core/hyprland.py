"""
Hyprland compositor backend for window-getter using hyprctl JSON IPC.
"""

import json
import subprocess
from typing import List, Optional, Dict, Any
from window_getter.core.models import WindowInfo
from window_getter.core.proc import get_process_info
from window_getter.core.launcher import get_desktop_entry


class HyprlandBackend:
    @staticmethod
    def is_available() -> bool:
        """Check if hyprctl command is present and Hyprland session is active."""
        try:
            res = subprocess.run(
                ["hyprctl", "activewindow", "-j"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_windows(self) -> List[WindowInfo]:
        """Fetch all managed windows from Hyprland via `hyprctl clients -j`."""
        try:
            res = subprocess.run(
                ["hyprctl", "clients", "-j"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                check=True
            )
            data = json.loads(res.stdout)
            active_addr = self.get_active_address()
            
            windows: List[WindowInfo] = []
            for item in data:
                win = self._parse_hyprland_window(item, active_addr)
                windows.append(win)
            return windows
        except Exception as e:
            print(f"[HyprlandBackend] Error getting windows: {e}")
            return []

    def get_active_window(self) -> Optional[WindowInfo]:
        """Fetch active/focused window from Hyprland via `hyprctl activewindow -j`."""
        try:
            res = subprocess.run(
                ["hyprctl", "activewindow", "-j"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                check=True
            )
            if not res.stdout.strip() or res.stdout.strip() == "{}":
                return None
            data = json.loads(res.stdout)
            if not data.get("address"):
                return None
            return self._parse_hyprland_window(data, active_addr=data.get("address"), is_active_override=True)
        except Exception as e:
            print(f"[HyprlandBackend] Error getting active window: {e}")
            return None

    def get_active_address(self) -> str:
        """Get active window address string."""
        try:
            res = subprocess.run(
                ["hyprctl", "activewindow", "-j"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                return data.get("address", "")
        except Exception:
            pass
        return ""

    def close_window(self, address_or_pid: str) -> bool:
        """Close window using `hyprctl dispatch closewindow address:<addr>`."""
        try:
            target = address_or_pid
            if not target.startswith("0x"):
                target = f"address:{address_or_pid}"
            else:
                target = f"address:{address_or_pid}"
                
            cmd = ["hyprctl", "dispatch", "closewindow", target]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode == 0
        except Exception as e:
            print(f"[HyprlandBackend] Error closing window: {e}")
            return False

    def focus_window(self, address: str) -> bool:
        """Focus window using `hyprctl dispatch focuswindow address:<addr>`."""
        try:
            target = address if address.startswith("address:") else f"address:{address}"
            cmd = ["hyprctl", "dispatch", "focuswindow", target]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode == 0
        except Exception as e:
            print(f"[HyprlandBackend] Error focusing window: {e}")
            return False

    def move_to_workspace(self, address: str, workspace_name_or_id: str) -> bool:
        """Move window to workspace using `hyprctl dispatch movetoworkspace <ws>,address:<addr>`."""
        try:
            target = address if address.startswith("address:") else f"address:{address}"
            cmd = ["hyprctl", "dispatch", "movetoworkspace", f"{workspace_name_or_id},{target}"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode == 0
        except Exception as e:
            print(f"[HyprlandBackend] Error moving to workspace: {e}")
            return False

    def toggle_floating(self, address: str) -> bool:
        """Toggle floating mode using `hyprctl dispatch togglefloating address:<addr>`."""
        try:
            target = address if address.startswith("address:") else f"address:{address}"
            cmd = ["hyprctl", "dispatch", "togglefloating", target]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode == 0
        except Exception as e:
            print(f"[HyprlandBackend] Error toggling floating: {e}")
            return False

    def toggle_fullscreen(self, address: str) -> bool:
        """Toggle fullscreen mode using `hyprctl dispatch fullscreen 0` after focusing window."""
        try:
            self.focus_window(address)
            cmd = ["hyprctl", "dispatch", "fullscreen", "0"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode == 0
        except Exception as e:
            print(f"[HyprlandBackend] Error toggling fullscreen: {e}")
            return False

    def _parse_hyprland_window(self, item: Dict[str, Any], active_addr: str = "", is_active_override: bool = False) -> WindowInfo:
        addr = item.get("address", "")
        pid = item.get("pid", 0)
        app_id = item.get("class", "")
        initial_class = item.get("initialClass", "")
        title = item.get("title", "")
        initial_title = item.get("initialTitle", "")

        at = item.get("at", [0, 0])
        size = item.get("size", [0, 0])
        x = at[0] if len(at) > 0 else 0
        y = at[1] if len(at) > 1 else 0
        width = size[0] if len(size) > 0 else 0
        height = size[1] if len(size) > 1 else 0

        ws = item.get("workspace", {})
        ws_id = ws.get("id", 1) if isinstance(ws, dict) else 1
        ws_name = str(ws.get("name", ws_id)) if isinstance(ws, dict) else str(ws)

        is_active = is_active_override or (addr and addr == active_addr) or (item.get("focusHistoryID") == 0)
        is_visible = bool(item.get("visible", True))
        is_mapped = bool(item.get("mapped", True))
        is_floating = bool(item.get("floating", False))
        is_fullscreen = bool(item.get("fullscreen", 0) != 0)
        is_xwayland = bool(item.get("xwayland", False))
        focus_hist = item.get("focusHistoryID", 0)
        monitor_id = item.get("monitor", 0)

        # Enrich process data
        proc_info = get_process_info(pid) if pid > 0 else None
        exe_path = proc_info.exe_path if proc_info else ""
        cwd = proc_info.cwd if proc_info else ""
        cmdline = proc_info.cmdline if proc_info else []
        memory_mb = proc_info.memory_mb if proc_info else 0.0
        cpu_percent = proc_info.cpu_percent if proc_info else 0.0

        # Resolve desktop entry & icon
        desktop_entry_path = None
        icon_name = None
        entry = get_desktop_entry(app_id, exe_path)
        if entry:
            desktop_entry_path = entry.get("_filepath")
            icon_name = entry.get("Icon")

        return WindowInfo(
            address=addr,
            app_id=app_id,
            title=title,
            pid=pid,
            x=x,
            y=y,
            width=width,
            height=height,
            workspace_id=ws_id,
            workspace_name=ws_name,
            monitor_id=monitor_id,
            is_active=is_active,
            is_visible=is_visible,
            is_mapped=is_mapped,
            is_floating=is_floating,
            is_fullscreen=is_fullscreen,
            is_xwayland=is_xwayland,
            initial_class=initial_class,
            initial_title=initial_title,
            focus_history_id=focus_hist,
            exe_path=exe_path,
            cwd=cwd,
            cmdline=cmdline,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            desktop_entry=desktop_entry_path,
            icon_name=icon_name
        )
