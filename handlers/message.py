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
from utils.user_mode import get_user_mode, get_active_role

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
    
    if user_id != settings.admin_id:
        return
    
    pesan = update.message.text
    if not pesan:
        return
    
    logger.info(f"📨 Message from {user_id}: {pesan[:50]}")
    
    mode = await get_user_mode(user_id)
    active_role = await get_active_role(user_id)
    
    logger.info(f"📌 Mode: {mode}, Active Role: {active_role}")
    
    # ========== ROLE MODE ==========
    if mode == 'role' and active_role:
        try:
            from commands.role import get_user_role, get_user_flow
            
            role = get_user_role(user_id)
            flow = get_user_flow(user_id)
            
            if not role or not flow:
                await update.message.reply_text(
                    "💜 Role belum aktif. Silakan pilih role dulu dengan **/role therapist** atau **/role pelacur**",
                    parse_mode='Markdown'
                )
                return
            
            logger.info(f"Processing message for role: {active_role}, character: {role.name}")
            
            # Proses pesan Mas ke flow
            response = await flow.process(pesan)
            
            if response:
                await update.message.reply_text(response, parse_mode='Markdown')
            
            # Hentikan auto-send task jika ada
            await _stop_auto_send(user_id)
            
            # Jika flow masih aktif, mulai auto-send task baru
            if flow.is_active:
                await _start_auto_send(user_id, flow, context)
            
        except Exception as e:
            logger.error(f"Role chat error: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
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
    
    # Hentikan task lama jika ada
    await _stop_auto_send(user_id)
    
    # Buat task baru
    task = asyncio.create_task(_auto_send_loop(user_id, flow, context))
    _auto_send_tasks[user_id] = task
    logger.info(f"🔄 Auto-send started for user {user_id}")


async def _stop_auto_send(user_id: int):
    """Hentikan auto-send task untuk user"""
    global _auto_send_tasks
    
    if user_id in _auto_send_tasks:
        task = _auto_send_tasks[user_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        del _auto_send_tasks[user_id]
        logger.info(f"🛑 Auto-send stopped for user {user_id}")


async def _auto_send_loop(user_id: int, flow, context: ContextTypes.DEFAULT_TYPE):
    """
    Loop auto-send untuk mengirim scene otomatis
    Setiap 30 detik cek apakah perlu kirim scene berikutnya
    """
    try:
        while flow.is_active:
            # Tunggu 30 detik
            await asyncio.sleep(30)
            
            # Cek apakah perlu kirim scene berikutnya
            response = await flow.process("")  # Pesan kosong = auto scene
            
            if response:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=response,
                    parse_mode='Markdown'
                )
                logger.info(f"📤 Auto-sent scene for user {user_id}")
            
            # Jika flow sudah tidak aktif, stop loop
            if not flow.is_active:
                break
                
    except asyncio.CancelledError:
        logger.info(f"Auto-send cancelled for user {user_id}")
    except Exception as e:
        logger.error(f"Auto-send error for user {user_id}: {e}", exc_info=True)
    finally:
        # Cleanup
        if user_id in _auto_send_tasks:
            del _auto_send_tasks[user_id]
