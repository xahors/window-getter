"""
Window rule generator module supporting Hyprland Lua, Hyprland Classic, and Sway/i3 formats.
"""

from typing import Dict, List, Optional, Any
from window_getter.core.models import WindowInfo


class RuleGenerator:
    @staticmethod
    def build_custom_rule(
        win: WindowInfo,
        syntax: str = "hyprland_lua",
        match_class: bool = True,
        match_title: bool = False,
        match_initial_class: bool = False,
        match_initial_title: bool = False,
        match_tag: bool = False,
        tag_match_val: str = "games",
        float_win: bool = True,
        tile_win: bool = False,
        launch_workspace: bool = False,
        workspace_val: str = "1",
        workspace_silent: bool = False,
        fixed_size: bool = False,
        width_val: int = 1200,
        height_val: int = 800,
        min_size_rule: bool = False,
        min_w: int = 400,
        min_h: int = 300,
        max_size_rule: bool = False,
        max_w: int = 1920,
        max_h: int = 1080,
        center_win: bool = False,
        fixed_pos: bool = False,
        x_val: int = 100,
        y_val: int = 100,
        pin_win: bool = False,
        opacity_win: bool = False,
        active_opacity: float = 0.95,
        inactive_opacity: float = 0.90,
        opaque_win: bool = False,
        fullscreen_win: bool = False,
        maximize_win: bool = False,
        idle_inhibit: bool = False,
        idle_inhibit_mode: str = "focus",
        max_fps_rule: bool = False,
        max_fps_val: int = 60,
        enable_render_unfocused: bool = False,
        no_focus: bool = False,
        stay_focused: bool = False,
        focus_on_activate: bool = False,
        disable_blur: bool = False,
        disable_border: bool = False,
        disable_shadow: bool = False,
        disable_anim: bool = False,
        dim_around: bool = False,
        custom_rounding: bool = False,
        rounding_val: int = 10,
        custom_bordercolor: bool = False,
        bordercolor_val: str = "rgb(ff5555)",
        suppress_max: bool = False,
        group_rule: bool = False,
        group_val: str = "new",
        set_tag_rule: bool = False,
        set_tag_val: str = "media"
    ) -> str:
        """
        Builds a comprehensive customized window rule snippet based on Hyprland & Sway spec.
        """
        app = win.display_app_id
        app_pattern = f"^({app})$" if app else ".*"
        title_pattern = f"^({win.title})$" if win.title else ".*"
        init_class_pattern = f"^({win.initial_class})$" if win.initial_class else app_pattern

        if syntax == "hyprland_lua":
            # Hyprland Lua config format
            match_parts = []
            if match_class and app:
                match_parts.append(f'class = "{app_pattern}"')
            if match_title and win.title:
                match_parts.append(f'title = "{title_pattern}"')
            if match_initial_class and win.initial_class:
                match_parts.append(f'initial_class = "{init_class_pattern}"')
            if match_initial_title and win.initial_title:
                match_parts.append(f'initial_title = "^({win.initial_title})$"')
            if match_tag and tag_match_val:
                match_parts.append(f'tag = "{tag_match_val.strip()}"')
            
            match_str = ", ".join(match_parts) if match_parts else f'class = "{app_pattern}"'

            props = []
            if float_win:
                props.append("float = true")
            elif tile_win:
                props.append("tile = true")

            if launch_workspace and workspace_val:
                if workspace_silent:
                    props.append(f'workspace_silent = "{workspace_val}"')
                else:
                    props.append(f'workspace = "{workspace_val}"')

            if fixed_size and width_val > 0 and height_val > 0:
                props.append(f'size = {{ {width_val}, {height_val} }}')
            if min_size_rule and min_w > 0 and min_h > 0:
                props.append(f'min_size = {{ {min_w}, {min_h} }}')
            if max_size_rule and max_w > 0 and max_h > 0:
                props.append(f'max_size = {{ {max_w}, {max_h} }}')

            if fixed_pos:
                props.append(f'move = {{ {x_val}, {y_val} }}')
            if center_win:
                props.append("center = true")
            if pin_win:
                props.append("pin = true")

            if opaque_win:
                props.append("opaque = true")
            elif opacity_win:
                props.append(f'opacity = {{ {active_opacity}, {inactive_opacity} }}')

            if fullscreen_win:
                props.append("fullscreen = true")
            if maximize_win:
                props.append("maximize = true")
            if idle_inhibit and idle_inhibit_mode != "none":
                props.append(f'idle_inhibit = "{idle_inhibit_mode}"')
            if max_fps_rule and max_fps_val > 0:
                props.append(f"max_fps = {max_fps_val}")
            if enable_render_unfocused:
                props.append("render_unfocused = true")
            if no_focus:
                props.append("no_initial_focus = true")
            if stay_focused:
                props.append("stayfocused = true")
            if focus_on_activate:
                props.append("focus_on_activate = true")

            if disable_blur:
                props.append("blur = false")
            if disable_border:
                props.append("border = false")
            if disable_shadow:
                props.append("shadow = false")
            if disable_anim:
                props.append("animation = false")
            if dim_around:
                props.append("dim_around = true")
            if custom_rounding and rounding_val >= 0:
                props.append(f"rounding = {rounding_val}")
            if custom_bordercolor and bordercolor_val.strip():
                props.append(f'bordercolor = "{bordercolor_val.strip()}"')
            if suppress_max:
                props.append('suppressevent = "maximize"')
            if group_rule and group_val:
                props.append(f'group = "{group_val}"')
            if set_tag_rule and set_tag_val.strip():
                props.append(f'tag = "+{set_tag_val.strip()}"')

            lines = [
                f"-- Window Rule for {win.display_title}",
                "hl.window_rule({",
                f"    match = {{ {match_str} }},",
            ]

            for p in props:
                lines.append(f"    {p},")
            lines.append("})")
            return "\n".join(lines)

        elif syntax == "hyprland_conf":
            # Hyprland Classic windowrulev2 format
            match_opts = []
            if match_class and app:
                match_opts.append(f"class:{app_pattern}")
            if match_title and win.title:
                match_opts.append(f"title:{title_pattern}")
            if match_initial_class and win.initial_class:
                match_opts.append(f"initialClass:{init_class_pattern}")
            if match_initial_title and win.initial_title:
                match_opts.append(f"initialTitle:^({win.initial_title})$")
            if match_tag and tag_match_val:
                match_opts.append(f"tag:{tag_match_val.strip()}")

            if not match_opts:
                match_opts.append(f"class:{app_pattern}")

            match_clause = ", ".join(match_opts)

            rule_lines = []
            if float_win:
                rule_lines.append(f"windowrulev2 = float, {match_clause}")
            elif tile_win:
                rule_lines.append(f"windowrulev2 = tile, {match_clause}")

            if launch_workspace and workspace_val:
                if workspace_silent:
                    rule_lines.append(f"windowrulev2 = workspace {workspace_val} silent, {match_clause}")
                else:
                    rule_lines.append(f"windowrulev2 = workspace {workspace_val}, {match_clause}")

            if fixed_size and width_val > 0 and height_val > 0:
                rule_lines.append(f"windowrulev2 = size {width_val} {height_val}, {match_clause}")
            if min_size_rule and min_w > 0 and min_h > 0:
                rule_lines.append(f"windowrulev2 = minsize {min_w} {min_h}, {match_clause}")
            if max_size_rule and max_w > 0 and max_h > 0:
                rule_lines.append(f"windowrulev2 = maxsize {max_w} {max_h}, {match_clause}")

            if fixed_pos:
                rule_lines.append(f"windowrulev2 = move {x_val} {y_val}, {match_clause}")
            if center_win:
                rule_lines.append(f"windowrulev2 = center, {match_clause}")
            if pin_win:
                rule_lines.append(f"windowrulev2 = pin, {match_clause}")

            if opaque_win:
                rule_lines.append(f"windowrulev2 = opaque, {match_clause}")
            elif opacity_win:
                rule_lines.append(f"windowrulev2 = opacity {active_opacity} {inactive_opacity}, {match_clause}")

            if fullscreen_win:
                rule_lines.append(f"windowrulev2 = fullscreen, {match_clause}")
            if maximize_win:
                rule_lines.append(f"windowrulev2 = maximize, {match_clause}")
            if idle_inhibit and idle_inhibit_mode != "none":
                rule_lines.append(f"windowrulev2 = idleinhibit {idle_inhibit_mode}, {match_clause}")
            if max_fps_rule and max_fps_val > 0:
                rule_lines.append(f"windowrulev2 = maxfps {max_fps_val}, {match_clause}")
            if enable_render_unfocused:
                rule_lines.append(f"windowrulev2 = renderunfocused 1, {match_clause}")

            if no_focus:
                rule_lines.append(f"windowrulev2 = noinitialfocus, {match_clause}")
            if stay_focused:
                rule_lines.append(f"windowrulev2 = stayfocused, {match_clause}")
            if focus_on_activate:
                rule_lines.append(f"windowrulev2 = focusonactivate, {match_clause}")

            if disable_blur:
                rule_lines.append(f"windowrulev2 = noblur, {match_clause}")
            if disable_border:
                rule_lines.append(f"windowrulev2 = noborder, {match_clause}")
            if disable_shadow:
                rule_lines.append(f"windowrulev2 = noshadow, {match_clause}")
            if disable_anim:
                rule_lines.append(f"windowrulev2 = noanim, {match_clause}")
            if dim_around:
                rule_lines.append(f"windowrulev2 = dimaround, {match_clause}")
            if custom_rounding and rounding_val >= 0:
                rule_lines.append(f"windowrulev2 = rounding {rounding_val}, {match_clause}")
            if custom_bordercolor and bordercolor_val.strip():
                rule_lines.append(f"windowrulev2 = bordercolor {bordercolor_val.strip()}, {match_clause}")
            if suppress_max:
                rule_lines.append(f"windowrulev2 = suppressevent maximize, {match_clause}")
            if group_rule and group_val:
                rule_lines.append(f"windowrulev2 = group {group_val}, {match_clause}")
            if set_tag_rule and set_tag_val.strip():
                rule_lines.append(f"windowrulev2 = tag +{set_tag_val.strip()}, {match_clause}")

            if not rule_lines:
                rule_lines.append(f"windowrulev2 = float, {match_clause}")

            lines = [
                f"# Window Rule for {win.display_title}",
            ] + rule_lines
            return "\n".join(lines)

        else:
            # Sway / i3 for_window format
            criteria = []
            if match_class and app:
                criteria.append(f'app_id="{app}"')
            if match_title and win.title:
                criteria.append(f'title="{win.title}"')
            if match_initial_class and win.initial_class:
                criteria.append(f'instance="{win.initial_class}"')
            if not criteria:
                criteria.append(f'app_id="{app}"')

            crit_str = " ".join(criteria)
            actions = []
            if float_win:
                actions.append("floating enable")
            elif tile_win:
                actions.append("floating disable")

            if launch_workspace and workspace_val:
                actions.append(f"move container to workspace {workspace_val}")
            if fixed_size and width_val > 0 and height_val > 0:
                actions.append(f"resize set {width_val} px {height_val} px")
            if min_size_rule and min_w > 0 and min_h > 0:
                actions.append(f"minimum_size {min_w} px x {min_h} px")
            if max_size_rule and max_w > 0 and max_h > 0:
                actions.append(f"maximum_size {max_w} px x {max_h} px")

            if fixed_pos:
                actions.append(f"move position {x_val} px {y_val} px")
            if pin_win:
                actions.append("sticky enable")
            if disable_border:
                actions.append("border none")
            if idle_inhibit and idle_inhibit_mode != "none":
                actions.append(f"inhibit_idle {idle_inhibit_mode}")

            if not actions:
                actions.append("floating enable")

            lines = [
                f"# Window Rule for {win.display_title}",
                f'for_window [{crit_str}] {", ".join(actions)}'
            ]
            return "\n".join(lines)

    @staticmethod
    def generate_formatted_block(win: WindowInfo, target: str = "hyprland") -> str:
        """
        Default template block generator.
        """
        if target.lower() in ["hyprland_lua", "lua"]:
            return RuleGenerator.build_custom_rule(win, syntax="hyprland_lua", float_win=True, launch_workspace=True, workspace_val=str(win.workspace_name), fixed_size=True, width_val=win.width, height_val=win.height)
        elif target.lower() in ["hyprland", "hyprland_conf"]:
            return RuleGenerator.build_custom_rule(win, syntax="hyprland_conf", float_win=True, launch_workspace=True, workspace_val=str(win.workspace_name), fixed_size=True, width_val=win.width, height_val=win.height)
        else:
            return RuleGenerator.build_custom_rule(win, syntax="sway", float_win=True, launch_workspace=True, workspace_val=str(win.workspace_name), fixed_size=True, width_val=win.width, height_val=win.height)
