"""
Niri scrollable-tiling Wayland compositor backend for window-getter using UNIX socket IPC / niri msg JSON.
"""

import os
import json
import socket
import subprocess
from typing import List, Optional, Dict, Any
from window_getter.core.models import WindowInfo
from window_getter.core.proc import get_process_info
from window_getter.core.launcher import get_desktop_entry
from window_getter.core.compat import get_clean_env


class NiriBackend:
    @staticmethod
    def get_socket_path() -> Optional[str]:
        """Retrieve the Niri IPC socket path."""
        sock = os.environ.get("NIRI_SOCKET")
        if sock and os.path.exists(sock):
            return sock

        # Search runtime directories
        uid = os.getuid() if hasattr(os, "getuid") else 1000
        run_dir = f"/run/user/{uid}"
        if os.path.exists(run_dir):
            for fname in os.listdir(run_dir):
                if fname.startswith("niri") and fname.endswith(".sock"):
                    candidate = os.path.join(run_dir, fname)
                    if os.path.exists(candidate):
                        return candidate
        return None

    @staticmethod
    def is_available() -> bool:
        """Check if Niri compositor session is active."""
        if os.environ.get("NIRI_SOCKET") and os.path.exists(os.environ.get("NIRI_SOCKET", "")):
            return True

        try:
            res = subprocess.run(
                ["niri", "msg", "--json", "windows"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            return res.returncode == 0
        except Exception:
            return False

    def _query_niri(self, subcmd: str) -> Optional[Any]:
        """Query Niri CLI with JSON output."""
        try:
            res = subprocess.run(
                ["niri", "msg", "--json", subcmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                check=True,
                env=get_clean_env()
            )
            if res.stdout.strip():
                return json.loads(res.stdout.strip())
        except Exception as e:
            pass
        return None

    def _send_action(self, action_args: List[str]) -> bool:
        """Dispatch an action to Niri compositor."""
        try:
            cmd = ["niri", "msg", "action"] + action_args
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                env=get_clean_env()
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_windows(self) -> List[WindowInfo]:
        """Fetch all managed windows from Niri."""
        data = self._query_niri("windows")
        if not data or not isinstance(data, list):
            return []

        windows: List[WindowInfo] = []
        for item in data:
            win = self._parse_niri_window(item)
            if win:
                windows.append(win)
        return windows

    def get_active_window(self) -> Optional[WindowInfo]:
        """Fetch currently focused window in Niri."""
        windows = self.get_windows()
        for w in windows:
            if w.is_active:
                return w
        return windows[0] if windows else None

    def close_window(self, window_id: str) -> bool:
        """Close window by Niri window ID."""
        # Focus window first if ID provided, then close-window
        if window_id.isdigit():
            self._send_action(["focus-window", "--id", window_id])
        return self._send_action(["close-window"])

    def focus_window(self, window_id: str) -> bool:
        """Focus window by Niri window ID."""
        if window_id.isdigit():
            return self._send_action(["focus-window", "--id", window_id])
        return False

    def move_to_workspace(self, window_id: str, workspace_name_or_id: str) -> bool:
        """Move window to workspace in Niri."""
        if window_id.isdigit():
            self._send_action(["focus-window", "--id", window_id])
        return self._send_action(["move-window-to-workspace", str(workspace_name_or_id)])

    def _parse_niri_window(self, item: Dict[str, Any]) -> Optional[WindowInfo]:
        win_id = str(item.get("id", ""))
        title = item.get("title", "") or ""
        app_id = item.get("app_id", "") or ""
        pid = item.get("pid", 0) or 0
        is_focused = bool(item.get("is_focused", False))

        ws_id = item.get("workspace_id", 1) or 1
        ws_name = str(ws_id)

        # Parse layout geometry if available
        layout = item.get("layout", {})
        tile = layout.get("tile", {}) if isinstance(layout, dict) else {}
        x = int(tile.get("x", 0)) if isinstance(tile, dict) else 0
        y = int(tile.get("y", 0)) if isinstance(tile, dict) else 0
        width = int(tile.get("width", 0)) if isinstance(tile, dict) else 0
        height = int(tile.get("height", 0)) if isinstance(tile, dict) else 0

        proc_info = get_process_info(pid) if pid > 0 else None
        exe_path = proc_info.exe_path if proc_info else ""
        cwd = proc_info.cwd if proc_info else ""
        cmdline = proc_info.cmdline if proc_info else []
        memory_mb = proc_info.memory_mb if proc_info else 0.0
        cpu_percent = proc_info.cpu_percent if proc_info else 0.0

        entry = get_desktop_entry(app_id, exe_path)
        desktop_entry = entry.get("_filepath") if entry else None
        icon_name = entry.get("Icon") if entry else None

        return WindowInfo(
            address=win_id,
            app_id=app_id,
            title=title,
            pid=pid,
            x=x,
            y=y,
            width=width,
            height=height,
            workspace_id=int(ws_id) if str(ws_id).isdigit() else 1,
            workspace_name=ws_name,
            is_active=is_focused,
            exe_path=exe_path,
            cwd=cwd,
            cmdline=cmdline,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            desktop_entry=desktop_entry,
            icon_name=icon_name
        )
