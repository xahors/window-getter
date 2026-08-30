"""
Application launcher and desktop file resolver module for window-getter.
"""

import os
import glob
import shlex
import subprocess
import shutil
import re
from typing import Dict, List, Optional, Tuple


class DesktopResolver:
    def __init__(self):
        self.desktop_dirs = [
            os.path.expanduser("~/.local/share/applications"),
            "/usr/share/applications",
            "/var/lib/flatpak/exports/share/applications",
            "/usr/local/share/applications",
        ]
        self._cache: Dict[str, Dict[str, str]] = {}
        self._scanned = False

    def scan(self, force: bool = False):
        if self._scanned and not force:
            return

        self._cache.clear()
        for d in self.desktop_dirs:
            if not os.path.exists(d):
                continue
            for filepath in glob.glob(os.path.join(d, "*.desktop")):
                filename = os.path.basename(filepath)
                entry_data = self._parse_desktop_file(filepath)
                if entry_data:
                    key = filename.lower().replace(".desktop", "")
                    if key not in self._cache:
                        self._cache[key] = entry_data

                    wm_class = entry_data.get("StartupWMClass", "").lower()
                    if wm_class and wm_class not in self._cache:
                        self._cache[wm_class] = entry_data

        self._scanned = True

    def _parse_desktop_file(self, filepath: str) -> Optional[Dict[str, str]]:
        try:
            data = {}
            in_main_section = False
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line == "[Desktop Entry]":
                        in_main_section = True
                        continue
                    elif line.startswith("[") and line.endswith("]"):
                        in_main_section = False
                        continue

                    if in_main_section and "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        data[k.strip()] = v.strip()
            data["_filepath"] = filepath
            return data
        except Exception:
            return None

    def find_entry(self, app_id: str, exe_path: str = "") -> Optional[Dict[str, str]]:
        self.scan()
        if not app_id:
            app_id = ""

        clean_app = app_id.lower().strip()
        if clean_app in self._cache:
            return self._cache[clean_app]

        # Try matching base class name (e.g., org.gnome.Nautilus -> nautilus)
        if "." in clean_app:
            short_name = clean_app.split(".")[-1]
            if short_name in self._cache:
                return self._cache[short_name]

        # Try matching by exe_path basename
        if exe_path:
            exe_base = os.path.basename(exe_path).lower()
            if exe_base in self._cache:
                return self._cache[exe_base]

        return None


# Global resolver singleton
_resolver = DesktopResolver()


def get_desktop_entry(app_id: str, exe_path: str = "") -> Optional[Dict[str, str]]:
    return _resolver.find_entry(app_id, exe_path)


def clean_exec_command(exec_str: str) -> str:
    """Strip desktop field codes like %u, %F, %U, %f, %k, %c, %i, %d, %D, %n, %N, %v, %m."""
    if not exec_str:
        return ""
    cleaned = re.sub(r"%[fFuUiIkKcCnNvmDd]", "", exec_str).strip()
    return cleaned


def _execute_cmd(cmd, cwd: Optional[str] = None):
    """Execute command as a detached background process."""
    valid_cwd = cwd if (cwd and os.path.exists(cwd)) else None

    if isinstance(cmd, list):
        subprocess.Popen(cmd, cwd=valid_cwd, start_new_session=True)
    elif isinstance(cmd, str):
        try:
            args = shlex.split(cmd)
            if args:
                subprocess.Popen(args, cwd=valid_cwd, start_new_session=True)
            else:
                subprocess.Popen(cmd, shell=True, cwd=valid_cwd, start_new_session=True)
        except Exception:
            subprocess.Popen(cmd, shell=True, cwd=valid_cwd, start_new_session=True)


def get_default_relaunch_command(
    app_id: str = "",
    exe_path: str = "",
    cmdline: List[str] = None
) -> str:
    """Determine the most reliable default shell command to relaunch a window."""
    # 1. Check desktop entry (highest fidelity for standard desktop applications)
    entry = get_desktop_entry(app_id, exe_path)
    if entry and entry.get("Exec"):
        cleaned = clean_exec_command(entry["Exec"])
        if cleaned:
            return cleaned

    # 2. Check cmdline
    if cmdline and len(cmdline) > 0 and cmdline[0]:
        return " ".join(cmdline)

    # 3. Fallback to executable path
    if exe_path and os.path.exists(exe_path):
        return exe_path

    # 4. Fallback to app_id
    if app_id:
        return app_id

    return ""


def relaunch_window(
    cmdline: List[str] = None,
    exe_path: str = "",
    app_id: str = "",
    cwd: str = "",
    custom_command: str = ""
) -> Tuple[bool, str]:
    """
    Relaunches an application using custom command, desktop entry, cmdline, or exe_path.
    Returns (success: bool, message: str).
    """
    try:
        # 1. Custom Command provided by user
        if custom_command and custom_command.strip():
            cmd = custom_command.strip()
            _execute_cmd(cmd, cwd=cwd)
            return True, f"Launched command: {cmd}"

        # 2. Desktop Entry Exec command
        entry = get_desktop_entry(app_id, exe_path)
        if entry and entry.get("Exec"):
            cleaned = clean_exec_command(entry["Exec"])
            if cleaned:
                _execute_cmd(cleaned, cwd=cwd)
                return True, f"Relaunched via desktop entry: {cleaned}"

        # 3. Cmdline list from /proc/<pid>/cmdline
        if cmdline and len(cmdline) > 0 and cmdline[0]:
            _execute_cmd(cmdline, cwd=cwd)
            return True, f"Relaunched via cmdline: {' '.join(cmdline)}"

        # 4. Fallback to exe_path
        if exe_path and os.path.exists(exe_path):
            _execute_cmd(exe_path, cwd=cwd)
            return True, f"Relaunched via executable: {exe_path}"

        # 5. Fallback to app_id
        if app_id:
            _execute_cmd(app_id, cwd=cwd)
            return True, f"Relaunched via App ID: {app_id}"

        return False, "Could not determine valid command to relaunch window."

    except Exception as e:
        return False, f"Failed to relaunch application: {str(e)}"


def launch_new_command(command_str: str, cwd: str = "") -> Tuple[bool, str]:
    """Launch any new shell command as a background process."""
    try:
        if not command_str or not command_str.strip():
            return False, "Command cannot be empty."

        _execute_cmd(command_str.strip(), cwd=cwd)
        return True, f"Successfully started: {command_str}"
    except Exception as e:
        return False, f"Error launching command: {str(e)}"
