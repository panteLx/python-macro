"""Utility modules for MacroManager."""

from macro_manager.utils.direct_keys import DIK_W, DIK_S, DIK_SPACE
from macro_manager.utils.window_utils import (
    find_game_window,
    focus_game_window,
    restore_window_focus,
    send_key_to_window,
)
from macro_manager.utils.auto_updater import (
    check_for_updates,
    download_and_install_update,
    get_current_version,
    cleanup_backups,
)

__all__ = [
    "DIK_W",
    "DIK_S",
    "DIK_SPACE",
    "find_game_window",
    "focus_game_window",
    "restore_window_focus",
    "send_key_to_window",
    "check_for_updates",
    "download_and_install_update",
    "get_current_version",
    "cleanup_backups",
]
