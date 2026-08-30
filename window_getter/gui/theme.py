"""
PyQt6 Design System - Flat Gray & White Theme (No Gradients).
"""

DARK_THEME_QSS = """
QMainWindow, QDialog {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

QWidget {
    color: #ffffff;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #252526;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #cccccc;
    border: 1px solid #3c3c3c;
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: 600;
    font-size: 12px;
}

QTabBar::tab:selected {
    background-color: #252526;
    color: #ffffff;
    border-bottom: 2px solid #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #383838;
    color: #ffffff;
}

QGroupBox {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
    font-size: 13px;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 10px;
    background-color: #383838;
    border-radius: 4px;
    left: 14px;
}

QPushButton {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #454545;
    border-radius: 5px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #454545;
    border-color: #666666;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #252526;
}

QPushButton#primaryBtn {
    background-color: #4a4a4a;
    color: #ffffff;
    border: 1px solid #666666;
    font-weight: 700;
}

QPushButton#primaryBtn:hover {
    background-color: #5a5a5a;
    border-color: #888888;
}

QPushButton#dangerBtn {
    background-color: #402828;
    color: #ff9999;
    border: 1px solid #663333;
}

QPushButton#dangerBtn:hover {
    background-color: #553333;
    color: #ffb3b3;
    border-color: #884444;
}

QLineEdit, QComboBox {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #454545;
    border-radius: 4px;
    padding: 3px 6px;
    font-size: 12px;
}


QLineEdit:focus, QComboBox:focus {
    border-color: #777777;
}

/* Fix dropdown popup item colors */
QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #ffffff;
    selection-background-color: #454545;
    selection-color: #ffffff;
    border: 1px solid #454545;
    outline: none;
    padding: 4px;
}

QComboBox QAbstractItemView::item {
    background-color: #2d2d2d;
    color: #ffffff;
    padding: 6px 10px;
}

QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {
    background-color: #454545;
    color: #ffffff;
}

QTableWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    gridline-color: #333333;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    selection-background-color: #383838;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #2d2d2d;
    color: #cccccc;
    padding: 8px;
    font-weight: 700;
    font-size: 11px;
    border: none;
    border-bottom: 1px solid #3c3c3c;
    text-transform: uppercase;
}

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #383838;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #505050;
}

QCheckBox {
    color: #ffffff;
    spacing: 8px;
    font-size: 12px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 3px;
    background-color: #2b2b2b;
}

QCheckBox::indicator:hover {
    border-color: #888888;
    background-color: #383838;
}

QCheckBox::indicator:checked {
    background-color: #3a7bd5;
    border-color: #3a7bd5;
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'></polyline></svg>");
}


QTextEdit {
    background-color: #141414;
    color: #ffffff;
    border: 1px solid #3c3c3c;
    border-radius: 5px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
}
"""
