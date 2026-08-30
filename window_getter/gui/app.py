"""
PyQt6 Application launcher entrypoint for window-getter.
"""

import sys
from PyQt6.QtWidgets import QApplication
from window_getter.gui.main_window import MainWindow


def run_gui():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    app.setApplicationName("window-getter")
    main_win = MainWindow()
    main_win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())
