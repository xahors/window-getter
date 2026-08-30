# ⚡ window-getter

**window-getter** is a modern Linux desktop application and task manager for inspecting active GUI windows, managing application lifecycle (closing, force-killing, relaunching), and generating compositor rules (such as Hyprland `windowrulev2` and Sway `for_window`).

---

## 🌟 Key Features

* **Active & Global Window Detection**:
  * **App ID / Class** (Used for writing window rules in Hyprland Lua/Conf configs)
  * **Process ID (PID)** & process tree stats
  * **Window Size & Position** (Width × Height @ X, Y coordinates)
  * **Workspace Association** (ID and display name)
  * **Visibility & State** (Active focus, floating mode, fullscreen, mapped status, XWayland indicator)
  * **Process Metrics** (RSS Memory in MB, CPU usage, working directory, executable path, command line arguments)
* **Task Manager Functionality**:
  * **Close Window**: Send graceful close signals via compositor IPC or window manager dispatchers.
  * **Force Kill**: Terminate stuck processes instantly with `SIGKILL` / `SIGTERM`.
  * **Application Relauncher**: Automatically inspects process `/proc/<pid>/cmdline`, executable binary, or system `.desktop` entries to relaunch applications with full command line customization.
  * **Window Focus**: Bring any open window directly to the front/active focus.
  * **Workspace Switcher**: Move windows between workspaces seamlessly.
* **Interactive 2D Desktop Workspace Map**:
  * Live visual representation of screens and window bounding boxes color-coded by workspace and focus state.
* **Window Rule Generator**:
  * Auto-generates copy-pasteable configuration rules for **Hyprland** (`windowrulev2 = float, class:^(app_id)$`) and **Sway** (`for_window [app_id="..."] floating enable`).
* **Multi-Backend Compositor Engine**:
  * **Hyprland** (Native `hyprctl` JSON IPC)
  * **Sway / i3** (`swaymsg` tree API)
  * **X11 / Generic** (`xdotool`, `xprop`, `wmctrl`)

---

## 🚀 Quick Start & Installation

### Option 1: Using Virtual Environment (`venv` or `uv`)

```bash
# Clone or enter project directory
cd window-getter

# Create virtual environment
python3 -m venv .venv
# OR using uv: uv venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install window-getter in editable mode
pip install -e .
```

---

## 🖥️ Usage

### Launch Desktop Application

Simply run:
```bash
window-getter
```
*(Or run `.venv/bin/window-getter` directly without activating venv)*

The Desktop GUI app features:
1. **⚡ Active Window Tab**: Highlights the currently selected window with live geometry, process inspection, and action shortcuts.
2. **🪟 Windows Table Tab**: Searchable & filterable table listing all open windows on the desktop.
3. **🗺️ Workspace Map Tab**: Interactive 2D visual layout map of display screens and windows.
4. **📜 Rule Generator**: Create and copy Hyprland/Sway rule blocks.

---

## 💻 CLI Commands

`window-getter` can also be used as a command-line tool for scripting and quick inspection:

| Command | Description |
| :--- | :--- |
| `window-getter` | Launches the PyQt6 Desktop GUI App |
| `window-getter list` | Lists all active GUI windows in a formatted terminal table |
| `window-getter list --json` | Outputs raw JSON array of all active windows |
| `window-getter active` | Prints active focused window details |
| `window-getter active --json` | Outputs JSON of active focused window |
| `window-getter active --rule` | Outputs Hyprland rule snippet for active window |
| `window-getter get <query>` | Finds window by title, App ID, PID, or address |
| `window-getter close <query>` | Gracefully closes window matching query |
| `window-getter kill <pid>` | Force kills process PID |
| `window-getter relaunch <query>` | Relaunches application |
| `window-getter focus <query>` | Focuses target window |
| `window-getter rule <query>` | Generates Hyprland or Sway config rule snippet |

---

## 🛠️ Project Architecture

```
window-getter/
├── pyproject.toml / setup.py     # Package configuration
├── window_getter/
│   ├── cli.py                     # CLI entrypoint & subcommands
│   ├── core/
│   │   ├── models.py              # Data models (WindowInfo, ProcessInfo, WorkspaceInfo)
│   │   ├── detector.py            # WindowDetector multi-backend manager
│   │   ├── hyprland.py            # Hyprland compositor IPC backend
│   │   ├── sway.py                # Sway / i3 compositor backend
│   │   ├── x11.py                 # X11 / xdotool backend
│   │   ├── proc.py                # Process inspector & /proc metrics reader
│   │   ├── launcher.py            # Application relauncher & .desktop resolver
│   │   └── rules.py               # Hyprland & Sway rule generator
│   └── gui/
│       ├── app.py                 # PyQt6 app launcher
│       ├── main_window.py         # Main Window layout & tab controller
│       ├── theme.py               # Dark Glassmorphism QSS design system
│       └── components/
│           ├── active_card.py     # Active window hero card
│           ├── window_table.py    # Searchable window list table
│           ├── workspace_map.py   # Interactive 2D workspace canvas
│           ├── process_dialog.py  # Detailed process inspector modal
│           ├── relaunch_dialog.py # Application relauncher modal
│           └── rule_dialog.py     # Window rule generator modal
└── tests/                         # Pytest test suite
```

---

## 🧪 Testing

Run pytest test suite:
```bash
.venv/bin/pytest tests/
```
