from __future__ import annotations

import os
import shutil
import subprocess


def copy_to_clipboard(text: str) -> bool:
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["clip"],
                input=text,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False
    if shutil.which("pbcopy"):
        try:
            result = subprocess.run(
                ["pbcopy"],
                input=text,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False
    if shutil.which("xclip"):
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False
    return False
