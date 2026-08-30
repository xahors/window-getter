"""
Active Window Inspector Widget for PyQt6 GUI.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
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
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header Row (Badge + PID)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.badge_label = QLabel("ACTIVE FOCUS")
        self.badge_label.setFixedHeight(24)
        self.badge_label.setStyleSheet("""
            background-color: #383838;
            color: #ffffff;
            border: 1px solid #505050;
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: 700;
            font-size: 11px;
        """)
        
        self.pid_label = QLabel("PID: --")
        self.pid_label.setFixedHeight(24)
        self.pid_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 12px;
        """)

        header_layout.addWidget(self.badge_label, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()
        header_layout.addWidget(self.pid_label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(header_layout)

        # Window Title
        self.title_label = QLabel("No active window selected")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Meta Grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        self.app_id_val = self._create_meta_box(grid, "APP ID / CLASS", "--", 0, 0)
        self.geom_val = self._create_meta_box(grid, "GEOMETRY (W×H @ X,Y)", "--", 0, 1)
        self.ws_val = self._create_meta_box(grid, "WORKSPACE", "--", 1, 0)
        self.mem_val = self._create_meta_box(grid, "MEMORY (RSS)", "--", 1, 1)

        layout.addLayout(grid)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.rule_btn = QPushButton("Create Rule")
        self.rule_btn.setObjectName("primaryBtn")
        self.rule_btn.clicked.connect(self._on_rule)


        self.relaunch_btn = QPushButton("Relaunch Window")
        self.relaunch_btn.clicked.connect(self._on_relaunch)


        self.inspect_btn = QPushButton("Inspect Process")
        self.inspect_btn.clicked.connect(self._on_inspect)

        self.close_btn = QPushButton("Close Window")
        self.close_btn.setObjectName("dangerBtn")
        self.close_btn.clicked.connect(self._on_close)

        self.kill_btn = QPushButton("Force Kill")
        self.kill_btn.setObjectName("dangerBtn")
        self.kill_btn.clicked.connect(self._on_kill)

        btn_layout.addWidget(self.rule_btn)
        btn_layout.addWidget(self.relaunch_btn)
        btn_layout.addWidget(self.inspect_btn)
        btn_layout.addWidget(self.close_btn)
        btn_layout.addWidget(self.kill_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _create_meta_box(self, grid: QGridLayout, title: str, default_val: str, row: int, col: int) -> QLabel:
        box = QFrame()
        box.setStyleSheet("""
            background-color: #2d2d2d;
            border: 1px solid #3c3c3c;
            border-radius: 5px;
            padding: 6px 10px;
        """)
        v = QVBoxLayout(box)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(4)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 10px; color: #aaaaaa; font-weight: 600;")
        
        val = QLabel(default_val)
        val.setStyleSheet("font-size: 13px; color: #ffffff; font-family: 'JetBrains Mono', monospace; font-weight: 600;")
        
        v.addWidget(lbl)
        v.addWidget(val)
        grid.addWidget(box, row, col)
        return val

    def update_window(self, win: WindowInfo):
        self.current_window = win
        if not win:
            self.title_label.setText("No active window selected")
            self.pid_label.setText("PID: --")
            self.app_id_val.setText("--")
            self.geom_val.setText("--")
            self.ws_val.setText("--")
            self.mem_val.setText("--")
            return

        self.title_label.setText(win.display_title)
        self.pid_label.setText(f"PID: {win.pid}")
        self.app_id_val.setText(win.display_app_id)
        self.geom_val.setText(win.geometry_str)
        self.ws_val.setText(f"Workspace {win.workspace_name}")
        self.mem_val.setText(f"{win.memory_mb:.1f} MB")

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
