# commands/__init__.py
"""
NovaService Commands Package
Semua command Telegram untuk NovaService
"""

from commands.general import register_general_commands
from commands.role import register_role_commands

__all__ = [
    'register_general_commands',
    'register_role_commands',
]
