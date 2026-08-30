"""
Rich Process Details Inspector Dialog with Tabbed Metrics for PyQt6 GUI.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGridLayout,
    QFrame, QTabWidget, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit
)
from PyQt6.QtCore import Qt
from window_getter.core.proc import get_process_info


class ProcessInspectorDialog(QDialog):
    def __init__(self, pid: int, parent=None):
        super().__init__(parent)
        self.pid = pid
        self.setWindowTitle(f"Process Details - PID {pid}")
        self.setMinimumSize(740, 560)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        info = get_process_info(self.pid)

        header = QLabel(f"Process Inspector: {info.name or 'Process'} (PID {self.pid})")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        layout.addWidget(header)

        tabs = QTabWidget()

        # ----------------------------------------------------
        # Tab 1: Overview & Metrics
        # ----------------------------------------------------
        overview_tab = QWidget()
        ov_v = QVBoxLayout(overview_tab)
        ov_v.setContentsMargins(10, 10, 10, 10)
        ov_v.setSpacing(10)

        # Meta Grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        self._add_grid_box(grid, "STATUS", info.status, 0, 0)
        self._add_grid_box(grid, "USER / UID", info.user, 0, 1)
        self._add_grid_box(grid, "PARENT PROCESS (PPID)", f"{info.ppid} ({info.parent_name or 'N/A'})", 0, 2)

        self._add_grid_box(grid, "START TIME", info.start_time_str or "N/A", 1, 0)
        self._add_grid_box(grid, "UPTIME", info.uptime_str or "N/A", 1, 1)
        self._add_grid_box(grid, "THREADS", str(info.threads), 1, 2)

        self._add_grid_box(grid, "RSS MEMORY", f"{info.memory_mb:.1f} MB", 2, 0)
        self._add_grid_box(grid, "VIRTUAL MEMORY (SIZE)", f"{info.vm_size_mb:.1f} MB", 2, 1)
        self._add_grid_box(grid, "PEAK VIRTUAL MEMORY", f"{info.vm_peak_mb:.1f} MB", 2, 2)

        self._add_grid_box(grid, "STORAGE READ", f"{info.read_bytes_mb:.2f} MB", 3, 0)
        self._add_grid_box(grid, "STORAGE WRITE", f"{info.write_bytes_mb:.2f} MB", 3, 1)
        self._add_grid_box(grid, "OPEN FILE DESCRIPTORS", str(info.open_fds), 3, 2)

        ov_v.addLayout(grid)

        # Additional Paths
        paths_box = QFrame()
        paths_box.setStyleSheet("background-color: #2d2d2d; border: 1px solid #3c3c3c; border-radius: 5px; padding: 8px;")
        paths_v = QVBoxLayout(paths_box)
        paths_v.setSpacing(4)

        exe_lbl = QLabel(f"Executable Binary: {info.exe_path or 'N/A'}")
        exe_lbl.setStyleSheet("font-family: monospace; font-size: 11px; color: #ffffff;")

        cwd_lbl = QLabel(f"Working Directory: {info.cwd or 'N/A'}")
        cwd_lbl.setStyleSheet("font-family: monospace; font-size: 11px; color: #cccccc;")

        ctxt_lbl = QLabel(f"Context Switches: {info.voluntary_ctxt_switches} voluntary, {info.nonvoluntary_ctxt_switches} nonvoluntary")
        ctxt_lbl.setStyleSheet("font-size: 11px; color: #aaaaaa;")

        paths_v.addWidget(exe_lbl)
        paths_v.addWidget(cwd_lbl)
        paths_v.addWidget(ctxt_lbl)

        ov_v.addWidget(paths_box)
        ov_v.addStretch()

        tabs.addTab(overview_tab, "Overview & Metrics")

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

        cmd_edit = QTextEdit()
        cmd_edit.setReadOnly(True)
        cmd_str = " ".join(info.cmdline) if info.cmdline else "N/A"
        cmd_edit.setText(cmd_str)
        cmd_v.addWidget(cmd_edit)

        tabs.addTab(cmd_tab, "Command Line")

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
        self.env_table.setColumnWidth(0, 220)
        self.env_table.verticalHeader().setVisible(False)
        self._populate_env_table(info.environ)
        env_v.addWidget(self.env_table)

        tabs.addTab(env_tab, f"Environment ({len(info.environ)})")

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

        fd_edit = QTextEdit()
        fd_edit.setReadOnly(True)
        fd_text = "\n".join(info.fd_details) if info.fd_details else "No accessible file descriptors"
        fd_edit.setText(fd_text)
        fd_v.addWidget(fd_edit)

        tabs.addTab(fd_tab, f"Open FDs ({len(info.fd_details)})")

        layout.addWidget(tabs, 1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _add_grid_box(self, grid: QGridLayout, title: str, val_text: str, row: int, col: int):
        box = QFrame()
        box.setStyleSheet("""
            background-color: #2d2d2d;
            border: 1px solid #3c3c3c;
            border-radius: 5px;
            padding: 6px 10px;
        """)
        v = QVBoxLayout(box)
        v.setContentsMargins(4, 4, 4, 4)
        v.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 10px; color: #aaaaaa; font-weight: 600;")
        
        v_lbl = QLabel(val_text)
        v_lbl.setStyleSheet("font-size: 12px; color: #ffffff; font-family: monospace; font-weight: 600;")
        v_lbl.setWordWrap(True)
        
        v.addWidget(t_lbl)
        v.addWidget(v_lbl)
        grid.addWidget(box, row, col)

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
