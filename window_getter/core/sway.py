"""
Sway / i3 compositor backend for window-getter using swaymsg JSON API with clean host environment.
"""

import json
import subprocess
from typing import List, Optional, Dict, Any
from window_getter.core.models import WindowInfo
from window_getter.core.proc import get_process_info
from window_getter.core.launcher import get_desktop_entry
from window_getter.core.compat import get_clean_env


class SwayBackend:
    @staticmethod
    def is_available() -> bool:
        try:
            res = subprocess.run(
                ["swaymsg", "-t", "get_tree"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                env=get_clean_env()
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_windows(self) -> List[WindowInfo]:
        try:
            res = subprocess.run(
                ["swaymsg", "-t", "get_tree"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                check=True,
                env=get_clean_env()
            )
            tree = json.loads(res.stdout)
            windows: List[WindowInfo] = []
            self._walk_node(tree, windows, current_workspace="1")
            return windows
        except Exception as e:
            print(f"[SwayBackend] Error getting windows: {e}")
            return []

    def get_active_window(self) -> Optional[WindowInfo]:
        windows = self.get_windows()
        for w in windows:
            if w.is_active:
                return w
        return windows[0] if windows else None

    def close_window(self, address_or_pid: str) -> bool:
        try:
            cmd = ["swaymsg", f"[id={address_or_pid}] kill"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=get_clean_env())
            return res.returncode == 0
        except Exception:
            return False

    def focus_window(self, address_or_pid: str) -> bool:
        try:
            cmd = ["swaymsg", f"[id={address_or_pid}] focus"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=get_clean_env())
            return res.returncode == 0
        except Exception:
            return False

    def move_to_workspace(self, address_or_pid: str, workspace: str) -> bool:
        try:
            cmd = ["swaymsg", f"[id={address_or_pid}] move container to workspace {workspace}"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=get_clean_env())
            return res.returncode == 0
        except Exception:
            return False

    def _walk_node(self, node: Dict[str, Any], windows: List[WindowInfo], current_workspace: str):
        node_type = node.get("type", "")
        if node_type == "workspace":
            current_workspace = node.get("name", current_workspace)

        # Check if node is a window container (has pid or app_id or window_properties)
        if node.get("pid") or node.get("app_id") or node.get("window_properties"):
            pid = node.get("pid", 0)
            app_id = node.get("app_id") or node.get("window_properties", {}).get("class", "")
            title = node.get("name", "")
            rect = node.get("rect", {})
            x = rect.get("x", 0)
            y = rect.get("y", 0)
            width = rect.get("width", 0)
            height = rect.get("height", 0)

            node_id = str(node.get("id", ""))
            is_active = bool(node.get("focused", False))
            is_floating = "floating" in node.get("type", "")

            proc_info = get_process_info(pid) if pid > 0 else None
            exe_path = proc_info.exe_path if proc_info else ""
            cwd = proc_info.cwd if proc_info else ""
            cmdline = proc_info.cmdline if proc_info else []
            memory_mb = proc_info.memory_mb if proc_info else 0.0

            entry = get_desktop_entry(app_id, exe_path)
            desktop_entry = entry.get("_filepath") if entry else None
            icon_name = entry.get("Icon") if entry else None

            windows.append(WindowInfo(
                address=node_id,
                app_id=app_id,
                title=title,
                pid=pid,
                x=x,
                y=y,
                width=width,
                height=height,
                workspace_name=current_workspace,
                is_active=is_active,
                is_floating=is_floating,
                exe_path=exe_path,
                cwd=cwd,
                cmdline=cmdline,
                memory_mb=memory_mb,
                desktop_entry=desktop_entry,
                icon_name=icon_name
            ))

        for child in node.get("nodes", []):
            self._walk_node(child, windows, current_workspace)
        for child in node.get("floating_nodes", []):
            self._walk_node(child, windows, current_workspace)
