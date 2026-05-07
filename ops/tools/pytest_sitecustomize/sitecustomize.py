from __future__ import annotations

import os


_original_mkdir = os.mkdir


def _sandbox_safe_mkdir(path, mode=0o777, *, dir_fd=None):
    if os.name == "nt" and mode == 0o700:
        mode = 0o755
    if dir_fd is not None:
        return _original_mkdir(path, mode, dir_fd=dir_fd)
    return _original_mkdir(path, mode)


os.mkdir = _sandbox_safe_mkdir
