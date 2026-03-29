# handlers/message.py
"""
Message Handler NovaService - Memproses pesan dari Mas
Dengan auto-send queue dan role mode management
"""

import asyncio
import logging
import time
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from config import get_settings
from utils.user_mode import get_user_mode, get_active_role, get_user_flow

logger = logging.getLogger(__name__)

# Global flag
NOVA_AVAILABLE = True

# Dictionary untuk menyimpan auto-send tasks per user
_auto_send_tasks: dict = {}


def set_nova_available(status: bool):
    """Set status ketersediaan Nova"""
    global NOVA_AVAILABLE
    NOVA_AVAILABLE = status
    logger.info(f"[NOVA] Availability set to: {status}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan biasa"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    # Hanya admin
    if user_id != settings.admin_id:
        return
    
    pesan = update.message.text
    if not pesan:
        return
    
    logger.info(f"📨 Message from {user_id}: {pesan[:50]}")
    
    # Ambil mode & role
    mode = await get_user_mode(user_id)
    active_role = await get_active_role(user_id)
    
    logger.info(f"📌 Mode: {mode}, Active Role: {active_role}")
    
    # ========== ROLE MODE ==========
    if mode == 'role' and active_role:
        try:
            # ✅ Lazy import (hindari circular import)
            from commands.role import get_user_role, get_user_flow
            
            role = get_user_role(user_id)
            flow = get_user_flow(user_id)
            
            if not role or not flow:
                await update.message.reply_text(
                    "💜 Role belum aktif. Silakan pilih role dulu dengan /role therapist atau /role pelacur",
                    parse_mode='Markdown'
                )
                return
            
            logger.info(f"Processing message for role: {active_role}, character: {role.name}")
            
            # Proses pesan ke flow
            response = await flow.process(pesan)
            
            if response:
                await update.message.reply_text(response, parse_mode='Markdown')
            
            # Stop auto-send lama
            await _stop_auto_send(user_id)
            
            # Start auto-send baru jika masih aktif
            if flow.is_active:
                await _start_auto_send(user_id, flow, context)
            
        except Exception as e:
            logger.error(f"Role chat error: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                parse_mode='Markdown'
            )
        return
    
    # ========== DEFAULT CHAT MODE ==========
    await _stop_auto_send(user_id)
    
    await update.message.reply_text(
        "*Nova tersenyum*\n\n"
        "\"Iya, Mas. Nova dengerin kok.\n\n"
        "Ketik /role therapist atau /role pelacur kalau mau service.\"",
        parse_mode='Markdown'
    )

        return
    
    # ========== CHAT MODE DEFAULT ==========
    # Hentikan auto-send jika ada
    await _stop_auto_send(user_id)
    
    await update.message.reply_text(
        "*Nova tersenyum*\n\n\"Iya, Mas. Nova dengerin kok.\n\nKetik /role therapist atau /role pelacur kalo mau service, Mas.\"",
        parse_mode='Markdown'
    )
    

# =============================================================================
# AUTO-SEND TASK MANAGEMENT
# =============================================================================

async def _start_auto_send(user_id: int, flow, context: ContextTypes.DEFAULT_TYPE):
    """Mulai auto-send task untuk mengirim scene otomatis"""
    global _auto_send_tasks

    try:
        # Hentikan task lama jika ada
        await _stop_auto_send(user_id)

        # ✅ Gunakan async function (bukan lambda)
        async def send_callback(msg):
            """Kirim pesan langsung ke Telegram"""
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=msg,
                    parse_mode='Markdown'
                )
                logger.debug(f"✅ Auto-send message delivered to {user_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send auto message: {e}")

        # ✅ Set callback ke flow
        flow._send_callback = send_callback
        logger.info(f"🔍 Flow class: {flow.__class__.__name__}")
        logger.info(f"✅ Send callback registered for user {user_id}")

        # ✅ Start auto-send task dari flow
        await flow._start_auto_send_task()

        # ✅ SIMPAN TASK (INI YANG KAMU KURANG)
        _auto_send_tasks[user_id] = flow.auto_send_task

        logger.info(f"🔄 Auto-send started for user {user_id}")

    except Exception as e:
        logger.error(f"Error starting auto-send for user {user_id}: {e}")


async def _stop_auto_send(user_id: int):
    """Hentikan auto-send task untuk user"""
    global _auto_send_tasks
    
    # CEK DULU APAKAH USER ID ADA
    if user_id not in _auto_send_tasks:
        logger.debug(f"No auto-send task for user {user_id}")
        return
    
    task = _auto_send_tasks[user_id]
    if not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error cancelling task for user {user_id}: {e}")
    
    # HAPUS DENGAN AMAN (pop dengan default None)
    _auto_send_tasks.pop(user_id, None)
    logger.info(f"🛑 Auto-send stopped for user {user_id}")
