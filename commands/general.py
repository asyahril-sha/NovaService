# commands/general.py
"""
General Commands NovaService
/start, /help, /status, /nova, /batal
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import get_settings
from utils.user_mode import set_user_mode, get_user_mode, get_active_role

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("Halo! Bot ini untuk Mas. 💜")
        return
    
    await set_user_mode(user_id, 'chat', None)
    
    await update.message.reply_text(
        "💜 *NOVASERVICE* 💜\n\n"
        "Selamat datang, Mas.\n\n"
        "*Command yang tersedia:*\n"
        "• `/nova` - Panggil Nova\n"
        "• `/role therapist` - Panggil therapist (Anya/Syifa/Laura/Tara/Pevita/Maudy/Zara/Angela)\n"
        "• `/role pelacur` - Panggil pelacur (Davina/Michelle/Jihane/Tissa/Hana/Shindy/Nadya/Alyssa)\n"
        "• `/status` - Lihat status\n"
        "• `/help` - Bantuan lengkap\n"
        "• `/batal` - Kembali ke mode chat\n\n"
        "Nikmati, Mas. 💜",
        parse_mode='Markdown'
    )


async def nova_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /nova - Kembali ke Nova"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("Maaf, Nova cuma untuk Mas. 💜")
        return
    
    await set_user_mode(user_id, 'chat', None)
    
    from datetime import datetime
    hour = datetime.now().hour
    
    if 5 <= hour < 11:
        greeting = "Pagi, Mas. Nova di sini. Ada yang bisa dibantu?"
    elif 11 <= hour < 15:
        greeting = "Siang, Mas. Nova di sini. Ada yang bisa dibantu?"
    elif 15 <= hour < 18:
        greeting = "Sore, Mas. Nova di sini. Ada yang bisa dibantu?"
    else:
        greeting = "Malam, Mas. Nova di sini. Ada yang bisa dibantu?"
    
    await update.message.reply_text(
        f"💜 *NOVA DI SINI* 💜\n\n{greeting}\n\nKetik /role therapist atau /role pelacur kalo mau service, Mas.",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /help"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("Bot ini untuk Mas. 💜")
        return
    
    await update.message.reply_text(
        "📖 *BANTUAN NOVASERVICE* 📖\n\n"
        "*Mode Chat:*\n"
        "• `/nova` - Panggil Nova\n"
        "• `/status` - Lihat status\n"
        "• `/help` - Bantuan ini\n\n"
        "*Role Therapist:*\n"
        "• `/role therapist` - Panggil therapist random\n"
        "• 8 karakter: Anya, Syifa, Laura, Tara, Pevita, Maudy, Zara, Angela\n"
        "• Alur: Pijat belakang (30 menit) → Pijat depan (30 menit) → HJ → Extra service (BJ/Sex)\n\n"
        "*Role Pelacur:*\n"
        "• `/role pelacur` - Panggil pelacur random\n"
        "• 8 karakter: Davina, Michelle, Jihane, Tissa, Hana, Shindy, Nadya, Alyssa\n"
        "• Full booking 10 jam, Mas bebas climax berapa kali\n\n"
        "*Umum:*\n"
        "• `/batal` - Kembali ke mode chat\n\n"
        "Selamat menikmati, Mas. 💜",
        parse_mode='Markdown'
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /status - Lihat status saat ini"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        return
    
    mode = await get_user_mode(user_id)
    active_role = await get_active_role(user_id)
    
    if mode == 'role' and active_role:
        from roles.manager import get_role_manager
        role_manager = get_role_manager()
        role = role_manager.get_role(user_id)
        
        if role:
            status_text = role.get_status()
            await update.message.reply_text(status_text, parse_mode='Markdown')
            return
    
    # Mode chat
    await update.message.reply_text(
        "💜 *MODE CHAT*\n\n"
        "Sedang dalam mode chat dengan Nova.\n\n"
        "Ketik /role therapist atau /role pelacur untuk mulai service, Mas.",
        parse_mode='Markdown'
    )


async def batal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /batal - Kembali ke mode chat"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        return
    
    await set_user_mode(user_id, 'chat', None)
    
    await update.message.reply_text(
        "💜 *KEMBALI KE NOVA* 💜\n\n"
        "Nova di sini, Mas. Ada yang bisa dibantu?",
        parse_mode='Markdown'
    )


def register_general_commands(app):
    """Register semua general commands"""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("nova", nova_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("batal", batal_command))
