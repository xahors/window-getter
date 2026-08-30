"""
Environment and host execution compatibility utilities.
"""

import os
from typing import Dict


def get_clean_env() -> Dict[str, str]:
    """
    Return an environment dictionary suitable for invoking external host binaries.
    Strips AppImage and PyInstaller bundle paths from LD_LIBRARY_PATH, PYTHONPATH, and PYTHONHOME
    to prevent library version mismatches with host system utilities (hyprctl, swaymsg, xdotool, etc.).
    """
    env = os.environ.copy()
    appdir = env.get("APPDIR", "")
    ld_path = env.get("LD_LIBRARY_PATH", "")

    if "LD_LIBRARY_PATH_ORIG" in env:
        orig = env["LD_LIBRARY_PATH_ORIG"]
        if orig:
            env["LD_LIBRARY_PATH"] = orig
        else:
            env.pop("LD_LIBRARY_PATH", None)
    elif appdir and ld_path:
        cleaned = [p for p in ld_path.split(":") if p and not p.startswith(appdir)]
        if cleaned:
            env["LD_LIBRARY_PATH"] = ":".join(cleaned)
        else:
            env.pop("LD_LIBRARY_PATH", None)
    elif "LD_LIBRARY_PATH" in env:
        cleaned = [p for p in ld_path.split(":") if p and "_MEI" not in p and "/tmp/.mount" not in p]
        if cleaned:
            env["LD_LIBRARY_PATH"] = ":".join(cleaned)
        else:
            env.pop("LD_LIBRARY_PATH", None)

    if "PYTHONPATH" in env and appdir and appdir in env.get("PYTHONPATH", ""):
        env.pop("PYTHONPATH", None)
    if "PYTHONHOME" in env and appdir and appdir in env.get("PYTHONHOME", ""):
        env.pop("PYTHONHOME", None)

    return env
