"""
Unit tests for WindowDetector models and backend logic.
"""

import pytest
from window_getter.core.models import WindowInfo, ProcessInfo
from window_getter.core.detector import WindowDetector, get_detector
from window_getter.core.proc import get_process_info
from window_getter.core.rules import RuleGenerator


def test_window_info_formatting():
    win = WindowInfo(
        address="0x123456",
        app_id="kitty",
        title="Terminal - ~",
        pid=1234,
        x=10,
        y=20,
        width=1920,
        height=1080,
        workspace_id=2,
        workspace_name="2",
        memory_mb=128.5
    )

    assert win.geometry_str == "1920x1080 @ (10,20)"
    assert win.display_app_id == "kitty"
    assert win.display_title == "Terminal - ~"

    # Hyprland rules
    hypr_rule = win.generate_hyprland_rule("float")
    assert hypr_rule == "windowrulev2 = float, class:^(kitty)$"

    sway_rule = win.generate_sway_rule("float")
    assert sway_rule == 'for_window [app_id="kitty"] floating enable'


def test_proc_info_reading():
    # Test with current process ID
    import os
    pid = os.getpid()
    proc = get_process_info(pid)
    
    assert proc.pid == pid
    assert proc.status != "dead"
    assert len(proc.cmdline) > 0


def test_rule_generator():
    win = WindowInfo(
        address="0xabc",
        app_id="steam",
        title="Steam Library",
        pid=5555,
        width=1280,
        height=720,
        workspace_name="1"
    )

    lua_rule = RuleGenerator.build_custom_rule(win, syntax="hyprland_lua", float_win=True, launch_workspace=True, workspace_val="1")
    assert "hl.window_rule" in lua_rule
    assert 'class = "^(steam)$"' in lua_rule

    assert "float = true" in lua_rule

    conf_rule = RuleGenerator.build_custom_rule(win, syntax="hyprland_conf", float_win=True)
    assert "windowrulev2 = float, class:^(steam)$" in conf_rule



def test_detector_active_window():
    detector = get_detector()
    windows = detector.get_windows()
    assert isinstance(windows, list)

    active = detector.get_active_window()
    if active:
        assert isinstance(active, WindowInfo)
        assert active.pid > 0


def test_launcher_helpers():
    from window_getter.core.launcher import clean_exec_command, get_default_relaunch_command
    assert clean_exec_command("firefox %u") == "firefox"
    assert clean_exec_command("steam %U") == "steam"

    cmd = get_default_relaunch_command(app_id="kitty", cmdline=["kitty"])
    assert "kitty" in cmd


def test_compat_clean_env(monkeypatch):
    import os
    from window_getter.core.compat import get_clean_env

    monkeypatch.setenv("APPDIR", "/tmp/.mount_window123")
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/.mount_window123/usr/lib:/usr/local/lib")

    clean = get_clean_env()
    assert "/tmp/.mount_window123" not in clean.get("LD_LIBRARY_PATH", "")
    assert "/usr/local/lib" in clean.get("LD_LIBRARY_PATH", "")


def test_backend_detection():
    detector = WindowDetector()
    assert detector.backend_name in ["Hyprland", "Sway", "X11", "Generic / Unsupported"]


