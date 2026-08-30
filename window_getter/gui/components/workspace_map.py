"""
Interactive 2D Desktop Workspace Map Visualizer with Grid Layout and Context Menu for PyQt6 GUI.
"""

import math
from typing import List, Dict, Optional
from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QMouseEvent, QContextMenuEvent
from PyQt6.QtCore import Qt, QRectF, QPoint, pyqtSignal
from window_getter.core.models import WindowInfo


class WorkspaceVisualizer(QWidget):
    windowClicked = pyqtSignal(str)
    focusRequested = pyqtSignal(str)
    ruleRequested = pyqtSignal(str)
    relaunchRequested = pyqtSignal(str)
    inspectProcessRequested = pyqtSignal(int)
    closeRequested = pyqtSignal(str)
    killRequested = pyqtSignal(int)
    windowSelected = pyqtSignal(object)
    workspaceSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.windows: List[WindowInfo] = []
        self.target_workspace: str = "All"
        self._rect_map: Dict[str, QRectF] = {}
        self._ws_tab_map: Dict[str, QRectF] = {}
        self.setMinimumHeight(420)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 6px;")

    def update_windows(self, windows: List[WindowInfo], target_workspace: str = "All"):
        self.windows = windows
        self.target_workspace = str(target_workspace)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw dark canvas background
        painter.fillRect(self.rect(), QColor("#1a1a1a"))

        # Extract all available workspace names from windows
        all_ws = sorted(list(set([str(w.workspace_name or w.workspace_id) for w in self.windows])))
        ws_options = ["All"] + all_ws

        # 1. Draw Workspace Selection Tabs Bar at Top
        self._ws_tab_map.clear()
        tab_x = 20
        tab_y = 14
        tab_h = 28
        painter.setFont(QFont("Inter", 9, QFont.Weight.Bold))

        for ws_name in ws_options:
            label = f" Workspace {ws_name} " if ws_name != "All" else " All Workspaces "
            font_metrics = painter.fontMetrics()
            tw = font_metrics.horizontalAdvance(label) + 16

            tab_rect = QRectF(tab_x, tab_y, tw, tab_h)
            self._ws_tab_map[ws_name] = tab_rect

            is_selected = (self.target_workspace == ws_name)
            if is_selected:
                bg = QColor("#454545")
                border = QColor("#ffffff")
                txt_col = QColor("#ffffff")
            else:
                bg = QColor("#2d2d2d")
                border = QColor("#3c3c3c")
                txt_col = QColor("#aaaaaa")

            painter.setPen(QPen(border, 1))
            painter.setBrush(QBrush(bg))
            painter.drawRoundedRect(tab_rect, 4, 4)

            painter.setPen(txt_col)
            painter.drawText(tab_rect, Qt.AlignmentFlag.AlignCenter, label)

            tab_x += tw + 8

        self._rect_map.clear()
        top_margin = 54

        if not self.windows:
            painter.setPen(QColor("#aaaaaa"))
            painter.setFont(QFont("Inter", 12))
            rect_empty = QRectF(0, top_margin, self.width(), self.height() - top_margin)
            painter.drawText(rect_empty, Qt.AlignmentFlag.AlignCenter, "No active windows")
            return

        # 2. Render Single Workspace vs All Workspaces Grid
        if self.target_workspace != "All":
            displayed_windows = [w for w in self.windows if str(w.workspace_name or w.workspace_id) == self.target_workspace]
            self._render_single_workspace(painter, displayed_windows, self.target_workspace, top_margin)
        else:
            self._render_all_workspaces_grid(painter, all_ws, top_margin)

    def _render_single_workspace(self, painter: QPainter, windows: List[WindowInfo], ws_name: str, top_margin: float):
        if not windows:
            painter.setPen(QColor("#aaaaaa"))
            painter.setFont(QFont("Inter", 12))
            rect_empty = QRectF(0, top_margin, self.width(), self.height() - top_margin)
            painter.drawText(rect_empty, Qt.AlignmentFlag.AlignCenter, f"No windows on Workspace {ws_name}")
            return

        max_x = max([w.x + w.width for w in windows] + [1920])
        max_y = max([w.y + w.height for w in windows] + [1080])

        canvas_w = self.width() - 40
        canvas_h = self.height() - top_margin - 20

        scale_x = canvas_w / max(max_x, 1)
        scale_y = canvas_h / max(max_y, 1)
        scale = min(scale_x, scale_y)

        offset_x = (self.width() - (max_x * scale)) / 2
        offset_y = top_margin + ((canvas_h - (max_y * scale)) / 2)

        # Draw Monitor Border Frame
        monitor_rect = QRectF(offset_x, offset_y, max_x * scale, max_y * scale)
        painter.setPen(QPen(QColor("#444444"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor("#252526")))
        painter.drawRoundedRect(monitor_rect, 6, 6)

        # Draw Window Rectangles
        for w in windows:
            self._draw_window_rect(painter, w, offset_x, offset_y, scale)

    def _render_all_workspaces_grid(self, painter: QPainter, ws_list: List[str], top_margin: float):
        if not ws_list:
            return

        num_ws = len(ws_list)
        cols = 2 if num_ws <= 4 else 3
        rows = math.ceil(num_ws / cols)

        grid_x = 20
        grid_y = top_margin
        grid_w = self.width() - 40
        grid_h = self.height() - top_margin - 20

        gap = 16
        cell_w = (grid_w - (gap * (cols - 1))) / cols
        cell_h = (grid_h - (gap * (rows - 1))) / rows

        for idx, ws_name in enumerate(ws_list):
            r = idx // cols
            c = idx % cols

            cx = grid_x + c * (cell_w + gap)
            cy = grid_y + r * (cell_h + gap)

            cell_rect = QRectF(cx, cy, cell_w, cell_h)

            # Draw Cell Frame
            painter.setPen(QPen(QColor("#3c3c3c"), 1))
            painter.setBrush(QBrush(QColor("#252526")))
            painter.drawRoundedRect(cell_rect, 6, 6)

            # Draw Cell Header Label
            header_rect = QRectF(cx + 8, cy + 6, cell_w - 16, 20)
            painter.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(header_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"Workspace {ws_name}")

            ws_windows = [w for w in self.windows if str(w.workspace_name or w.workspace_id) == ws_name]
            if not ws_windows:
                empty_rect = QRectF(cx, cy + 26, cell_w, cell_h - 26)
                painter.setFont(QFont("Inter", 9))
                painter.setPen(QColor("#888888"))
                painter.drawText(empty_rect, Qt.AlignmentFlag.AlignCenter, "Empty Workspace")
                continue

            # Compute scale inside cell
            inner_x = cx + 8
            inner_y = cy + 28
            inner_w = cell_w - 16
            inner_h = cell_h - 36

            max_x = max([w.x + w.width for w in ws_windows] + [1920])
            max_y = max([w.y + w.height for w in ws_windows] + [1080])

            scale_x = inner_w / max(max_x, 1)
            scale_y = inner_h / max(max_y, 1)
            scale = min(scale_x, scale_y)

            offset_x = inner_x + ((inner_w - (max_x * scale)) / 2)
            offset_y = inner_y + ((inner_h - (max_y * scale)) / 2)

            for w in ws_windows:
                self._draw_window_rect(painter, w, offset_x, offset_y, scale)

    def _draw_window_rect(self, painter: QPainter, w: WindowInfo, offset_x: float, offset_y: float, scale: float):
        rx = offset_x + (w.x * scale)
        ry = offset_y + (w.y * scale)
        rw = max(w.width * scale, 24)
        rh = max(w.height * scale, 18)

        win_rect = QRectF(rx, ry, rw, rh)
        self._rect_map[w.address] = win_rect

        if w.is_active:
            bg_color = QColor("#454545")
            border_color = QColor("#ffffff")
            border_width = 2
        else:
            bg_color = QColor("#2d2d2d")
            border_color = QColor("#555555")
            border_width = 1

        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(win_rect, 4, 4)

        if rw > 40 and rh > 20:
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            label = f"{w.display_app_id}"
            painter.drawText(
                win_rect.adjusted(4, 2, -4, -2),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                label
            )

    def _get_window_at_pos(self, pos) -> Optional[WindowInfo]:
        px = pos.x() if hasattr(pos, "x") else pos[0]
        py = pos.y() if hasattr(pos, "y") else pos[1]
        for addr, rect in self._rect_map.items():
            if rect.contains(px, py):
                return next((w for w in self.windows if w.address == addr), None)
        return None

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()

        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicked a workspace tab
            for ws_name, rect in self._ws_tab_map.items():
                if rect.contains(pos):
                    self.target_workspace = ws_name
                    self.workspaceSelected.emit(ws_name)
                    self.update()
                    return

            # Check if clicked a window
            win = self._get_window_at_pos(pos)
            if win:
                self.windowSelected.emit(win)
                self.windowClicked.emit(win.address)
                self.focusRequested.emit(win.address)

        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent):
        win = self._get_window_at_pos(event.pos())
        if not win:
            return

        self.windowSelected.emit(win)
        self._show_context_menu(win, event.globalPos())

    def _show_context_menu(self, win: WindowInfo, global_pos: QPoint):
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

        action = menu.exec(global_pos)
        if not action:
            return

        if action == act_focus:
            self.focusRequested.emit(win.address)
            self.windowClicked.emit(win.address)
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
