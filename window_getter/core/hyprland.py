"""
Hyprland compositor backend for window-getter supporting direct UNIX domain socket IPC and hyprctl fallback.
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


class HyprlandBackend:
    @staticmethod
    def get_socket_path() -> Optional[str]:
        """Find the active Hyprland UNIX domain command socket."""
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
        uid = os.getuid() if hasattr(os, "getuid") else 1000

        candidate_paths = []
        if sig:
            candidate_paths.extend([
                f"/run/user/{uid}/hypr/{sig}/.socket.sock",
                f"/tmp/hypr/{sig}/.socket.sock",
            ])

        # Also search user runtime dir if signature env was not set or changed
        base_user_dir = f"/run/user/{uid}/hypr"
        if os.path.exists(base_user_dir):
            try:
                for entry in os.listdir(base_user_dir):
                    sock = os.path.join(base_user_dir, entry, ".socket.sock")
                    if os.path.exists(sock):
                        candidate_paths.append(sock)
            except Exception:
                pass

        base_tmp_dir = "/tmp/hypr"
        if os.path.exists(base_tmp_dir):
            try:
                for entry in os.listdir(base_tmp_dir):
                    sock = os.path.join(base_tmp_dir, entry, ".socket.sock")
                    if os.path.exists(sock):
                        candidate_paths.append(sock)
            except Exception:
                pass

        for p in candidate_paths:
            if os.path.exists(p):
                return p
        return None

    @staticmethod
    def _query_socket(cmd: str) -> Optional[str]:
        """Send command string to Hyprland UNIX domain socket and return response."""
        sock_path = HyprlandBackend.get_socket_path()
        if not sock_path:
            return None

        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect(sock_path)
            s.sendall(cmd.encode("utf-8"))
            chunks = []
            while True:
                try:
                    data = s.recv(8192)
                    if not data:
                        break
                    chunks.append(data)
                except Exception:
                    break
            s.close()
            return b"".join(chunks).decode("utf-8", errors="ignore")
        except Exception:
            return None

    @staticmethod
    def is_available() -> bool:
        """Check if Hyprland session is active via direct socket or hyprctl."""
        # 1. Direct socket check
        sock = HyprlandBackend.get_socket_path()
        if sock:
            res = HyprlandBackend._query_socket("j/activewindow")
            if res is not None:
                return True

        # 2. Subprocess check with clean env
        try:
            res = subprocess.run(
                ["hyprctl", "activewindow", "-j"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            return res.returncode == 0
        except Exception:
            return False

    def _query(self, json_cmd: str, hyprctl_subcmd: List[str]) -> Optional[str]:
        """Query Hyprland via direct socket, falling back to hyprctl with clean environment."""
        # Try direct socket first
        sock_res = self._query_socket(json_cmd)
        if sock_res is not None and sock_res.strip():
            return sock_res.strip()

        # Fallback to hyprctl
        try:
            res = subprocess.run(
                ["hyprctl"] + hyprctl_subcmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                check=True,
                env=get_clean_env()
            )
            return res.stdout.strip()
        except Exception:
            return None

    def _dispatch(self, dispatch_args: str, hyprctl_args: List[str]) -> bool:
        """Send dispatch command via socket or hyprctl."""
        sock_res = self._query_socket(f"dispatch {dispatch_args}")
        if sock_res is not None:
            return "ok" in sock_res.lower() or len(sock_res) == 0

        try:
            res = subprocess.run(
                ["hyprctl", "dispatch"] + hyprctl_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=get_clean_env()
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_windows(self) -> List[WindowInfo]:
        """Fetch all managed windows from Hyprland."""
        raw_json = self._query("j/clients", ["clients", "-j"])
        if not raw_json:
            return []

        try:
            data = json.loads(raw_json)
            active_addr = self.get_active_address()

            windows: List[WindowInfo] = []
            for item in data:
                win = self._parse_hyprland_window(item, active_addr)
                windows.append(win)
            return windows
        except Exception as e:
            print(f"[HyprlandBackend] Error parsing windows: {e}")
            return []

    def get_active_window(self) -> Optional[WindowInfo]:
        """Fetch active/focused window from Hyprland."""
        raw_json = self._query("j/activewindow", ["activewindow", "-j"])
        if not raw_json or raw_json == "{}":
            return None

        try:
            data = json.loads(raw_json)
            if not data.get("address"):
                return None
            return self._parse_hyprland_window(data, active_addr=data.get("address"), is_active_override=True)
        except Exception as e:
            print(f"[HyprlandBackend] Error parsing active window: {e}")
            return None

    def get_active_address(self) -> str:
        """Get active window address string."""
        raw_json = self._query("j/activewindow", ["activewindow", "-j"])
        if raw_json and raw_json != "{}":
            try:
                data = json.loads(raw_json)
                return data.get("address", "")
            except Exception:
                pass
        return ""

    def close_window(self, address_or_pid: str) -> bool:
        """Close window using `closewindow address:<addr>`."""
        target = address_or_pid if address_or_pid.startswith("address:") else f"address:{address_or_pid}"
        return self._dispatch(f"closewindow {target}", ["closewindow", target])

    def focus_window(self, address: str) -> bool:
        """Focus window using `focuswindow address:<addr>`."""
        target = address if address.startswith("address:") else f"address:{address}"
        return self._dispatch(f"focuswindow {target}", ["focuswindow", target])

    def move_to_workspace(self, address: str, workspace_name_or_id: str) -> bool:
        """Move window to workspace using `movetoworkspace <ws>,address:<addr>`."""
        target = address if address.startswith("address:") else f"address:{address}"
        arg = f"{workspace_name_or_id},{target}"
        return self._dispatch(f"movetoworkspace {arg}", ["movetoworkspace", arg])

    def toggle_floating(self, address: str) -> bool:
        """Toggle floating mode using `togglefloating address:<addr>`."""
        target = address if address.startswith("address:") else f"address:{address}"
        return self._dispatch(f"togglefloating {target}", ["togglefloating", target])

    def toggle_fullscreen(self, address: str) -> bool:
        """Toggle fullscreen mode using `fullscreen 0`."""
        self.focus_window(address)
        return self._dispatch("fullscreen 0", ["fullscreen", "0"])

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
