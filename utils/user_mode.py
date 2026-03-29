# utils/user_mode.py
"""
User Mode Management NovaService
Menyimpan mode user (chat/role) ke database
"""

import json
import time
import logging
from typing import Optional

from memory.persistent import get_nova_persistent

logger = logging.getLogger(__name__)

# Dictionary untuk menyimpan mode user
_user_modes = {}
_active_roles = {}
_user_flows = {}


async def set_user_mode(user_id: int, mode: str, role: Optional[str] = None):
    """Set user mode (chat/role)"""
    _user_modes[user_id] = mode
    if role:
        _active_roles[user_id] = role
    logger.info(f"👤 User {user_id} mode saved: {mode}, role: {role}")


async def get_user_mode(user_id: int) -> str:
    """Get user mode (default: chat)"""
    return _user_modes.get(user_id, 'chat')


async def set_active_role(user_id: int, role: str):
    """Set active role for user (therapist/pelacur)"""
    global _active_roles
    _active_roles[user_id] = role
    logger.info(f"👤 User {user_id} active role set to: {role}")


async def get_active_role(user_id: int) -> str:
    """Get active role for user"""
    return _active_roles.get(user_id)


async def set_user_flow(user_id: int, flow):
    """Set flow instance for user"""
    global _user_flows
    _user_flows[user_id] = flow
    logger.info(f"👤 User {user_id} flow set")


async def get_user_flow(user_id: int):
    """Get flow instance for user"""
    return _user_flows.get(user_id)


async def clear_user_flow(user_id: int):
    """Clear flow instance for user"""
    global _user_flows
    if user_id in _user_flows:
        del _user_flows[user_id]
        logger.info(f"👤 User {user_id} flow cleared")
