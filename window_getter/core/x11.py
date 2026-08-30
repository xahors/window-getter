"""
X11 backend for window-getter using xdotool / xprop with clean host environment.
"""

import subprocess
import re
from typing import List, Optional
from window_getter.core.models import WindowInfo
from window_getter.core.proc import get_process_info
from window_getter.core.launcher import get_desktop_entry
from window_getter.core.compat import get_clean_env


class X11Backend:
    @staticmethod
    def is_available() -> bool:
        try:
            res = subprocess.run(
                ["xdotool", "getactivewindow"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_active_window(self) -> Optional[WindowInfo]:
        try:
            res = subprocess.run(
                ["xdotool", "getactivewindow"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                check=True,
                env=get_clean_env()
            )
            win_id = res.stdout.strip()
            if not win_id:
                return None
            return self._parse_x11_window(win_id, is_active=True)
        except Exception:
            return None

    def get_windows(self) -> List[WindowInfo]:
        try:
            res = subprocess.run(
                ["xdotool", "search", "--onlyvisible", "--class", ".*"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                env=get_clean_env()
            )
            win_ids = [w.strip() for w in res.stdout.splitlines() if w.strip()]
            active_win = self.get_active_window()
            active_id = active_win.address if active_win else ""

            windows: List[WindowInfo] = []
            for wid in win_ids:
                win = self._parse_x11_window(wid, is_active=(wid == active_id))
                if win:
                    windows.append(win)
            return windows
        except Exception as e:
            print(f"[X11Backend] Error getting windows: {e}")
            return []

    def close_window(self, win_id: str) -> bool:
        try:
            res = subprocess.run(["xdotool", "windowclose", win_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=get_clean_env())
            return res.returncode == 0
        except Exception:
            return False

    def focus_window(self, win_id: str) -> bool:
        try:
            res = subprocess.run(["xdotool", "windowactivate", win_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=get_clean_env())
            return res.returncode == 0
        except Exception:
            return False

    def _parse_x11_window(self, win_id: str, is_active: bool = False) -> Optional[WindowInfo]:
        try:
            # Fetch window geometry
            geo_res = subprocess.run(
                ["xdotool", "getwindowgeometry", "--shell", win_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            geo = {}
            for line in geo_res.stdout.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    geo[k.strip()] = v.strip()

            x = int(geo.get("X", 0))
            y = int(geo.get("Y", 0))
            width = int(geo.get("WIDTH", 0))
            height = int(geo.get("HEIGHT", 0))

            # Fetch PID
            pid_res = subprocess.run(
                ["xdotool", "getwindowpid", win_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            pid = int(pid_res.stdout.strip()) if pid_res.stdout.strip().isdigit() else 0

            # Fetch Title
            title_res = subprocess.run(
                ["xdotool", "getwindowname", win_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            title = title_res.stdout.strip()

            # Fetch WM_CLASS via xprop
            app_id = "unknown"
            xprop_res = subprocess.run(
                ["xprop", "-id", win_id, "WM_CLASS"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            if '="' in xprop_res.stdout:
                matches = re.findall(r'"([^"]*)"', xprop_res.stdout)
                if matches:
                    app_id = matches[-1]

            proc_info = get_process_info(pid) if pid > 0 else None
            exe_path = proc_info.exe_path if proc_info else ""
            cwd = proc_info.cwd if proc_info else ""
            cmdline = proc_info.cmdline if proc_info else []
            memory_mb = proc_info.memory_mb if proc_info else 0.0

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
                is_active=is_active,
                exe_path=exe_path,
                cwd=cwd,
                cmdline=cmdline,
                memory_mb=memory_mb,
                desktop_entry=desktop_entry,
                icon_name=icon_name
            )
        except Exception:
            return None
