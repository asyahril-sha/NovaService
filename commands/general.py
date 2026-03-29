# commands/general.py
"""
General Commands NovaService
/start, /help, /status, /nova, /batal, /pause, /resume
"""

import logging
import time
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
        "• `/role pelacur` - Panggil pelacur (Davina/Michelle/Jihane/Tissa/Hana/Shindy/Nadya/Sallsa)\n"
        "• `/status` - Lihat status\n"
        "• `/pause` - Hentikan sesi sementara\n"
        "• `/resume` - Lanjutkan sesi\n"
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
    
    # Hentikan auto-send jika ada
    try:
        from handlers.message import _stop_auto_send
        await _stop_auto_send(user_id)
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Error stopping auto-send: {e}")
    
    await set_user_mode(user_id, 'chat', None)
    
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
        "• 8 karakter: Davina, Michelle, Jihane, Tissa, Hana, Shindy, Nadya, Sallsa
        "• Full booking 10 jam, Mas bebas climax berapa kali\n\n"
        "*Manajemen Sesi:*\n"
        "• `/pause` - Hentikan sesi sementara (timer berhenti)\n"
        "• `/resume` - Lanjutkan sesi (timer jalan lagi)\n"
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
        from commands.role import get_user_role
        role = get_user_role(user_id)
        
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
    
    # Hentikan auto-send jika ada
    try:
        from handlers.message import _stop_auto_send
        await _stop_auto_send(user_id)
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Error stopping auto-send: {e}")
    
    await set_user_mode(user_id, 'chat', None)
    
    await update.message.reply_text(
        "💜 *KEMBALI KE NOVA* 💜\n\n"
        "Nova di sini, Mas. Ada yang bisa dibantu?",
        parse_mode='Markdown'
    )


# =============================================================================
# PAUSE & RESUME COMMANDS
# =============================================================================

async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /pause - Hentikan sesi sementara (timer berhenti)"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        return
    
    mode = await get_user_mode(user_id)
    active_role = await get_active_role(user_id)
    
    if mode != 'role' or not active_role:
        await update.message.reply_text(
            "💜 Tidak ada role yang aktif.\n\n"
            "Gunakan `/role therapist` atau `/role pelacur` untuk mulai, Mas.",
            parse_mode='Markdown'
        )
        return
    
    from commands.role import get_user_flow
    flow = get_user_flow(user_id)
    
    if not flow:
        await update.message.reply_text(
            "❌ Flow tidak ditemukan. Silakan pilih role lagi, Mas.",
            parse_mode='Markdown'
        )
        return
    
    # Cek apakah flow punya atribut is_paused
    if hasattr(flow, 'is_paused') and flow.is_paused:
        await update.message.reply_text(
            "💜 Sesi sudah dalam keadaan pause.\n\n"
            "Kirim `/resume` untuk lanjutkan.",
            parse_mode='Markdown'
        )
        return
    
    # Pause sesi
    flow.is_paused = True
    flow.pause_start_time = time.time()
    
    # Hentikan auto-send
    try:
        from handlers.message import _stop_auto_send
        await _stop_auto_send(user_id)
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Error stopping auto-send: {e}")
    
    await update.message.reply_text(
        "⏸️ *SESI DI-PAUSE* ⏸️\n\n"
        "Waktu dihentikan sementara.\n\n"
        "Kirim `/resume` untuk lanjutkan sesi.",
        parse_mode='Markdown'
    )


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /resume - Lanjutkan sesi yang di-pause"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        return
    
    mode = await get_user_mode(user_id)
    active_role = await get_active_role(user_id)
    
    if mode != 'role' or not active_role:
        await update.message.reply_text(
            "💜 Tidak ada role yang aktif.\n\n"
            "Gunakan `/role therapist` atau `/role pelacur` untuk mulai, Mas.",
            parse_mode='Markdown'
        )
        return
    
    from commands.role import get_user_flow
    flow = get_user_flow(user_id)
    
    if not flow:
        await update.message.reply_text(
            "❌ Flow tidak ditemukan. Silakan pilih role lagi, Mas.",
            parse_mode='Markdown'
        )
        return
    
    if not hasattr(flow, 'is_paused') or not flow.is_paused:
        await update.message.reply_text(
            "💜 Tidak ada sesi yang di-pause.\n\n"
            "Gunakan `/pause` untuk menghentikan sesi sementara.",
            parse_mode='Markdown'
        )
        return
    
    # Hitung durasi pause
    pause_duration = time.time() - flow.pause_start_time
    
    # Resume sesi - adjust timer (untuk therapist flow)
    if hasattr(flow, 'back_area_start_time') and flow.back_area_start_time > 0:
        old_time = flow.back_area_start_time
        flow.back_area_start_time += pause_duration
        logger.info(f"Adjusted back_area_start_time: {old_time} → {flow.back_area_start_time} (+{pause_duration}s)")

    if hasattr(flow, 'front_area_start_time') and flow.front_area_start_time > 0:
        old_time = flow.front_area_start_time
        flow.front_area_start_time += pause_duration
        logger.info(f"Adjusted front_area_start_time: {old_time} → {flow.front_area_start_time} (+{pause_duration}s)")

    if hasattr(flow, 'phase_start_time') and flow.phase_start_time > 0:
        flow.phase_start_time += pause_duration

    # Untuk pelacur flow
    if hasattr(flow, 'area_start_time') and flow.area_start_time > 0:
        flow.area_start_time += pause_duration
    
    flow.is_paused = False
    
    # Mulai auto-send lagi
    try:
        from handlers.message import _start_auto_send
        await _start_auto_send(user_id, flow, context)
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Error starting auto-send: {e}")
    
    minutes = int(pause_duration // 60)
    seconds = int(pause_duration % 60)
    
    await update.message.reply_text(
        f"▶️ *SESI DILANJUTKAN* ▶️\n\n"
        f"Pause selama {minutes} menit {seconds} detik.\n\n"
        "Melanjutkan service...",
        parse_mode='Markdown'
    )


def register_general_commands(app):
    """Register semua general commands"""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("nova", nova_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("batal", batal_command))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("resume", resume_command))
    logger.info("✅ General commands registered: /start, /nova, /help, /status, /batal, /pause, /resume")
