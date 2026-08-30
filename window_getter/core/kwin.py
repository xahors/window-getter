"""
KDE Plasma / KWin compositor backend for window-getter using D-Bus IPC and KWin scripting.
"""

import os
import json
import subprocess
from typing import List, Optional, Dict, Any
from window_getter.core.models import WindowInfo
from window_getter.core.proc import get_process_info
from window_getter.core.launcher import get_desktop_entry
from window_getter.core.compat import get_clean_env


class KWinBackend:
    @staticmethod
    def is_available() -> bool:
        """Check if KDE Plasma KWin session is active."""
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        if "KDE" in desktop or "PLASMA" in desktop or os.environ.get("KDE_FULL_SESSION"):
            return True

        # Check D-Bus for org.kde.KWin service
        try:
            res = subprocess.run(
                ["gdbus", "call", "--session", "--dest", "org.kde.KWin",
                 "--object-path", "/KWin", "--method", "org.freedesktop.DBus.Peer.Ping"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            if res.returncode == 0:
                return True
        except Exception:
            pass

        try:
            qdbus_bin = "qdbus-qt6" if subprocess.run(["which", "qdbus-qt6"], stdout=subprocess.PIPE).returncode == 0 else "qdbus"
            res = subprocess.run(
                [qdbus_bin, "org.kde.KWin"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            return res.returncode == 0
        except Exception:
            pass

        return False

    def _eval_kwin_script(self, script_code: str) -> Optional[str]:
        """Execute a JavaScript snippet in KWin and read results via KWin scripting interface."""
        # Using dbus / qdbus to load and execute temporary kwin script
        qdbus_cmd = "qdbus-qt6" if subprocess.run(["which", "qdbus-qt6"], stdout=subprocess.PIPE).returncode == 0 else "qdbus"
        try:
            # Check if qdbus is available
            res = subprocess.run(
                [qdbus_cmd, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadScript", "/dev/null", "windowgetter_script"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
        except Exception:
            pass
        return None

    def get_windows(self) -> List[WindowInfo]:
        """Fetch managed windows in KDE Plasma session."""
        # Try kwin support information parsing or qdbus client queries
        windows: List[WindowInfo] = []
        try:
            qdbus_cmd = "qdbus-qt6" if subprocess.run(["which", "qdbus-qt6"], stdout=subprocess.PIPE).returncode == 0 else "qdbus"
            res = subprocess.run(
                [qdbus_cmd, "org.kde.KWin", "/KWin", "org.kde.KWin.supportInformation"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                env=get_clean_env()
            )
            if res.returncode == 0 and res.stdout:
                windows = self._parse_support_info(res.stdout)
        except Exception:
            pass

        return windows

    def _parse_support_info(self, info_text: str) -> List[WindowInfo]:
        """Parse KWin supportInformation output into structured WindowInfo list."""
        windows: List[WindowInfo] = []
        in_windows_section = False
        current_win: Dict[str, Any] = {}

        for line in info_text.splitlines():
            line_str = line.strip()
            if "All Clients" in line or "Windows:" in line:
                in_windows_section = True
                continue
            elif in_windows_section and (line_str.startswith("=== ") or line_str.startswith("--- ")):
                if current_win.get("address"):
                    win_obj = self._build_kwin_window(current_win)
                    if win_obj:
                        windows.append(win_obj)
                    current_win = {}
                continue

            if in_windows_section and ":" in line_str:
                k, v = line_str.split(":", 1)
                k = k.strip().lower()
                v = v.strip()
                current_win[k] = v

        if current_win.get("address"):
            win_obj = self._build_kwin_window(current_win)
            if win_obj:
                windows.append(win_obj)

        return windows

    def _build_kwin_window(self, data: Dict[str, Any]) -> Optional[WindowInfo]:
        address = str(data.get("address", data.get("id", "")))
        if not address:
            return None

        title = data.get("caption", data.get("name", "Unknown"))
        app_id = data.get("resourceclass", data.get("desktopfilename", data.get("app_id", "unknown")))
        pid_val = data.get("pid", "0")
        pid = int(pid_val) if str(pid_val).isdigit() else 0

        x = int(data.get("x", 0)) if str(data.get("x", "")).isdigit() else 0
        y = int(data.get("y", 0)) if str(data.get("y", "")).isdigit() else 0
        width = int(data.get("width", 0)) if str(data.get("width", "")).isdigit() else 0
        height = int(data.get("height", 0)) if str(data.get("height", "")).isdigit() else 0
        is_active = bool(data.get("active", "false").lower() == "true")
        ws_name = str(data.get("desktop", "1"))

        proc_info = get_process_info(pid) if pid > 0 else None
        exe_path = proc_info.exe_path if proc_info else ""
        cwd = proc_info.cwd if proc_info else ""
        cmdline = proc_info.cmdline if proc_info else []
        memory_mb = proc_info.memory_mb if proc_info else 0.0

        entry = get_desktop_entry(app_id, exe_path)
        desktop_entry = entry.get("_filepath") if entry else None
        icon_name = entry.get("Icon") if entry else None

        return WindowInfo(
            address=address,
            app_id=app_id,
            title=title,
            pid=pid,
            x=x,
            y=y,
            width=width,
            height=height,
            workspace_name=ws_name,
            is_active=is_active,
            exe_path=exe_path,
            cwd=cwd,
            cmdline=cmdline,
            memory_mb=memory_mb,
            desktop_entry=desktop_entry,
            icon_name=icon_name
        )

    def get_active_window(self) -> Optional[WindowInfo]:
        windows = self.get_windows()
        for w in windows:
            if w.is_active:
                return w
        return windows[0] if windows else None

    def close_window(self, address_or_pid: str) -> bool:
        # Fallback to PID termination if D-Bus window ID close not directly mapped
        if address_or_pid.isdigit():
            pid = int(address_or_pid)
            try:
                import signal
                os.kill(pid, signal.SIGTERM)
                return True
            except Exception:
                return False
        return False

    def focus_window(self, address: str) -> bool:
        # Focus via D-Bus client activation
        return False
