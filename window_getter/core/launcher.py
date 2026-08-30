"""
Application launcher and desktop file resolver module with workspace dispatch support.
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
    """Strip desktop field codes like %u, %F, %U, %f, %k, %c, %i."""
    if not exec_str:
        return ""
    cleaned = re.sub(r"%[fFuUiIkKcCnNvm]", "", exec_str).strip()
    return cleaned


def _execute_cmd(cmd, target_workspace: str = "", cwd: str = None):
    """Execute command with optional workspace dispatching."""
    valid_cwd = cwd if (cwd and os.path.exists(cwd)) else None
    cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)

    # Hyprland Workspace Dispatcher
    if target_workspace and shutil.which("hyprctl"):
        hypr_cmd = f"hyprctl dispatch exec [workspace {target_workspace}] -- {cmd_str}"
        subprocess.Popen(hypr_cmd, shell=True, cwd=valid_cwd, start_new_session=True)
        return
    # Sway Workspace Dispatcher
    elif target_workspace and shutil.which("swaymsg"):
        sway_cmd = f"swaymsg 'exec [workspace {target_workspace}] {cmd_str}'"
        subprocess.Popen(sway_cmd, shell=True, cwd=valid_cwd, start_new_session=True)
        return

    # Standard Fallback Dispatcher
    if isinstance(cmd, list) and not target_workspace:
        subprocess.Popen(cmd, cwd=valid_cwd, start_new_session=True)
    else:
        subprocess.Popen(cmd_str, shell=True, cwd=valid_cwd, start_new_session=True)


def relaunch_window(
    cmdline: List[str] = None,
    exe_path: str = "",
    app_id: str = "",
    cwd: str = "",
    custom_command: str = "",
    target_workspace: str = ""
) -> Tuple[bool, str]:
    """
    Relaunches an application using custom command, cmdline, desktop file exec, or exe_path,
    targeting the specified workspace.
    Returns (success: bool, message: str).
    """
    try:
        ws_info = f" on workspace '{target_workspace}'" if target_workspace else ""

        # 1. Custom Command provided by user
        if custom_command and custom_command.strip():
            cmd = custom_command.strip()
            _execute_cmd(cmd, target_workspace=target_workspace, cwd=cwd)
            return True, f"Launched custom command{ws_info}: {cmd}"

        # 2. Cmdline list from /proc/<pid>/cmdline
        if cmdline and len(cmdline) > 0 and cmdline[0]:
            _execute_cmd(cmdline, target_workspace=target_workspace, cwd=cwd)
            return True, f"Relaunched via cmdline{ws_info}: {' '.join(cmdline)}"

        # 3. Desktop Entry Exec command
        entry = get_desktop_entry(app_id, exe_path)
        if entry and entry.get("Exec"):
            raw_exec = entry["Exec"]
            cleaned = clean_exec_command(raw_exec)
            if cleaned:
                _execute_cmd(cleaned, target_workspace=target_workspace, cwd=cwd)
                return True, f"Relaunched via desktop entry{ws_info}: {cleaned}"

        # 4. Fallback to exe_path
        if exe_path and os.path.exists(exe_path):
            _execute_cmd(exe_path, target_workspace=target_workspace, cwd=cwd)
            return True, f"Relaunched via executable{ws_info}: {exe_path}"

        return False, "Could not determine valid command to relaunch window."

    except Exception as e:
        return False, f"Failed to relaunch application: {str(e)}"


def launch_new_command(command_str: str, cwd: str = "", target_workspace: str = "") -> Tuple[bool, str]:
    """Launch any new shell command as a background process."""
    try:
        if not command_str or not command_str.strip():
            return False, "Command cannot be empty."

        _execute_cmd(command_str.strip(), target_workspace=target_workspace, cwd=cwd)
        return True, f"Successfully started: {command_str}"
    except Exception as e:
        return False, f"Error launching command: {str(e)}"
