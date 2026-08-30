"""
Rich Command Line Interface (CLI) for window-getter.
"""

import sys
import json
import argparse
from typing import List
from window_getter.core.detector import get_detector
from window_getter.core.models import WindowInfo
from window_getter.core.rules import RuleGenerator
from window_getter.web.server import WebServer


def print_table(windows: List[WindowInfo]):
    """Print clean formatted terminal table of windows."""
    if not windows:
        print("No active GUI windows found.")
        return

    headers = ["ACTIVE", "APP ID / CLASS", "PID", "WS", "SIZE @ POS", "TITLE"]
    
    rows = []
    for w in windows:
        act = "⭐ YES" if w.is_active else "  NO"
        title = w.display_title[:45] + ("..." if len(w.display_title) > 45 else "")
        rows.append([
            act,
            w.display_app_id[:20],
            str(w.pid),
            str(w.workspace_name),
            w.geometry_str,
            title
        ])

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(val))

    format_str = "  ".join([f"{{:<{w}}}" for w in col_widths])
    
    print("-" * (sum(col_widths) + len(col_widths) * 2))
    print(format_str.format(*headers))
    print("-" * (sum(col_widths) + len(col_widths) * 2))
    for row in rows:
        print(format_str.format(*row))
    print("-" * (sum(col_widths) + len(col_widths) * 2))


def main():
    parser = argparse.ArgumentParser(
        prog="window-getter",
        description="Linux Window Inspector & Task Manager CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # active
    active_parser = subparsers.add_parser("active", help="Get details of currently active/focused window")
    active_parser.add_argument("--json", action="store_true", help="Output full raw JSON")
    active_parser.add_argument("--rule", action="store_true", help="Output Hyprland rule snippet")
    active_parser.add_argument("--pid", action="store_true", help="Print PID only")
    active_parser.add_argument("--app-id", action="store_true", help="Print App ID / Class only")
    active_parser.add_argument("--title", action="store_true", help="Print window title only")
    active_parser.add_argument("--size", action="store_true", help="Print geometry size only")

    # list
    list_parser = subparsers.add_parser("list", help="List all active GUI windows")
    list_parser.add_argument("--json", action="store_true", help="Output raw JSON array")
    list_parser.add_argument("--workspace", type=str, default="", help="Filter by workspace name/id")
    list_parser.add_argument("--class", type=str, dest="app_class", default="", help="Filter by app_id/class")

    # get
    get_parser = subparsers.add_parser("get", help="Get details of window matching query")
    get_parser.add_argument("query", type=str, help="Search query (address, PID, app_id, title)")
    get_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # close
    close_parser = subparsers.add_parser("close", help="Gracefully close window")
    close_parser.add_argument("query", type=str, help="Window query (active, address, PID, app_id, title)")

    # kill
    kill_parser = subparsers.add_parser("kill", help="Force kill process (SIGKILL)")
    kill_parser.add_argument("target", type=str, help="PID or window query to kill")

    # relaunch
    relaunch_parser = subparsers.add_parser("relaunch", help="Relaunch application window")
    relaunch_parser.add_argument("query", type=str, help="Window query (active, address, PID, app_id)")
    relaunch_parser.add_argument("--command", type=str, default="", help="Optional custom command string")

    # focus
    focus_parser = subparsers.add_parser("focus", help="Bring target window to focus")
    focus_parser.add_argument("query", type=str, help="Window query to focus")

    # rule
    rule_parser = subparsers.add_parser("rule", help="Create custom window rule snippet")
    rule_parser.add_argument("query", type=str, nargs="?", default="active", help="Window query (default: active)")
    rule_parser.add_argument("--target", choices=["hyprland_lua", "hyprland_conf", "sway"], default="hyprland_lua", help="Target window manager syntax format")


    # gui
    subparsers.add_parser("gui", help="Launch Desktop GUI Application")

    # web
    web_parser = subparsers.add_parser("web", help="Launch Web Dashboard Server")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    web_parser.add_argument("--port", type=int, default=8080, help="Port number")

    args = parser.parse_args()
    detector = get_detector()

    # Default action if no subcommand is given: Launch Desktop GUI App!
    if not args.command:
        from window_getter.gui.app import run_gui
        sys.exit(run_gui())


    if args.command == "active":
        win = detector.get_active_window()
        if not win:
            print("No active window found.", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(win.to_dict(), indent=2))
        elif args.rule:
            print(win.generate_hyprland_rule("float"))
        elif args.pid:
            print(win.pid)
        elif args.app_id:
            print(win.display_app_id)
        elif args.title:
            print(win.display_title)
        elif args.size:
            print(f"{win.width}x{win.height}")
        else:
            print(json.dumps(win.to_dict(), indent=2))

    elif args.command == "list":
        windows = detector.get_windows()
        if args.workspace:
            windows = [w for w in windows if str(w.workspace_name or w.workspace_id) == args.workspace]
        if args.app_class:
            windows = [w for w in windows if args.app_class.lower() in w.display_app_id.lower()]

        if args.json:
            print(json.dumps([w.to_dict() for w in windows], indent=2))
        else:
            print_table(windows)

    elif args.command == "get":
        win = detector.find_window(args.query)
        if not win:
            print(f"Window matching '{args.query}' not found.", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(win.to_dict(), indent=2))
        else:
            print(f"Window Information for '{win.display_title}':")
            for k, v in win.to_dict().items():
                print(f"  {k}: {v}")

    elif args.command == "close":
        success, msg = detector.close_window(args.query)
        print(msg)
        sys.exit(0 if success else 1)

    elif args.command == "kill":
        target = args.target
        if target.isdigit():
            pid = int(target)
        else:
            win = detector.find_window(target)
            pid = win.pid if win else 0

        if pid <= 0:
            print(f"Target '{args.target}' could not be resolved to a valid PID.", file=sys.stderr)
            sys.exit(1)

        success, msg = detector.kill_process(pid)
        print(msg)
        sys.exit(0 if success else 1)

    elif args.command == "relaunch":
        success, msg = detector.relaunch_window(args.query, custom_command=args.command)
        print(msg)
        sys.exit(0 if success else 1)

    elif args.command == "focus":
        success, msg = detector.focus_window(args.query)
        print(msg)
        sys.exit(0 if success else 1)

    elif args.command == "rule":
        win = detector.find_window(args.query)
        if not win:
            print(f"Window matching '{args.query}' not found.", file=sys.stderr)
            sys.exit(1)
        block = RuleGenerator.generate_formatted_block(win, target=args.target)
        print(block)

    elif args.command == "gui":
        from window_getter.gui.app import run_gui
        run_gui()

    elif args.command == "web":
        server = WebServer(host=args.host, port=args.port)
        server.start(block=True)


if __name__ == "__main__":
    main()
