"""
Universal EWMH / X11 backend for window-getter supporting XFCE, MATE, Cinnamon, Openbox, bspwm, AwesomeWM, dwm, and standard X11 WMs.
"""

import os
import subprocess
import re
import shutil
from typing import List, Optional, Dict
from window_getter.core.models import WindowInfo
from window_getter.core.proc import get_process_info
from window_getter.core.launcher import get_desktop_entry
from window_getter.core.compat import get_clean_env


class X11Backend:
    @staticmethod
    def is_available() -> bool:
        """Check if X11 session with EWMH/xdotool/wmctrl/xprop is active."""
        if not os.environ.get("DISPLAY"):
            return False

        # 1. Check wmctrl
        if shutil.which("wmctrl"):
            try:
                res = subprocess.run(["wmctrl", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2, env=get_clean_env())
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        # 2. Check xdotool
        if shutil.which("xdotool"):
            try:
                res = subprocess.run(["xdotool", "getactivewindow"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2, env=get_clean_env())
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        # 3. Check xprop
        if shutil.which("xprop"):
            try:
                res = subprocess.run(["xprop", "-root", "_NET_CLIENT_LIST"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2, env=get_clean_env())
                if res.returncode == 0 and "window id" in res.stdout.lower():
                    return True
            except Exception:
                pass

        return False

    def get_active_window_id(self) -> str:
        """Get the active window ID in hex format."""
        # 1. Try xprop _NET_ACTIVE_WINDOW
        try:
            res = subprocess.run(["xprop", "-root", "_NET_ACTIVE_WINDOW"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2, env=get_clean_env())
            if res.returncode == 0 and "#" in res.stdout:
                wid_hex = res.stdout.split("#", 1)[1].strip().split()[0]
                if wid_hex and wid_hex != "0x0":
                    return wid_hex.lower()
        except Exception:
            pass

        # 2. Try xdotool getactivewindow
        try:
            res = subprocess.run(["xdotool", "getactivewindow"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2, env=get_clean_env())
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return hex(int(res.stdout.strip())).lower()
        except Exception:
            pass

        return ""

    def get_windows(self) -> List[WindowInfo]:
        """Fetch all managed EWMH / X11 windows."""
        # 1. Try wmctrl (fastest and most complete in a single execution)
        if shutil.which("wmctrl"):
            wins = self._get_windows_wmctrl()
            if wins:
                return wins

        # 2. Fallback to xprop / xdotool
        return self._get_windows_xprop_xdotool()

    def _get_windows_wmctrl(self) -> List[WindowInfo]:
        """Query windows via `wmctrl -l -p -G -x`."""
        try:
            res = subprocess.run(
                ["wmctrl", "-l", "-p", "-G", "-x"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                env=get_clean_env()
            )
            if res.returncode != 0:
                return []

            active_id = self.get_active_window_id()
            windows: List[WindowInfo] = []

            for line in res.stdout.splitlines():
                parts = line.strip().split(None, 8)
                if len(parts) < 8:
                    continue

                wid = parts[0].lower()
                desktop_id = parts[1]
                pid = int(parts[2]) if parts[2].isdigit() else 0
                x = int(parts[3]) if parts[3].isdigit() or (parts[3].startswith("-") and parts[3][1:].isdigit()) else 0
                y = int(parts[4]) if parts[4].isdigit() or (parts[4].startswith("-") and parts[4][1:].isdigit()) else 0
                width = int(parts[5]) if parts[5].isdigit() else 0
                height = int(parts[6]) if parts[6].isdigit() else 0
                wm_class_full = parts[7]
                title = parts[8] if len(parts) > 8 else ""

                # Extract app_id from wm_class (e.g. firefox.Navigator -> firefox)
                app_id = wm_class_full.split(".")[0] if "." in wm_class_full else wm_class_full

                is_active = (wid == active_id) or (int(wid, 16) == int(active_id, 16) if active_id.startswith("0x") else False)

                ws_name = f"Workspace {int(desktop_id) + 1}" if desktop_id.isdigit() and int(desktop_id) >= 0 else "Sticky"

                proc_info = get_process_info(pid) if pid > 0 else None
                exe_path = proc_info.exe_path if proc_info else ""
                cwd = proc_info.cwd if proc_info else ""
                cmdline = proc_info.cmdline if proc_info else []
                memory_mb = proc_info.memory_mb if proc_info else 0.0
                cpu_percent = proc_info.cpu_percent if proc_info else 0.0

                entry = get_desktop_entry(app_id, exe_path)
                desktop_entry = entry.get("_filepath") if entry else None
                icon_name = entry.get("Icon") if entry else None

                windows.append(WindowInfo(
                    address=wid,
                    app_id=app_id,
                    title=title,
                    pid=pid,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    workspace_id=int(desktop_id) + 1 if desktop_id.isdigit() and int(desktop_id) >= 0 else 1,
                    workspace_name=ws_name,
                    is_active=is_active,
                    exe_path=exe_path,
                    cwd=cwd,
                    cmdline=cmdline,
                    memory_mb=memory_mb,
                    cpu_percent=cpu_percent,
                    desktop_entry=desktop_entry,
                    icon_name=icon_name
                ))

            return windows
        except Exception as e:
            return []

    def _get_windows_xprop_xdotool(self) -> List[WindowInfo]:
        """Fallback querying via xdotool and xprop."""
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
            active_id = self.get_active_window_id()

            windows: List[WindowInfo] = []
            for wid in win_ids:
                win = self._parse_x11_window(wid, active_id)
                if win:
                    windows.append(win)
            return windows
        except Exception:
            return []

    def get_active_window(self) -> Optional[WindowInfo]:
        windows = self.get_windows()
        for w in windows:
            if w.is_active:
                return w
        return windows[0] if windows else None

    def close_window(self, win_id: str) -> bool:
        """Close window via wmctrl or xdotool."""
        if shutil.which("wmctrl"):
            try:
                res = subprocess.run(["wmctrl", "-i", "-c", win_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=get_clean_env())
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        try:
            res = subprocess.run(["xdotool", "windowclose", win_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=get_clean_env())
            return res.returncode == 0
        except Exception:
            return False

    def focus_window(self, win_id: str) -> bool:
        """Focus window via wmctrl or xdotool."""
        if shutil.which("wmctrl"):
            try:
                res = subprocess.run(["wmctrl", "-i", "-a", win_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=get_clean_env())
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        try:
            res = subprocess.run(["xdotool", "windowactivate", win_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=get_clean_env())
            return res.returncode == 0
        except Exception:
            return False

    def move_to_workspace(self, win_id: str, workspace_idx: str) -> bool:
        """Move window to workspace index (0-indexed) via wmctrl."""
        if shutil.which("wmctrl"):
            try:
                ws_num = int(workspace_idx) - 1 if workspace_idx.isdigit() and int(workspace_idx) > 0 else 0
                res = subprocess.run(["wmctrl", "-i", "-r", win_id, "-t", str(ws_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=get_clean_env())
                return res.returncode == 0
            except Exception:
                pass
        return False

    def _parse_x11_window(self, win_id: str, active_id: str = "") -> Optional[WindowInfo]:
        try:
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

            pid_res = subprocess.run(
                ["xdotool", "getwindowpid", win_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            pid = int(pid_res.stdout.strip()) if pid_res.stdout.strip().isdigit() else 0

            title_res = subprocess.run(
                ["xdotool", "getwindowname", win_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            title = title_res.stdout.strip()

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

            wid_hex = hex(int(win_id)).lower() if win_id.isdigit() else win_id.lower()
            is_active = (wid_hex == active_id.lower())

            proc_info = get_process_info(pid) if pid > 0 else None
            exe_path = proc_info.exe_path if proc_info else ""
            cwd = proc_info.cwd if proc_info else ""
            cmdline = proc_info.cmdline if proc_info else []
            memory_mb = proc_info.memory_mb if proc_info else 0.0

            entry = get_desktop_entry(app_id, exe_path)
            desktop_entry = entry.get("_filepath") if entry else None
            icon_name = entry.get("Icon") if entry else None

            return WindowInfo(
                address=wid_hex,
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
