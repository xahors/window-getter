"""
Active Window Inspector Widget with Details List View and Copy Support for PyQt6 GUI.
"""

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu, QApplication
)
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from window_getter.core.models import WindowInfo


class ActiveWindowCard(QFrame):
    focusRequested = pyqtSignal(str)
    relaunchRequested = pyqtSignal(str)
    closeRequested = pyqtSignal(str)
    killRequested = pyqtSignal(int)
    ruleRequested = pyqtSignal(str)
    inspectProcessRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_window: WindowInfo = None
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            ActiveWindowCard {
                background-color: #202020;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Row (Title + PID)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("No active window selected")
        self.title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)

        self.pid_label = QLabel("PID: --")
        self.pid_label.setFixedHeight(22)
        self.pid_label.setStyleSheet("""
            color: #aaaaaa;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            font-size: 11px;
            padding: 2px 6px;
            background-color: #2a2a2a;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
        """)
        self.pid_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        header_layout.addWidget(self.title_label, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.pid_label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(header_layout)

        # Details List Table
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(4)
        self.details_table.setHorizontalHeaderLabels(["Property", "Value", "Property", "Value"])
        self.details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.details_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.details_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.details_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.details_table.setColumnWidth(0, 150)
        self.details_table.setColumnWidth(2, 150)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.horizontalHeader().setVisible(False)
        self.details_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.details_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setMaximumHeight(140)
        self.details_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.details_table.customContextMenuRequested.connect(self._show_details_context_menu)

        self.details_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                alternate-background-color: #222222;
                color: #ffffff;
                border: 1px solid #383838;
                border-radius: 5px;
                gridline-color: #2d2d2d;
            }
            QTableWidget::item {
                padding: 4px 10px;
            }
            QTableWidget::item:selected {
                background-color: #3e3e42;
                color: #ffffff;
            }
        """)

        layout.addWidget(self.details_table)

        # Action Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.rule_btn = QPushButton("Create Rule")
        self.rule_btn.setObjectName("primaryBtn")
        self.rule_btn.clicked.connect(self._on_rule)

        self.relaunch_btn = QPushButton("Relaunch Window")
        self.relaunch_btn.clicked.connect(self._on_relaunch)

        self.inspect_btn = QPushButton("Inspect Process")
        self.inspect_btn.clicked.connect(self._on_inspect)

        self.copy_btn = QPushButton("Copy JSON")
        self.copy_btn.setToolTip("Copy active window metadata JSON to clipboard")
        self.copy_btn.clicked.connect(self._on_copy_json)

        self.close_btn = QPushButton("Close Window")
        self.close_btn.setObjectName("dangerBtn")
        self.close_btn.clicked.connect(self._on_close)

        self.kill_btn = QPushButton("Force Kill")
        self.kill_btn.setObjectName("dangerBtn")
        self.kill_btn.clicked.connect(self._on_kill)

        btn_layout.addWidget(self.rule_btn)
        btn_layout.addWidget(self.relaunch_btn)
        btn_layout.addWidget(self.inspect_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        btn_layout.addWidget(self.kill_btn)

        layout.addLayout(btn_layout)

        # Initialize empty table grid
        self._populate_grid([
            ("App ID / Class", "--", "Geometry (W×H @ X,Y)", "--"),
            ("Workspace", "--", "Memory (RSS)", "--"),
            ("Window Address", "--", "State / Flags", "--"),
            ("Executable Binary", "--", "Working Directory", "--"),
        ])

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Copy):
            self._copy_selected_cell()
            return
        super().keyPressEvent(event)

    def _copy_selected_cell(self):
        selected = self.details_table.selectedItems()
        if selected:
            text = "\t".join([item.text() for item in selected])
            QApplication.clipboard().setText(text)
        elif self.current_window:
            self._on_copy_json()

    def _populate_grid(self, row_data):
        self.details_table.setRowCount(len(row_data))
        font_prop = QFont("Inter", 8, QFont.Weight.Medium)
        font_val = QFont("JetBrains Mono", 8)
        font_val.setStyleHint(QFont.StyleHint.Monospace)

        for r, (p1, v1, p2, v2) in enumerate(row_data):
            # Col 0 (Prop 1)
            i0 = QTableWidgetItem(p1)
            i0.setFont(font_prop)
            i0.setForeground(QColor("#aaaaaa"))

            # Col 1 (Val 1)
            i1 = QTableWidgetItem(str(v1))
            i1.setFont(font_val)
            i1.setForeground(QColor("#ffffff"))

            # Col 2 (Prop 2)
            i2 = QTableWidgetItem(p2)
            i2.setFont(font_prop)
            i2.setForeground(QColor("#aaaaaa"))

            # Col 3 (Val 2)
            i3 = QTableWidgetItem(str(v2))
            i3.setFont(font_val)
            i3.setForeground(QColor("#ffffff"))

            self.details_table.setItem(r, 0, i0)
            self.details_table.setItem(r, 1, i1)
            self.details_table.setItem(r, 2, i2)
            self.details_table.setItem(r, 3, i3)

    def update_window(self, win: WindowInfo):
        self.current_window = win
        if not win:
            self.title_label.setText("No active window selected")
            self.pid_label.setText("PID: --")
            self._populate_grid([
                ("App ID / Class", "--", "Geometry (W×H @ X,Y)", "--"),
                ("Workspace", "--", "Memory (RSS)", "--"),
                ("Window Address", "--", "State / Flags", "--"),
                ("Executable Binary", "--", "Working Directory", "--"),
            ])
            return

        self.title_label.setText(win.display_title)
        self.pid_label.setText(f"PID: {win.pid}")

        state_flags = []
        if win.is_floating:
            state_flags.append("Floating")
        else:
            state_flags.append("Tiled")
        if win.is_fullscreen:
            state_flags.append("Fullscreen")
        if win.is_xwayland:
            state_flags.append("XWayland")
        state_str = ", ".join(state_flags) if state_flags else "Standard"

        row_data = [
            ("App ID / Class", win.display_app_id, "Geometry (W×H @ X,Y)", win.geometry_str),
            ("Workspace", f"Workspace {win.workspace_name}", "Memory (RSS)", f"{win.memory_mb:.1f} MB"),
            ("Window Address", win.address, "State / Flags", state_str),
            ("Executable Binary", win.exe_path or "N/A", "Working Directory", win.cwd or "N/A"),
        ]
        self._populate_grid(row_data)

    def _show_details_context_menu(self, pos: QPoint):
        item = self.details_table.itemAt(pos)
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
        """)

        if item:
            act_copy_val = menu.addAction("Copy Cell Value")
            act_copy_val.triggered.connect(lambda: QApplication.clipboard().setText(item.text()))

        if self.current_window:
            act_copy_addr = menu.addAction("Copy Window Address")
            act_copy_addr.triggered.connect(lambda: QApplication.clipboard().setText(self.current_window.address))

            act_copy_title = menu.addAction("Copy Window Title")
            act_copy_title.triggered.connect(lambda: QApplication.clipboard().setText(self.current_window.title))

            act_copy_app = menu.addAction("Copy App ID")
            act_copy_app.triggered.connect(lambda: QApplication.clipboard().setText(self.current_window.display_app_id))

            act_copy_json = menu.addAction("Copy Window JSON")
            act_copy_json.triggered.connect(self._on_copy_json)

        menu.exec(self.details_table.viewport().mapToGlobal(pos))

    def _on_copy_json(self):
        if self.current_window:
            data = self.current_window.to_dict()
            QApplication.clipboard().setText(json.dumps(data, indent=2))

    def _on_rule(self):
        if self.current_window:
            self.ruleRequested.emit(self.current_window.address)

    def _on_relaunch(self):
        if self.current_window:
            self.relaunchRequested.emit(self.current_window.address)

    def _on_inspect(self):
        if self.current_window and self.current_window.pid > 0:
            self.inspectProcessRequested.emit(self.current_window.pid)

    def _on_close(self):
        if self.current_window:
            self.closeRequested.emit(self.current_window.address)

    def _on_kill(self):
        if self.current_window and self.current_window.pid > 0:
            self.killRequested.emit(self.current_window.pid)
