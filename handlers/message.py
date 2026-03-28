# handlers/message.py
"""
Message Handler NovaService
Memproses pesan biasa dari Mas
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import get_settings
from utils.user_mode import get_user_mode, get_active_role

logger = logging.getLogger(__name__)

# Global flag
NOVA_AVAILABLE = True


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
    
    # handlers/message.py bagian role mode

    if mode == 'role' and active_role:
        try:
            from commands.role import get_user_role
            role = get_user_role(user_id)
        
            if not role:
                await update.message.reply_text(
                    "💜 Role belum aktif. Silakan pilih role dulu dengan **/role therapist** atau **/role pelacur**",
                    parse_mode='Markdown'
                )
                return
        
            # Proses pesan ke role
            from service.therapist_flow import TherapistFlow
            from service.pelacur_flow import PelacurFlow

            logger.info(f"Processing message for role: {active_role}, character: {role.name}")
        
            if active_role == "therapist":
                flow = TherapistFlow(role)
                response = await flow.process(pesan)
            elif active_role == "pelacur":
                flow = PelacurFlow(role)
                response = await flow.process(pesan)
            else:
                response = f"*{role.name} tersenyum*\n\n\"{role.panggilan}... ada yang bisa dibantu?\""
        
            await update.message.reply_text(response, parse_mode='Markdown')
        
        except Exception as e:
            logger.error(f"Role chat error: {e}", exc_info=True)
            await update.message.reply_text(
                "Maaf, ada error. Coba lagi ya, Mas.",
                parse_mode='Markdown'
            )
        return
    
    # ========== CHAT MODE DEFAULT ==========
    await update.message.reply_text(
        "*Nova tersenyum*\n\n\"Iya, Mas. Nova dengerin kok.\n\nKetik /role therapist atau /role pelacur kalo mau service, Mas.\"",
        parse_mode='Markdown'
    )
