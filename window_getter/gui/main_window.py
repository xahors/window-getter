"""
PyQt6 Main Window Application Shell for window-getter.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QLineEdit, QComboBox, QPushButton, QStatusBar, QMessageBox, QInputDialog
)
from PyQt6.QtCore import QTimer, Qt, QEvent


from window_getter.core.detector import get_detector
from window_getter.core.models import WindowInfo
from window_getter.gui.theme import DARK_THEME_QSS
from window_getter.gui.components.active_card import ActiveWindowCard
from window_getter.gui.components.window_table import WindowTableWidget
from window_getter.gui.components.workspace_map import WorkspaceVisualizer
from window_getter.gui.components.process_dialog import ProcessInspectorDialog
from window_getter.gui.components.relaunch_dialog import RelaunchDialog
from window_getter.gui.components.rule_dialog import RuleGeneratorDialog



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.detector = get_detector()
        self.web_server: Optional[WebServer] = None
        self.windows_cache: List[WindowInfo] = []

        self.setWindowTitle(f"window-getter — Linux Window & Task Manager ({self.detector.backend_name})")
        self.resize(1080, 720)
        self.setStyleSheet(DARK_THEME_QSS)

        self._init_ui()
        self._setup_timer()
        self.refresh_data()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Header Bar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self.backend_badge = QLabel(f"Backend: {self.detector.backend_name}")
        self.backend_badge.setStyleSheet("""
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #454545;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 700;
        """)

        header_layout.addWidget(self.backend_badge)
        header_layout.addStretch()

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search windows by title, app ID, PID...")
        self.search_input.setFixedWidth(260)
        self.search_input.textChanged.connect(self._apply_filters)

        # Workspace Filter
        self.ws_combo = QComboBox()
        self.ws_combo.addItem("Workspace: All", "All")
        self.ws_combo.currentIndexChanged.connect(self._apply_filters)

        # Refresh Rate Combo
        self.refresh_combo = QComboBox()
        self.refresh_combo.addItem("Auto-refresh: Adaptive (10ms active / 1s idle)", "adaptive")
        self.refresh_combo.addItem("Auto-refresh: Immediate (10ms)", 10)
        self.refresh_combo.addItem("Auto-refresh: 100ms", 100)
        self.refresh_combo.addItem("Auto-refresh: 500ms", 500)
        self.refresh_combo.addItem("Auto-refresh: 1s", 1000)
        self.refresh_combo.addItem("Auto-refresh: Off", 0)
        self.refresh_combo.setCurrentIndex(0)
        self.refresh_combo.currentIndexChanged.connect(self._on_refresh_rate_changed)

        # Buttons
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)

        new_app_btn = QPushButton("Launch App")
        new_app_btn.setObjectName("primaryBtn")
        new_app_btn.clicked.connect(self._launch_new_app)

        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.ws_combo)
        header_layout.addWidget(self.refresh_combo)
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(new_app_btn)

        main_layout.addLayout(header_layout)

        # 2. Main Tab Widget
        self.tabs = QTabWidget()
        self.selected_window_address = ""

        # Combined Windows Tab (Active Window Inspector Card on Top + Windows Table on Bottom)
        windows_container = QWidget()
        win_layout = QVBoxLayout(windows_container)
        win_layout.setContentsMargins(0, 8, 0, 0)
        win_layout.setSpacing(12)

        self.active_card = ActiveWindowCard()
        self.active_card.focusRequested.connect(self._on_focus_window)
        self.active_card.relaunchRequested.connect(self._on_relaunch_dialog)
        self.active_card.closeRequested.connect(self._on_close_window)
        self.active_card.killRequested.connect(self._on_kill_process)
        self.active_card.ruleRequested.connect(self._on_rule_dialog)
        self.active_card.inspectProcessRequested.connect(self._on_inspect_process)

        self.table_widget = WindowTableWidget()
        self.table_widget.focusRequested.connect(self._on_focus_window)
        self.table_widget.relaunchRequested.connect(self._on_relaunch_dialog)
        self.table_widget.closeRequested.connect(self._on_close_window)
        self.table_widget.killRequested.connect(self._on_kill_process)
        self.table_widget.ruleRequested.connect(self._on_rule_dialog)
        self.table_widget.inspectProcessRequested.connect(self._on_inspect_process)
        self.table_widget.windowSelected.connect(self._on_window_selected)

        win_layout.addWidget(self.active_card)
        win_layout.addWidget(self.table_widget, 1)

        self.tabs.addTab(windows_container, "Windows")

        # Tab 2: Workspace Visualizer
        self.visualizer = WorkspaceVisualizer()
        self.visualizer.windowClicked.connect(self._on_focus_window)
        self.visualizer.workspaceSelected.connect(self._on_workspace_selected_from_map)
        self.tabs.addTab(self.visualizer, "Workspace Map")

        main_layout.addWidget(self.tabs)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self._update_timer_interval()

    def changeEvent(self, event):
        if event.type() in (QEvent.Type.ActivationChange, QEvent.Type.WindowStateChange):
            self._update_timer_interval()
        super().changeEvent(event)

    def _on_refresh_rate_changed(self):
        self._update_timer_interval()

    def _update_timer_interval(self):
        mode = self.refresh_combo.currentData()
        if mode == "adaptive":
            is_active = self.isActiveWindow() and not self.isMinimized()
            interval = 10 if is_active else 1000
        else:
            try:
                interval = int(mode)
            except Exception:
                interval = 10

        if interval > 0:
            if not self.timer.isActive() or self.timer.interval() != interval:
                self.timer.start(interval)
        else:
            self.timer.stop()


    def _on_window_selected(self, win: WindowInfo):
        if win:
            self.selected_window_address = win.address
            self.active_card.update_window(win)

    def refresh_data(self):
        self.windows_cache = self.detector.get_windows()
        active_win = self.detector.get_active_window()

        # Update Active Card (selected window if user picked one, else active window)
        target_win = None
        if self.selected_window_address:
            target_win = self.detector.find_window(self.selected_window_address)
        if not target_win:
            target_win = active_win

        self.active_card.update_window(target_win)

        # Update Workspace Filter Dropdown choices only when workspace list changes
        self._update_workspace_dropdown(self.windows_cache)

        # Update Table & Visualizer
        self._apply_filters()

        # Status bar update
        count = len(self.windows_cache)
        active_str = f"Active Focus: {active_win.display_app_id} ('{active_win.display_title[:30]}')" if active_win else "No Active Focus"
        self.status_bar.showMessage(f"Found {count} GUI Windows | {active_str}")

    def _update_workspace_dropdown(self, windows: List[WindowInfo]):
        new_ws_set = sorted(list(set([str(w.workspace_name or w.workspace_id) for w in windows])))
        if hasattr(self, "_known_workspaces") and self._known_workspaces == new_ws_set:
            return

        self._known_workspaces = new_ws_set
        current_ws = str(self.ws_combo.currentData() or "All")

        self.ws_combo.blockSignals(True)
        self.ws_combo.clear()
        self.ws_combo.addItem("Workspace: All", "All")
        for ws in new_ws_set:
            self.ws_combo.addItem(f"Workspace {ws}", str(ws))

        idx = self.ws_combo.findData(current_ws)
        if idx >= 0:
            self.ws_combo.setCurrentIndex(idx)
        else:
            self.ws_combo.setCurrentIndex(0)
        self.ws_combo.blockSignals(False)

    def _apply_filters(self):
        q = self.search_input.text()
        ws = str(self.ws_combo.currentData() or "All")
        self.table_widget.update_data(self.windows_cache, filter_text=q, filter_workspace=ws)
        self.visualizer.update_windows(self.windows_cache, target_workspace=ws)

    def _on_workspace_selected_from_map(self, ws_name: str):
        target_ws = str(ws_name)
        idx = self.ws_combo.findData(target_ws)
        if idx >= 0:
            self.ws_combo.setCurrentIndex(idx)
        self._apply_filters()



    def _on_focus_window(self, address: str):
        success, msg = self.detector.focus_window(address)
        self.status_bar.showMessage(msg)
        self.refresh_data()

    def _on_close_window(self, address: str):
        success, msg = self.detector.close_window(address)
        self.status_bar.showMessage(msg)
        self.refresh_data()

    def _on_kill_process(self, pid: int):
        reply = QMessageBox.question(
            self, "Confirm Force Kill",
            f"Are you sure you want to force kill process PID {pid} (SIGKILL)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.detector.kill_process(pid)
            self.status_bar.showMessage(msg)
            self.refresh_data()

    def _on_relaunch_dialog(self, address: str):
        win = self.detector.find_window(address)
        if win:
            dlg = RelaunchDialog(win, self)
            if dlg.exec() == RelaunchDialog.DialogCode.Accepted:
                self.refresh_data()

    def _on_rule_dialog(self, address: str):
        win = self.detector.find_window(address)
        if win:
            dlg = RuleGeneratorDialog(win, self)
            dlg.exec()

    def _on_inspect_process(self, pid: int):
        dlg = ProcessInspectorDialog(pid, self)
        dlg.exec()

    def _launch_new_app(self):
        cmd, ok = QInputDialog.getText(self, "Launch New Application", "Enter shell command to execute:")
        if ok and cmd.strip():
            success, msg = self.detector.relaunch_window("", custom_command=cmd.strip())
            QMessageBox.information(self, "Launch Result", msg)

