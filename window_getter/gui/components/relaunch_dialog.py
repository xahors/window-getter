"""
Relaunch Window Modal Dialog for PyQt6 GUI.
"""

import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from window_getter.core.models import WindowInfo
from window_getter.core.launcher import relaunch_window
from window_getter.core.detector import get_detector


class RelaunchDialog(QDialog):
    def __init__(self, win: WindowInfo, parent=None):
        super().__init__(parent)
        self.win = win
        self.setWindowTitle(f"Relaunch Window - {win.display_app_id}")
        self.setMinimumSize(500, 220)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel(f"Relaunch Window: {self.win.display_title}")
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        layout.addWidget(header)

        lbl = QLabel("Command line to execute:")
        lbl.setStyleSheet("color: #cccccc; font-size: 12px;")
        layout.addWidget(lbl)

        # Pre-fill command line
        default_cmd = " ".join(self.win.cmdline) if self.win.cmdline else (self.win.exe_path or self.win.display_app_id)
        self.cmd_input = QLineEdit()
        self.cmd_input.setText(default_cmd)
        layout.addWidget(self.cmd_input)

        cwd_lbl = QLabel(f"Working Directory: {self.win.cwd or 'Default'}")
        cwd_lbl.setStyleSheet("font-family: monospace; font-size: 11px; color: #cccccc;")
        layout.addWidget(cwd_lbl)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        launch_btn = QPushButton("Relaunch Window")
        launch_btn.setObjectName("primaryBtn")
        launch_btn.clicked.connect(self._do_relaunch)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(launch_btn)

        layout.addLayout(btn_layout)

    def _do_relaunch(self):
        cmd = self.cmd_input.text().strip()

        # 1. Safely close existing target window
        detector = get_detector()
        detector.close_window(self.win.address)
        time.sleep(0.15)  # Allow window to close gracefully

        # 2. Relaunch process command
        success, msg = relaunch_window(
            cmdline=self.win.cmdline,
            exe_path=self.win.exe_path,
            app_id=self.win.app_id,
            cwd=self.win.cwd,
            custom_command=cmd,
            target_workspace=str(self.win.workspace_name or self.win.workspace_id)
        )


        if success:
            QMessageBox.information(self, "Window Relaunched", f"Closed active window and executed command:\n{msg}")
            self.accept()
        else:
            QMessageBox.warning(self, "Relaunch Error", msg)
