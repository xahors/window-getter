"""
Automated PyQt6 GUI Component & Modal Dialog Tests.
"""

import pytest
from PyQt6.QtWidgets import QApplication
from window_getter.core.models import WindowInfo
from window_getter.gui.main_window import MainWindow
from window_getter.gui.components.active_card import ActiveWindowCard
from window_getter.gui.components.window_table import WindowTableWidget
from window_getter.gui.components.workspace_map import WorkspaceVisualizer
from window_getter.gui.components.process_dialog import ProcessInspectorDialog
from window_getter.gui.components.rule_dialog import RuleGeneratorDialog
from window_getter.gui.components.relaunch_dialog import RelaunchDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app


def test_main_window_instantiation(qapp):
    win = MainWindow()
    assert win is not None
    assert "window-getter" in win.windowTitle()
    win.refresh_data()
    qapp.processEvents()
    win.close()


def test_active_card_widget(qapp):
    card = ActiveWindowCard()
    sample_win = WindowInfo(
        address="0x123",
        app_id="kitty",
        title="Terminal",
        pid=9999,
        width=1200,
        height=800,
        workspace_name="1"
    )
    card.update_window(sample_win)
    assert card.title_label.text() == "Terminal"
    assert "9999" in card.pid_label.text()
    assert card.details_table.rowCount() == 4
    assert card.details_table.item(0, 1).text() == "kitty"
    card._on_copy_json()
    assert "0x123" in QApplication.clipboard().text()
    qapp.processEvents()


def test_window_table_widget(qapp):
    table = WindowTableWidget()
    sample_windows = [
        WindowInfo(address="0x1", app_id="firefox", title="Mozilla Firefox", pid=101, is_active=True),
        WindowInfo(address="0x2", app_id="steam", title="Steam", pid=102, is_active=False),
    ]
    table.update_data(sample_windows, filter_text="")
    assert table.table.rowCount() == 2

    # Test search filter
    table.update_data(sample_windows, filter_text="firefox")
    assert table.table.rowCount() == 1

    # Test copy row
    table.table.selectRow(0)
    table._copy_selected_row()
    assert "firefox" in QApplication.clipboard().text()
    qapp.processEvents()


def test_workspace_visualizer(qapp):
    viz = WorkspaceVisualizer()
    sample_windows = [
        WindowInfo(address="0x1", app_id="kitty", title="Kitty", pid=101, x=0, y=0, width=800, height=600, workspace_name="1"),
        WindowInfo(address="0x2", app_id="firefox", title="Firefox", pid=102, x=800, y=0, width=800, height=600, workspace_name="2"),
    ]
    viz.update_windows(sample_windows)
    viz.resize(800, 600)
    qapp.processEvents()

    # Verify windows loaded and visualizer state
    assert len(viz.windows) == 2
    assert viz.target_workspace == "All"


def test_workspace_visualizer_signals(qapp):
    viz = WorkspaceVisualizer()
    sample_windows = [
        WindowInfo(address="0x1", app_id="kitty", title="Kitty", pid=101, x=0, y=0, width=800, height=600, workspace_name="1"),
    ]
    viz.update_windows(sample_windows)

    received = {}
    viz.focusRequested.connect(lambda addr: received.setdefault("focus", addr))
    viz.windowSelected.connect(lambda w: received.setdefault("selected", w.address))

    viz.focusRequested.emit("0x1")
    assert received.get("focus") == "0x1"


def test_rule_dialog(qapp):
    sample_win = WindowInfo(address="0x1", app_id="kitty", title="Kitty", pid=101)
    dlg = RuleGeneratorDialog(sample_win)
    assert dlg is not None
    assert "hl.window_rule" in dlg.code_preview.toPlainText()
    dlg.close()


def test_process_inspector_dialog(qapp):
    import os
    dlg = ProcessInspectorDialog(os.getpid())
    assert dlg is not None
    assert dlg.details_table.rowCount() > 10
    # Check that properties like Process Name and Process ID exist
    props = [dlg.details_table.item(r, 0).text() for r in range(dlg.details_table.rowCount())]
    assert "Process ID (PID)" in props
    assert "RSS Memory (Physical)" in props
    dlg.close()




