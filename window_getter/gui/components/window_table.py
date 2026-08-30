"""
Window List Table Widget with Right-Click Context Menu for PyQt6 GUI.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from window_getter.core.models import WindowInfo


class WindowTableWidget(QWidget):
    focusRequested = pyqtSignal(str)
    relaunchRequested = pyqtSignal(str)
    closeRequested = pyqtSignal(str)
    killRequested = pyqtSignal(int)
    ruleRequested = pyqtSignal(str)
    inspectProcessRequested = pyqtSignal(int)
    windowSelected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.windows: List[WindowInfo] = []
        self.filtered_windows: List[WindowInfo] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Status", "App ID / Class", "Window Title", "PID", "Workspace", "Geometry", "Memory"
        ])
        
        # Configure Header Column Resizing
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Context Menu & Selection Signals
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.table)

    def update_data(self, windows: List[WindowInfo], filter_text: str = "", filter_workspace: str = "All"):
        self.windows = windows
        q = filter_text.lower().strip()

        self.filtered_windows = []
        for w in windows:
            ws_str = str(w.workspace_name or w.workspace_id)
            if filter_workspace != "All" and ws_str != filter_workspace:
                continue

            if q:
                match = (
                    q in w.display_title.lower() or
                    q in w.display_app_id.lower() or
                    q in str(w.pid) or
                    q in w.address.lower()
                )
                if not match:
                    continue

            self.filtered_windows.append(w)

        self.table.blockSignals(True)
        self.table.setRowCount(len(self.filtered_windows))

        for row, w in enumerate(self.filtered_windows):
            # Status
            active_item = QTableWidgetItem("[Active]" if w.is_active else "")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # App ID / Class
            app_item = QTableWidgetItem(w.display_app_id)
            
            # Title
            title_item = QTableWidgetItem(w.display_title)
            
            # PID
            pid_item = QTableWidgetItem(str(w.pid))
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Workspace
            ws_item = QTableWidgetItem(str(w.workspace_name or w.workspace_id))
            ws_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)


            # Geometry
            geom_item = QTableWidgetItem(w.geometry_str)
            geom_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Memory
            mem_item = QTableWidgetItem(f"{w.memory_mb:.1f} MB")
            mem_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self.table.setItem(row, 0, active_item)
            self.table.setItem(row, 1, app_item)
            self.table.setItem(row, 2, title_item)
            self.table.setItem(row, 3, pid_item)
            self.table.setItem(row, 4, ws_item)
            self.table.setItem(row, 5, geom_item)
            self.table.setItem(row, 6, mem_item)

        self.table.blockSignals(False)

    def _on_selection_changed(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.filtered_windows):
            win = self.filtered_windows[row]
            self.windowSelected.emit(win)

    def _show_context_menu(self, pos: QPoint):
        row = self.table.indexAt(pos).row()
        if row < 0 or row >= len(self.filtered_windows):
            return

        self.table.selectRow(row)
        win = self.filtered_windows[row]
        self.windowSelected.emit(win)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #454545;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #454545;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #454545;
                margin: 4px 0px;
            }
        """)

        act_focus = menu.addAction("Focus Window")
        act_rule = menu.addAction("Create Rule")
        act_relaunch = menu.addAction("Relaunch Window")


        act_inspect = menu.addAction("Inspect Process")
        menu.addSeparator()
        act_close = menu.addAction("Close Window")
        act_kill = menu.addAction("Force Kill (SIGKILL)")

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if not action:
            return

        if action == act_focus:
            self.focusRequested.emit(win.address)
        elif action == act_rule:
            self.ruleRequested.emit(win.address)
        elif action == act_relaunch:
            self.relaunchRequested.emit(win.address)
        elif action == act_inspect:
            if win.pid > 0:
                self.inspectProcessRequested.emit(win.pid)
        elif action == act_close:
            self.closeRequested.emit(win.address)
        elif action == act_kill:
            if win.pid > 0:
                self.killRequested.emit(win.pid)
