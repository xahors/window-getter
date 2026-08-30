"""
Data models for Window, Process, Workspace, and System details.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class ProcessInfo:
    pid: int
    name: str = ""
    ppid: int = 0
    parent_name: str = ""
    exe_path: str = ""
    cwd: str = ""
    cmdline: List[str] = field(default_factory=list)
    memory_mb: float = 0.0                  # RSS Memory usage in Megabytes
    vm_size_mb: float = 0.0                 # Total Virtual Memory size in MB
    vm_peak_mb: float = 0.0                 # Peak Virtual Memory size in MB
    vm_swap_mb: float = 0.0                 # Swap space usage in MB
    cpu_percent: float = 0.0
    threads: int = 1
    user: str = ""
    status: str = "running"
    open_fds: int = 0
    start_time_str: str = ""
    uptime_str: str = ""
    read_bytes_mb: float = 0.0
    write_bytes_mb: float = 0.0
    voluntary_ctxt_switches: int = 0
    nonvoluntary_ctxt_switches: int = 0
    cgroup: str = ""
    environ: Dict[str, str] = field(default_factory=dict)
    fd_details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WindowInfo:
    address: str                             # Hyprland address or X11 window ID
    app_id: str                              # Class name / App ID (e.g. kitty, steam, org.gnome.Nautilus)
    title: str                              # Current window title
    pid: int                                # Process ID
    x: int = 0                              # Top-left X coordinate
    y: int = 0                              # Top-left Y coordinate
    width: int = 0                          # Window width
    height: int = 0                         # Window height
    workspace_id: int = 1                   # Workspace numerical ID
    workspace_name: str = "1"               # Workspace display name
    monitor_id: int = 0                     # Monitor numerical ID or name
    is_active: bool = False                 # Is this the currently selected/focused window?
    is_visible: bool = True                 # Is the window currently visible?
    is_mapped: bool = True                  # Is the window mapped in compositor?
    is_floating: bool = False               # Floating vs tiled mode
    is_fullscreen: bool = False             # Fullscreen status
    is_xwayland: bool = False               # XWayland vs native Wayland
    initial_class: str = ""                 # Initial class if changed dynamically
    initial_title: str = ""                 # Initial title
    focus_history_id: int = 0              # Focus history ordering index
    
    # Extended Process Info
    exe_path: str = ""                      # Executable path from /proc/<pid>/exe
    cwd: str = ""                           # Working directory from /proc/<pid>/cwd
    cmdline: List[str] = field(default_factory=list) # Full startup command line
    memory_mb: float = 0.0                  # RSS Memory usage in Megabytes
    cpu_percent: float = 0.0                # CPU usage percentage
    desktop_entry: Optional[str] = None     # Matched .desktop file path
    icon_name: Optional[str] = None         # Resolved app icon name

    @property
    def geometry_str(self) -> str:
        return f"{self.width}x{self.height} @ ({self.x},{self.y})"

    @property
    def display_app_id(self) -> str:
        return self.app_id if self.app_id else (self.initial_class if self.initial_class else "Unknown")

    @property
    def display_title(self) -> str:
        return self.title if self.title else (self.initial_title if self.initial_title else "Untitled Window")

    def generate_hyprland_rule(self, rule_type: str = "float") -> str:
        app = self.display_app_id
        pattern = f"^({app})$" if app else ".*"
        if rule_type == "float":
            return f"windowrulev2 = float, class:{pattern}"
        elif rule_type == "workspace":
            return f"windowrulev2 = workspace {self.workspace_name}, class:{pattern}"
        elif rule_type == "size":
            return f"windowrulev2 = size {self.width} {self.height}, class:{pattern}"
        elif rule_type == "position":
            return f"windowrulev2 = move {self.x} {self.y}, class:{pattern}"
        return f"windowrulev2 = float, class:{pattern}"

    def generate_sway_rule(self, rule_type: str = "float") -> str:
        app = self.display_app_id
        if rule_type == "float":
            return f'for_window [app_id="{app}"] floating enable'
        elif rule_type == "workspace":
            return f'for_window [app_id="{app}"] move container to workspace {self.workspace_name}'
        elif rule_type == "size":
            return f'for_window [app_id="{app}"] resize set {self.width} px {self.height} px'
        return f'for_window [app_id="{app}"] floating enable'

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["geometry_str"] = self.geometry_str
        d["display_app_id"] = self.display_app_id
        d["display_title"] = self.display_title
        return d


@dataclass
class WorkspaceInfo:
    id: int
    name: str
    monitor: str = ""
    active_window_address: str = ""
    windows_count: int = 0
    is_active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
