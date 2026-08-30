# window-getter

window-getter is a Linux desktop utility and command-line tool for inspecting active graphical windows, managing process lifecycles (closing, terminating, relaunching), and generating compositor window rules for Hyprland and Sway.

---

## Features

- **Window Detection and Metadata**:
  - Window class, App ID, title, and initial class.
  - Process ID (PID), parent PID, and process tree information.
  - Geometry (width, height, and screen coordinates).
  - Workspace assignment and display name.
  - Window state flags (focus, floating mode, fullscreen, mapped status, XWayland flag).
  - Process resource metrics (resident set size memory, CPU utilization, executable path, current working directory, and command-line arguments).
- **Process and Lifecycle Management**:
  - Graceful window closing through compositor IPC or window manager dispatchers.
  - Process termination via `SIGKILL` or `SIGTERM`.
  - Application relaunching with automatic command-line reconstruction from `/proc/<pid>/cmdline`, executable binary resolution, or `.desktop` entry matching.
  - Window focus switching and workspace relocation.
- **Compositor Backends**:
  - **Hyprland**: Native `hyprctl` JSON IPC for querying windows, workspaces, and dispatching actions.
  - **Sway / i3**: Native `swaymsg` tree and workspace query API.
  - **X11 / Generic**: Fallback using `xdotool`, `xprop`, and `wmctrl`.
- **User Interfaces**:
  - **PyQt6 Desktop GUI**: Graphical dashboard featuring active window inspection, a searchable window table, and an interactive 2D spatial workspace map.
  - **CLI Interface**: Subcommands for automated scripts, terminal inspection, and window management.
  - **Web Dashboard and REST API**: Lightweight HTTP server providing a browser dashboard and JSON API endpoints.
- **Compositor Rule Generator**:
  - Generates configuration rules for Hyprland (`windowrulev2` and Hyprland Lua syntax) and Sway (`for_window`).

---

## Installation

### Prerequisites

- Python 3.9 or higher
- One of the supported window environments:
  - Hyprland (`hyprctl`)
  - Sway / i3 (`swaymsg`)
  - X11 with `xdotool`, `xprop`, and `wmctrl` installed
- For the desktop GUI: Qt6 runtime libraries (e.g. `libxcb`, `libxkbcommon`)

### Installation from Source

```bash
# Clone the repository
git clone https://github.com/durkluf/window-getter.git
cd window-getter

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package in editable mode
pip install -e .
```

---

## Usage

### Desktop Graphical Interface

Launch the PyQt6 desktop interface:

```bash
window-getter
# or explicitly:
window-getter gui
```

The GUI provides four main views:
1. **Active Window**: Details of the currently focused window with process metrics, geometry, and action controls.
2. **Windows Table**: Filterable and searchable table of all open windows across all workspaces.
3. **Workspace Map**: 2D canvas displaying monitor boundaries and window positions.
4. **Rule Generator**: Configurable dialog to generate and copy compositor rule blocks.

---

### Command-Line Interface (CLI)

The CLI provides subcommands for automation, terminal queries, and window operations:

| Command | Description |
| :--- | :--- |
| `window-getter` | Launches the PyQt6 desktop GUI (default behavior when no subcommand is specified). |
| `window-getter gui` | Explicitly launches the PyQt6 desktop GUI. |
| `window-getter active` | Prints details of the currently focused window. |
| `window-getter active --json` | Outputs JSON object representing the active window. |
| `window-getter active --rule` | Generates a compositor rule snippet for the active window. |
| `window-getter active --pid` | Prints the PID of the active window. |
| `window-getter active --app-id` | Prints the App ID / Class of the active window. |
| `window-getter active --title` | Prints the title of the active window. |
| `window-getter active --size` | Prints the width and height of the active window. |
| `window-getter list` | Displays a formatted table of all open windows. |
| `window-getter list --json` | Outputs an array of JSON objects for all open windows. |
| `window-getter list --workspace <name/id>` | Filters window listing by workspace. |
| `window-getter list --class <string>` | Filters window listing by application class/App ID. |
| `window-getter get <query>` | Looks up a window by title, App ID, PID, or address. |
| `window-getter get <query> --json` | Outputs JSON for a matching window. |
| `window-getter close <query>` | Sends a graceful close request to the matching window. |
| `window-getter kill <target>` | Terminates a process by PID or window query with `SIGKILL`. |
| `window-getter relaunch <query>` | Relaunches an application associated with a window. |
| `window-getter relaunch <query> --command "<cmd>"` | Relaunches with a customized command string. |
| `window-getter focus <query>` | Focuses the matching window. |
| `window-getter rule <query>` | Generates a rule configuration block (`--target hyprland_lua`, `hyprland_conf`, or `sway`). |
| `window-getter web` | Starts the embedded web dashboard and REST API server. |
| `window-getter web --host <ip> --port <port>` | Configures the host interface and port (default: `127.0.0.1:8080`). |

---

### Web Server and REST API

`window-getter` includes a built-in HTTP server using Python's standard library `http.server`:

```bash
window-getter web --host 127.0.0.1 --port 8080
```

#### API Endpoints

- `GET /`: Serves the web dashboard interface.
- `GET /api/status`: Returns server status, active backend, and window count.
- `GET /api/active`: Returns JSON metadata for the currently active window.
- `GET /api/windows`: Returns JSON list of all open windows.
- `GET /api/workspaces`: Returns list of detected workspaces.
- `POST /api/close`: Closes a window (`{"query": "<target>"}`).
- `POST /api/kill`: Terminates a process (`{"pid": <int>}` or `{"query": "<target>"}`).
- `POST /api/relaunch`: Relaunches an application (`{"query": "<target>", "command": "<cmd>"}`).
- `POST /api/focus`: Focuses a target window (`{"query": "<target>"}`).
- `POST /api/rule`: Generates rule configuration (`{"query": "<target>", "target": "<backend>"}`).

---

## Project Architecture

```
window-getter/
├── pyproject.toml              # Project metadata, dependencies, and entrypoints
├── setup.py                    # Build configuration
├── window_getter/
│   ├── __init__.py             # Package version and export definitions
│   ├── cli.py                  # CLI argument parsing and command dispatchers
│   ├── core/                   # Core business logic and backend implementations
│   │   ├── __init__.py
│   │   ├── models.py           # WindowInfo, ProcessInfo, and WorkspaceInfo dataclasses
│   │   ├── detector.py         # WindowDetector base class and backend auto-discovery
│   │   ├── hyprland.py         # Hyprland IPC backend (hyprctl)
│   │   ├── sway.py             # Sway/i3 IPC backend (swaymsg)
│   │   ├── x11.py              # X11 fallback backend (xdotool, xprop, wmctrl)
│   │   ├── proc.py             # Linux /proc filesystem reader and process statistics
│   │   ├── launcher.py         # Application relauncher and .desktop resolver
│   │   └── rules.py            # Compositor rule generation logic
│   ├── gui/                    # PyQt6 desktop application
│   │   ├── __init__.py
│   │   ├── app.py              # Qt application lifecycle and entrypoint
│   │   ├── main_window.py      # Main window controller, timer loops, and tab orchestration
│   │   ├── theme.py            # Dark theme stylesheets and styling definitions
│   │   └── components/
│   │       ├── active_card.py  # Active window hero card and metrics display
│   │       ├── window_table.py # Searchable and sortable window table widget
│   │       ├── workspace_map.py# 2D visual monitor and window layout canvas
│   │       ├── process_dialog.py # Process details inspection modal
│   │       ├── relaunch_dialog.py# Application relaunch configuration modal
│   │       └── rule_dialog.py  # Window rule generator modal
│   └── web/                    # Embedded web dashboard and REST server
│       ├── __init__.py
│       ├── server.py           # HTTP request handler and server loop
│       └── static/
│           └── index.html      # Single-page web dashboard interface
└── tests/                      # Automated unit and integration test suite
    ├── test_detector.py        # Detector backend unit tests
    └── test_gui.py             # PyQt6 GUI component tests
```

### Component Breakdown

1. **Core Layer (`window_getter.core`)**:
   - **`detector.py`**: Identifies the running desktop environment (checking `$HYPRLAND_INSTANCE_SIGNATURE`, `$SWAYSOCK`, or `$DISPLAY`) and instantiates the appropriate backend.
   - **Compositor Backends (`hyprland.py`, `sway.py`, `x11.py`)**: Abstract communication with window managers to query window states, monitors, and dispatch window management actions.
   - **`proc.py`**: Parses `/proc/<pid>/stat`, `/proc/<pid>/status`, `/proc/<pid>/cmdline`, and memory maps to gather process-level resource metrics without external binary dependencies.
   - **`launcher.py`**: Reconstructs execution commands and maps window classes to `.desktop` entries in `/usr/share/applications` and `~/.local/share/applications`.
   - **`rules.py`**: Formats compositor-specific configuration directives based on window attributes.

2. **Presentation Layer**:
   - **Desktop GUI (`window_getter.gui`)**: Built on PyQt6. Uses a background timer to poll window state changes and updates UI widgets without blocking the event loop.
   - **CLI (`window_getter.cli`)**: Provides direct command-line access to core functions with human-readable table or machine-readable JSON output formats.
   - **Web Server (`window_getter.web`)**: Implements an embedded HTTP server providing REST endpoints and a browser-based dashboard.

---

## Testing

Run the pytest test suite:

```bash
pytest
```

---

## License

This project is licensed under the MIT License. See the license declarations in `pyproject.toml` for details.
