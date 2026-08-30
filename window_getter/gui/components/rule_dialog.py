"""
Comprehensive Create Rule Modal Dialog for PyQt6 GUI with Full Hyprland & i3 Window Rule Specs.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QComboBox, QCheckBox, QLineEdit, QGroupBox, QGridLayout, QApplication,
    QSplitter, QWidget, QTabWidget
)
from PyQt6.QtCore import Qt
from window_getter.core.models import WindowInfo
from window_getter.core.rules import RuleGenerator


class RuleGeneratorDialog(QDialog):
    def __init__(self, win: WindowInfo, parent=None):
        super().__init__(parent)
        self.win = win
        self.setWindowTitle(f"Create Rule - {win.display_app_id}")
        self.setMinimumSize(960, 680)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header
        header = QLabel(f"Create Custom Window Rule: {self.win.display_title}")
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        main_layout.addWidget(header)

        # Splitter Layout (Left Form Controls, Right Live Code Preview)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Container (Form with Tabs)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(10)

        # Syntax Selector
        syn_layout = QHBoxLayout()
        syn_lbl = QLabel("Format:")
        syn_lbl.setStyleSheet("font-weight: 600; color: #cccccc; font-size: 12px;")
        
        self.syntax_combo = QComboBox()
        self.syntax_combo.addItem("Hyprland (Lua Config)", "hyprland_lua")
        self.syntax_combo.addItem("Hyprland (Classic windowrulev2)", "hyprland_conf")
        self.syntax_combo.addItem("Niri (KDL window-rule)", "niri")
        self.syntax_combo.addItem("KDE Plasma (kwinrulesrc)", "kwin")
        self.syntax_combo.addItem("Sway / i3 (for_window)", "sway")
        self.syntax_combo.currentIndexChanged.connect(self._rebuild_preview)

        syn_layout.addWidget(syn_lbl)
        syn_layout.addWidget(self.syntax_combo, 1)
        left_layout.addLayout(syn_layout)

        # Match Criteria Group
        match_box = QGroupBox("Match Criteria")
        match_grid = QGridLayout(match_box)
        match_grid.setContentsMargins(10, 10, 10, 10)
        match_grid.setSpacing(8)

        self.cb_match_class = QCheckBox("Match App ID / Class:")
        self.cb_match_class.setChecked(True)
        self.cb_match_class.toggled.connect(self._rebuild_preview)
        self.input_match_class = QLineEdit(self.win.display_app_id)
        self.input_match_class.textChanged.connect(self._rebuild_preview)

        self.cb_match_title = QCheckBox("Match Window Title:")
        self.cb_match_title.setChecked(False)
        self.cb_match_title.toggled.connect(self._rebuild_preview)
        self.input_match_title = QLineEdit(self.win.display_title)
        self.input_match_title.textChanged.connect(self._rebuild_preview)

        self.cb_match_init_class = QCheckBox("Match Initial Class:")
        self.cb_match_init_class.toggled.connect(self._rebuild_preview)
        self.input_match_init_class = QLineEdit(self.win.initial_class or self.win.display_app_id)
        self.input_match_init_class.textChanged.connect(self._rebuild_preview)

        self.cb_match_tag = QCheckBox("Match Tag:")
        self.cb_match_tag.toggled.connect(self._rebuild_preview)
        self.input_match_tag = QLineEdit("games")
        self.input_match_tag.setMinimumWidth(80)
        self.input_match_tag.textChanged.connect(self._rebuild_preview)

        match_grid.addWidget(self.cb_match_class, 0, 0)
        match_grid.addWidget(self.input_match_class, 0, 1)
        match_grid.addWidget(self.cb_match_title, 1, 0)
        match_grid.addWidget(self.input_match_title, 1, 1)
        match_grid.addWidget(self.cb_match_init_class, 2, 0)
        match_grid.addWidget(self.input_match_init_class, 2, 1)
        match_grid.addWidget(self.cb_match_tag, 3, 0)
        match_grid.addWidget(self.input_match_tag, 3, 1)

        left_layout.addWidget(match_box)

        # Category Tab Widget for Window Properties
        prop_tabs = QTabWidget()

        # ----------------------------------------------------
        # Tab 1: Layout & Geometry
        # ----------------------------------------------------
        layout_tab = QWidget()
        lay_v = QVBoxLayout(layout_tab)
        lay_v.setContentsMargins(10, 10, 10, 10)
        lay_v.setSpacing(8)

        self.cb_float = QCheckBox("Float Window")
        self.cb_float.setChecked(True)
        self.cb_float.toggled.connect(self._rebuild_preview)

        self.cb_tile = QCheckBox("Force Tile Window")
        self.cb_tile.toggled.connect(self._rebuild_preview)

        self.cb_workspace = QCheckBox("Launch on Workspace:")
        self.cb_workspace.toggled.connect(self._rebuild_preview)
        self.input_workspace = QLineEdit(str(self.win.workspace_name or "1"))
        self.input_workspace.setMinimumWidth(60)
        self.input_workspace.setMaximumWidth(80)
        self.input_workspace.textChanged.connect(self._rebuild_preview)
        self.cb_workspace_silent = QCheckBox("Silent (Don't switch focus to workspace)")
        self.cb_workspace_silent.toggled.connect(self._rebuild_preview)

        self.cb_size = QCheckBox("Initial Size on Launch (W×H):")
        self.cb_size.setToolTip("Sets starting dimensions for floating window on launch (window remains freely resizable)")
        self.cb_size.toggled.connect(self._rebuild_preview)
        self.input_width = QLineEdit(str(self.win.width or 1200))
        self.input_width.setMinimumWidth(65)
        self.input_width.setMaximumWidth(80)
        self.input_width.textChanged.connect(self._rebuild_preview)
        self.input_height = QLineEdit(str(self.win.height or 800))
        self.input_height.setMinimumWidth(65)
        self.input_height.setMaximumWidth(80)
        self.input_height.textChanged.connect(self._rebuild_preview)

        self.cb_min_size = QCheckBox("Minimum Size (W×H):")
        self.cb_min_size.toggled.connect(self._rebuild_preview)
        self.input_min_w = QLineEdit("400")
        self.input_min_w.setMinimumWidth(60)
        self.input_min_w.setMaximumWidth(75)
        self.input_min_w.textChanged.connect(self._rebuild_preview)
        self.input_min_h = QLineEdit("300")
        self.input_min_h.setMinimumWidth(60)
        self.input_min_h.setMaximumWidth(75)
        self.input_min_h.textChanged.connect(self._rebuild_preview)

        self.cb_max_size = QCheckBox("Maximum Size (W×H):")
        self.cb_max_size.toggled.connect(self._rebuild_preview)
        self.input_max_w = QLineEdit("1920")
        self.input_max_w.setMinimumWidth(60)
        self.input_max_w.setMaximumWidth(75)
        self.input_max_w.textChanged.connect(self._rebuild_preview)
        self.input_max_h = QLineEdit("1080")
        self.input_max_h.setMinimumWidth(60)
        self.input_max_h.setMaximumWidth(75)
        self.input_max_h.textChanged.connect(self._rebuild_preview)

        self.cb_move = QCheckBox("Initial Position on Launch (X, Y):")
        self.cb_move.setToolTip("Sets starting screen coordinates when window is launched")
        self.cb_move.toggled.connect(self._rebuild_preview)

        self.input_x = QLineEdit(str(self.win.x or 100))
        self.input_x.setMinimumWidth(65)
        self.input_x.setMaximumWidth(80)
        self.input_x.textChanged.connect(self._rebuild_preview)
        self.input_y = QLineEdit(str(self.win.y or 100))
        self.input_y.setMinimumWidth(65)
        self.input_y.setMaximumWidth(80)
        self.input_y.textChanged.connect(self._rebuild_preview)

        self.cb_center = QCheckBox("Center Window on Screen")
        self.cb_center.toggled.connect(self._rebuild_preview)

        self.cb_pin = QCheckBox("Pin Window (Sticky across workspaces)")
        self.cb_pin.toggled.connect(self._rebuild_preview)

        lay_v.addWidget(self.cb_float)
        lay_v.addWidget(self.cb_tile)

        ws_row = QHBoxLayout()
        ws_row.addWidget(self.cb_workspace)
        ws_row.addWidget(self.input_workspace)
        ws_row.addWidget(self.cb_workspace_silent)
        ws_row.addStretch()
        lay_v.addLayout(ws_row)

        sz_row = QHBoxLayout()
        sz_row.addWidget(self.cb_size)
        sz_row.addWidget(self.input_width)
        sz_row.addWidget(QLabel("×"))
        sz_row.addWidget(self.input_height)
        sz_row.addStretch()
        lay_v.addLayout(sz_row)

        min_sz_row = QHBoxLayout()
        min_sz_row.addWidget(self.cb_min_size)
        min_sz_row.addWidget(self.input_min_w)
        min_sz_row.addWidget(QLabel("×"))
        min_sz_row.addWidget(self.input_min_h)
        min_sz_row.addStretch()
        lay_v.addLayout(min_sz_row)

        max_sz_row = QHBoxLayout()
        max_sz_row.addWidget(self.cb_max_size)
        max_sz_row.addWidget(self.input_max_w)
        max_sz_row.addWidget(QLabel("×"))
        max_sz_row.addWidget(self.input_max_h)
        max_sz_row.addStretch()
        lay_v.addLayout(max_sz_row)

        pos_row = QHBoxLayout()
        pos_row.addWidget(self.cb_move)
        pos_row.addWidget(self.input_x)
        pos_row.addWidget(QLabel(","))
        pos_row.addWidget(self.input_y)
        pos_row.addStretch()
        lay_v.addLayout(pos_row)

        lay_v.addWidget(self.cb_center)
        lay_v.addWidget(self.cb_pin)
        lay_v.addStretch()

        prop_tabs.addTab(layout_tab, "Layout & Geometry")

        # ----------------------------------------------------
        # Tab 2: Appearance & Styling
        # ----------------------------------------------------
        app_tab = QWidget()
        app_v = QVBoxLayout(app_tab)
        app_v.setContentsMargins(10, 10, 10, 10)
        app_v.setSpacing(8)

        self.cb_opacity = QCheckBox("Custom Opacity (Active / Inactive):")
        self.cb_opacity.toggled.connect(self._rebuild_preview)
        self.input_opacity_act = QLineEdit("0.95")
        self.input_opacity_act.setMinimumWidth(55)
        self.input_opacity_act.setMaximumWidth(70)
        self.input_opacity_act.textChanged.connect(self._rebuild_preview)
        self.input_opacity_inact = QLineEdit("0.90")
        self.input_opacity_inact.setMinimumWidth(55)
        self.input_opacity_inact.setMaximumWidth(70)
        self.input_opacity_inact.textChanged.connect(self._rebuild_preview)

        self.cb_opaque = QCheckBox("Force 100% Opaque (opaque = true)")
        self.cb_opaque.toggled.connect(self._rebuild_preview)

        self.cb_rounding = QCheckBox("Custom Corner Rounding Radius:")
        self.cb_rounding.toggled.connect(self._rebuild_preview)
        self.input_rounding = QLineEdit("10")
        self.input_rounding.setMinimumWidth(55)
        self.input_rounding.setMaximumWidth(70)
        self.input_rounding.textChanged.connect(self._rebuild_preview)

        self.cb_bordercolor = QCheckBox("Custom Border Color:")
        self.cb_bordercolor.toggled.connect(self._rebuild_preview)
        self.input_bordercolor = QLineEdit("rgb(ff5555)")
        self.input_bordercolor.setMinimumWidth(110)
        self.input_bordercolor.setMaximumWidth(140)
        self.input_bordercolor.textChanged.connect(self._rebuild_preview)

        self.cb_disable_blur = QCheckBox("Disable Background Blur (noblur)")
        self.cb_disable_blur.toggled.connect(self._rebuild_preview)

        self.cb_disable_border = QCheckBox("Disable Window Border (noborder)")
        self.cb_disable_border.toggled.connect(self._rebuild_preview)

        self.cb_disable_shadow = QCheckBox("Disable Drop Shadow (noshadow)")
        self.cb_disable_shadow.toggled.connect(self._rebuild_preview)

        self.cb_disable_anim = QCheckBox("Disable Window Animations (noanim)")
        self.cb_disable_anim.toggled.connect(self._rebuild_preview)

        self.cb_dim_around = QCheckBox("Dim Surrounding Desktop (dimaround)")
        self.cb_dim_around.toggled.connect(self._rebuild_preview)

        op_row = QHBoxLayout()
        op_row.addWidget(self.cb_opacity)
        op_row.addWidget(self.input_opacity_act)
        op_row.addWidget(QLabel("/"))
        op_row.addWidget(self.input_opacity_inact)
        op_row.addStretch()
        app_v.addLayout(op_row)

        app_v.addWidget(self.cb_opaque)

        rnd_row = QHBoxLayout()
        rnd_row.addWidget(self.cb_rounding)
        rnd_row.addWidget(self.input_rounding)
        rnd_row.addStretch()
        app_v.addLayout(rnd_row)

        col_row = QHBoxLayout()
        col_row.addWidget(self.cb_bordercolor)
        col_row.addWidget(self.input_bordercolor)
        col_row.addStretch()
        app_v.addLayout(col_row)

        app_v.addWidget(self.cb_disable_blur)
        app_v.addWidget(self.cb_disable_border)
        app_v.addWidget(self.cb_disable_shadow)
        app_v.addWidget(self.cb_disable_anim)
        app_v.addWidget(self.cb_dim_around)
        app_v.addStretch()

        prop_tabs.addTab(app_tab, "Appearance")

        # ----------------------------------------------------
        # Tab 3: Behavior & Focus
        # ----------------------------------------------------
        beh_tab = QWidget()
        beh_v = QVBoxLayout(beh_tab)
        beh_v.setContentsMargins(10, 10, 10, 10)
        beh_v.setSpacing(8)

        self.cb_fullscreen = QCheckBox("Fullscreen Mode")
        self.cb_fullscreen.toggled.connect(self._rebuild_preview)

        self.cb_maximize = QCheckBox("Maximize Window")
        self.cb_maximize.toggled.connect(self._rebuild_preview)

        self.cb_idle = QCheckBox("Idle Inhibit Mode:")
        self.cb_idle.toggled.connect(self._rebuild_preview)
        self.combo_idle = QComboBox()
        self.combo_idle.addItem("When Focused (focus)", "focus")
        self.combo_idle.addItem("When Fullscreen (fullscreen)", "fullscreen")
        self.combo_idle.addItem("Always while Open (always)", "always")
        self.combo_idle.currentIndexChanged.connect(self._rebuild_preview)

        self.cb_max_fps = QCheckBox("Limit Window Max FPS:")
        self.cb_max_fps.toggled.connect(self._rebuild_preview)
        self.input_max_fps = QLineEdit("60")
        self.input_max_fps.setMinimumWidth(60)
        self.input_max_fps.setMaximumWidth(75)
        self.input_max_fps.textChanged.connect(self._rebuild_preview)

        self.cb_enable_render_unfocused = QCheckBox("Enable Render when Unfocused (render_unfocused = true)")
        self.cb_enable_render_unfocused.toggled.connect(self._rebuild_preview)

        self.cb_no_focus = QCheckBox("Launch Silently (No initial focus)")
        self.cb_no_focus.toggled.connect(self._rebuild_preview)

        self.cb_stay_focused = QCheckBox("Force Stay Focused (stayfocused)")
        self.cb_stay_focused.toggled.connect(self._rebuild_preview)

        self.cb_focus_on_activate = QCheckBox("Focus on Activation Request (focus_on_activate)")
        self.cb_focus_on_activate.toggled.connect(self._rebuild_preview)

        self.cb_suppress_max = QCheckBox("Suppress Maximize Events")
        self.cb_suppress_max.toggled.connect(self._rebuild_preview)

        self.cb_group = QCheckBox("Add to Window Group:")
        self.cb_group.toggled.connect(self._rebuild_preview)
        self.combo_group = QComboBox()
        self.combo_group.addItem("new", "new")
        self.combo_group.addItem("set", "set")
        self.combo_group.addItem("lock", "lock")
        self.combo_group.currentIndexChanged.connect(self._rebuild_preview)

        self.cb_set_tag = QCheckBox("Assign Window Tag:")
        self.cb_set_tag.toggled.connect(self._rebuild_preview)
        self.input_set_tag = QLineEdit("media")
        self.input_set_tag.setMinimumWidth(80)
        self.input_set_tag.setMaximumWidth(110)
        self.input_set_tag.textChanged.connect(self._rebuild_preview)

        idle_row = QHBoxLayout()
        idle_row.addWidget(self.cb_idle)
        idle_row.addWidget(self.combo_idle)
        idle_row.addStretch()

        fps_row = QHBoxLayout()
        fps_row.addWidget(self.cb_max_fps)
        fps_row.addWidget(self.input_max_fps)
        fps_row.addStretch()

        grp_row = QHBoxLayout()
        grp_row.addWidget(self.cb_group)
        grp_row.addWidget(self.combo_group)
        grp_row.addStretch()

        tag_row = QHBoxLayout()
        tag_row.addWidget(self.cb_set_tag)
        tag_row.addWidget(self.input_set_tag)
        tag_row.addStretch()

        beh_v.addWidget(self.cb_fullscreen)
        beh_v.addWidget(self.cb_maximize)
        beh_v.addLayout(idle_row)
        beh_v.addLayout(fps_row)
        beh_v.addWidget(self.cb_enable_render_unfocused)
        beh_v.addWidget(self.cb_no_focus)
        beh_v.addWidget(self.cb_stay_focused)
        beh_v.addWidget(self.cb_focus_on_activate)
        beh_v.addWidget(self.cb_suppress_max)
        beh_v.addLayout(grp_row)
        beh_v.addLayout(tag_row)
        beh_v.addStretch()

        prop_tabs.addTab(beh_tab, "Behavior")

        left_layout.addWidget(prop_tabs, 1)

        # Right Container (Live Code Preview)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)

        prev_lbl = QLabel("Generated Code Preview:")
        prev_lbl.setStyleSheet("font-weight: 600; color: #cccccc; font-size: 12px;")
        right_layout.addWidget(prev_lbl)

        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(False)
        right_layout.addWidget(self.code_preview)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 440])

        main_layout.addWidget(splitter, 1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setObjectName("primaryBtn")
        copy_btn.clicked.connect(self._copy_code)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(close_btn)

        main_layout.addLayout(btn_layout)

        self._rebuild_preview()

    def _rebuild_preview(self):
        syntax = self.syntax_combo.currentData() or "hyprland_lua"

        def _safe_int(txt: str, default: int) -> int:
            return int(txt) if txt.strip().isdigit() else default

        def _safe_float(txt: str, default: float) -> float:
            try:
                return float(txt)
            except Exception:
                return default

        custom_win = WindowInfo(
            address=self.win.address,
            app_id=self.input_match_class.text().strip() or self.win.display_app_id,
            title=self.input_match_title.text().strip() or self.win.display_title,
            pid=self.win.pid,
            workspace_name=self.win.workspace_name,
            initial_class=self.input_match_init_class.text().strip() or self.win.initial_class,
            initial_title=self.win.initial_title
        )

        snippet = RuleGenerator.build_custom_rule(
            win=custom_win,
            syntax=syntax,
            match_class=self.cb_match_class.isChecked(),
            match_title=self.cb_match_title.isChecked(),
            match_initial_class=self.cb_match_init_class.isChecked(),
            match_tag=self.cb_match_tag.isChecked(),
            tag_match_val=self.input_match_tag.text().strip(),
            float_win=self.cb_float.isChecked(),
            tile_win=self.cb_tile.isChecked(),
            launch_workspace=self.cb_workspace.isChecked(),
            workspace_val=self.input_workspace.text().strip() or "1",
            workspace_silent=self.cb_workspace_silent.isChecked(),
            fixed_size=self.cb_size.isChecked(),
            width_val=_safe_int(self.input_width.text(), 1200),
            height_val=_safe_int(self.input_height.text(), 800),
            min_size_rule=self.cb_min_size.isChecked(),
            min_w=_safe_int(self.input_min_w.text(), 400),
            min_h=_safe_int(self.input_min_h.text(), 300),
            max_size_rule=self.cb_max_size.isChecked(),
            max_w=_safe_int(self.input_max_w.text(), 1920),
            max_h=_safe_int(self.input_max_h.text(), 1080),
            center_win=self.cb_center.isChecked(),
            fixed_pos=self.cb_move.isChecked(),
            x_val=_safe_int(self.input_x.text(), 100),
            y_val=_safe_int(self.input_y.text(), 100),
            pin_win=self.cb_pin.isChecked(),
            opacity_win=self.cb_opacity.isChecked(),
            active_opacity=_safe_float(self.input_opacity_act.text(), 0.95),
            inactive_opacity=_safe_float(self.input_opacity_inact.text(), 0.90),
            opaque_win=self.cb_opaque.isChecked(),
            fullscreen_win=self.cb_fullscreen.isChecked(),
            maximize_win=self.cb_maximize.isChecked(),
            idle_inhibit=self.cb_idle.isChecked(),
            idle_inhibit_mode=self.combo_idle.currentData() or "focus",
            max_fps_rule=self.cb_max_fps.isChecked(),
            max_fps_val=_safe_int(self.input_max_fps.text(), 60),
            enable_render_unfocused=self.cb_enable_render_unfocused.isChecked(),
            no_focus=self.cb_no_focus.isChecked(),
            stay_focused=self.cb_stay_focused.isChecked(),
            focus_on_activate=self.cb_focus_on_activate.isChecked(),
            disable_blur=self.cb_disable_blur.isChecked(),
            disable_border=self.cb_disable_border.isChecked(),
            disable_shadow=self.cb_disable_shadow.isChecked(),
            disable_anim=self.cb_disable_anim.isChecked(),
            dim_around=self.cb_dim_around.isChecked(),
            custom_rounding=self.cb_rounding.isChecked(),
            rounding_val=_safe_int(self.input_rounding.text(), 10),
            custom_bordercolor=self.cb_bordercolor.isChecked(),
            bordercolor_val=self.input_bordercolor.text().strip(),
            suppress_max=self.cb_suppress_max.isChecked(),
            group_rule=self.cb_group.isChecked(),
            group_val=self.combo_group.currentData() or "new",
            set_tag_rule=self.cb_set_tag.isChecked(),
            set_tag_val=self.input_set_tag.text().strip()
        )

        self.code_preview.setText(snippet)

    def _copy_code(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.code_preview.toPlainText())
