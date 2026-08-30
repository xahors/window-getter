"""
Rich Process Details Inspector Dialog with Real-Time Live Updating Metrics for PyQt6 GUI.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QComboBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer
from window_getter.core.proc import get_process_info


class ProcessInspectorDialog(QDialog):
    def __init__(self, pid: int, parent=None):
        super().__init__(parent)
        self.pid = pid
        self.setWindowTitle(f"Process Details - PID {pid}")
        self.setMinimumSize(820, 620)
        self._init_ui()

        # Live Task-Manager Active Updates Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_metrics)
        self.timer.start(1000)  # Default 1 second polling interval

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        info = get_process_info(self.pid)

        # Header Bar with Live Indicator & Rate Selector
        header_layout = QHBoxLayout()
        self.header_title = QLabel(f"Process Inspector: {info.name or 'Process'} (PID {self.pid})")
        self.header_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()

        self.rate_combo = QComboBox()
        self.rate_combo.addItem("Update: 1s", 1000)
        self.rate_combo.addItem("Update: 500ms", 500)
        self.rate_combo.addItem("Update: 2s", 2000)
        self.rate_combo.addItem("Update: Paused", 0)
        self.rate_combo.currentIndexChanged.connect(self._on_rate_changed)
        header_layout.addWidget(self.rate_combo)

        layout.addLayout(header_layout)

        self.tabs = QTabWidget()

        # ----------------------------------------------------
        # Tab 1: Overview (Details List View)
        # ----------------------------------------------------
        overview_tab = QWidget()
        ov_v = QVBoxLayout(overview_tab)
        ov_v.setContentsMargins(10, 10, 10, 10)
        ov_v.setSpacing(8)

        # Overview Details Table
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(2)
        self.details_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.details_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.details_table.setColumnWidth(0, 240)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.details_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                gridline-color: #2d2d2d;
            }
            QTableWidget::item {
                padding: 6px 12px;
            }
            QTableWidget::item:selected {
                background-color: #3e3e42;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 6px 12px;
                border: 1px solid #3c3c3c;
                font-weight: 600;
            }
        """)

        self.prop_keys = [
            "Process Name",
            "Process ID (PID)",
            "Parent Process (PPID)",
            "User / Owner",
            "Status",
            "Active Threads",
            "Start Time",
            "Uptime",
            "CPU Utilization",
            "RSS Memory (Physical)",
            "Virtual Memory (Size)",
            "Peak Virtual Memory",
            "Virtual Memory (Swap)",
            "Storage Read",
            "Storage Write",
            "Open File Descriptors",
            "Context Switches",
            "Executable Binary",
            "Working Directory",
        ]

        self.details_table.setRowCount(len(self.prop_keys))
        font_prop = QFont("Inter", 9, QFont.Weight.Medium)
        font_val = QFont("JetBrains Mono", 9)
        font_val.setStyleHint(QFont.StyleHint.Monospace)

        for row, prop in enumerate(self.prop_keys):
            item_prop = QTableWidgetItem(prop)
            item_prop.setFont(font_prop)
            item_prop.setForeground(QColor("#aaaaaa"))

            item_val = QTableWidgetItem("")
            item_val.setFont(font_val)
            item_val.setForeground(QColor("#ffffff"))

            self.details_table.setItem(row, 0, item_prop)
            self.details_table.setItem(row, 1, item_val)

        ov_v.addWidget(self.details_table)
        self.tabs.addTab(overview_tab, "Overview")

        # ----------------------------------------------------
        # Tab 2: Command Line Arguments
        # ----------------------------------------------------
        cmd_tab = QWidget()
        cmd_v = QVBoxLayout(cmd_tab)
        cmd_v.setContentsMargins(10, 10, 10, 10)
        cmd_v.setSpacing(8)

        cmd_title = QLabel("Full Executable Command Line:")
        cmd_title.setStyleSheet("font-weight: 600; color: #cccccc; font-size: 12px;")
        cmd_v.addWidget(cmd_title)

        self.cmd_edit = QTextEdit()
        self.cmd_edit.setReadOnly(True)
        cmd_v.addWidget(self.cmd_edit)

        self.tabs.addTab(cmd_tab, "Command Line")

        # ----------------------------------------------------
        # Tab 3: Environment Variables
        # ----------------------------------------------------
        env_tab = QWidget()
        env_v = QVBoxLayout(env_tab)
        env_v.setContentsMargins(10, 10, 10, 10)
        env_v.setSpacing(8)

        self.env_search = QLineEdit()
        self.env_search.setPlaceholderText("Search environment variables...")
        self.env_search.textChanged.connect(self._filter_env_table)
        env_v.addWidget(self.env_search)

        self.env_table = QTableWidget()
        self.env_table.setColumnCount(2)
        self.env_table.setHorizontalHeaderLabels(["Variable Name", "Value"])
        self.env_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.env_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.env_table.setColumnWidth(0, 240)
        self.env_table.verticalHeader().setVisible(False)
        self.env_table.setAlternatingRowColors(True)
        self.env_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                gridline-color: #2d2d2d;
            }
            QTableWidget::item {
                padding: 6px 12px;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 6px 12px;
                border: 1px solid #3c3c3c;
                font-weight: 600;
            }
        """)
        env_v.addWidget(self.env_table)

        self.env_tab_idx = self.tabs.addTab(env_tab, "Environment")

        # ----------------------------------------------------
        # Tab 4: Open File Descriptors
        # ----------------------------------------------------
        fd_tab = QWidget()
        fd_v = QVBoxLayout(fd_tab)
        fd_v.setContentsMargins(10, 10, 10, 10)
        fd_v.setSpacing(8)

        fd_lbl = QLabel("Open File Descriptors Symlinks:")
        fd_lbl.setStyleSheet("font-weight: 600; color: #cccccc; font-size: 12px;")
        fd_v.addWidget(fd_lbl)

        self.fd_edit = QTextEdit()
        self.fd_edit.setReadOnly(True)
        fd_v.addWidget(self.fd_edit)

        self.fd_tab_idx = self.tabs.addTab(fd_tab, "Open FDs")

        layout.addWidget(self.tabs, 1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        # Populate initial values
        self._update_ui_with_info(info, initial=True)

    def _on_rate_changed(self):
        rate = self.rate_combo.currentData()
        if rate > 0:
            self.timer.start(rate)
        else:
            self.timer.stop()

    def _refresh_metrics(self):
        info = get_process_info(self.pid)
        self._update_ui_with_info(info, initial=False)

    def _update_ui_with_info(self, info, initial: bool = False):
        if info.status == "dead" or not info.name:
            self.timer.stop()

        # Update Overview Table
        values_map = {
            "Process Name": info.name or "N/A",
            "Process ID (PID)": str(info.pid),
            "Parent Process (PPID)": f"{info.ppid} ({info.parent_name or 'systemd'})" if info.ppid > 0 else "None",
            "User / Owner": f"{info.user}",
            "Status": info.status if info.status != "dead" else "Terminated (dead)",
            "Active Threads": str(info.threads),
            "Start Time": info.start_time_str or "N/A",
            "Uptime": info.uptime_str or "N/A",
            "CPU Utilization": f"{info.cpu_percent:.1f} %",
            "RSS Memory (Physical)": f"{info.memory_mb:.1f} MB",
            "Virtual Memory (Size)": f"{info.vm_size_mb:.1f} MB",
            "Peak Virtual Memory": f"{info.vm_peak_mb:.1f} MB",
            "Virtual Memory (Swap)": f"{info.vm_swap_mb:.1f} MB",
            "Storage Read": f"{info.read_bytes_mb:.2f} MB",
            "Storage Write": f"{info.write_bytes_mb:.2f} MB",
            "Open File Descriptors": str(info.open_fds),
            "Context Switches": f"{info.voluntary_ctxt_switches:,} voluntary, {info.nonvoluntary_ctxt_switches:,} nonvoluntary",
            "Executable Binary": info.exe_path or "N/A",
            "Working Directory": info.cwd or "N/A",
        }

        for row, prop in enumerate(self.prop_keys):
            val = values_map.get(prop, "")
            item_val = self.details_table.item(row, 1)
            if item_val:
                item_val.setText(str(val))
                if prop == "CPU Utilization" and info.cpu_percent > 5.0:
                    item_val.setForeground(QColor("#4ade80"))
                elif prop == "Status" and info.status == "dead":
                    item_val.setForeground(QColor("#f87171"))
                else:
                    item_val.setForeground(QColor("#ffffff"))

        # Initial/Static updates
        if initial:
            cmd_str = " ".join(info.cmdline) if info.cmdline else "N/A"
            self.cmd_edit.setText(cmd_str)
            self._populate_env_table(info.environ)
            self.tabs.setTabText(self.env_tab_idx, f"Environment ({len(info.environ)})")

        # Update FDs Tab
        fd_text = "\n".join(info.fd_details) if info.fd_details else "No accessible file descriptors"
        if self.fd_edit.toPlainText() != fd_text:
            self.fd_edit.setText(fd_text)
        self.tabs.setTabText(self.fd_tab_idx, f"Open FDs ({len(info.fd_details)})")

    def _populate_env_table(self, env_dict):
        self.env_items = list(env_dict.items())
        self._filter_env_table()

    def _filter_env_table(self):
        query = self.env_search.text().lower()
        filtered = [(k, v) for k, v in getattr(self, "env_items", []) if query in k.lower() or query in v.lower()]

        self.env_table.setRowCount(len(filtered))
        for row, (k, v) in enumerate(filtered):
            item_k = QTableWidgetItem(k)
            item_v = QTableWidgetItem(v)
            self.env_table.setItem(row, 0, item_k)
            self.env_table.setItem(row, 1, item_v)

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)

    def reject(self):
        self.timer.stop()
        super().reject()

    def accept(self):
        self.timer.stop()
        super().accept()
