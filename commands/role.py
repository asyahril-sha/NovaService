# commands/role.py
"""
Role Commands NovaService
/role therapist, /role pelacur, /status, /statusrole, /batal, /pause, /resume
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import get_settings
from utils.user_mode import set_user_mode, get_user_mode, get_active_role, set_active_role, set_user_flow
from service.therapist_flow import TherapistFlow
from service.pelacur_system import PelacurSystem
from handlers.message import _stop_auto_send

logger = logging.getLogger(__name__)


# Daftar karakter
THERAPIST_CHARACTERS = ["anya", "syifa", "laura", "tara", "pevita", "maudy", "zara", "angela"]
PELACUR_CHARACTERS = ["davina", "michelle", "jihane", "tissa", "hana", "shindy", "nadya", "alyssa"]

# Dictionary untuk menyimpan role instance dan flow instance
_user_roles = {}
_user_flows = {}


def get_user_role(user_id: int):
    """Dapatkan role instance untuk user"""
    return _user_roles.get(user_id)


def get_user_flow(user_id: int):
    """Dapatkan flow instance untuk user"""
    return _user_flows.get(user_id)


# =============================================================================
# MAIN ROLE COMMAND
# =============================================================================

async def role_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /role [therapist/pelacur]"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "🎭 *Pilih Role*\n\n"
            "Gunakan: `/role therapist` atau `/role pelacur`\n\n"
            "*Therapist:* Anya, Syifa, Laura, Tara, Pevita, Maudy, Zara, Angela\n"
            "*Pelacur:* Davina, Michelle, Jihane, Tissa, Hana, Shindy, Nadya, Alyssa",
            parse_mode='Markdown'
        )
        return
    
    role_type = args[0].lower()
    
    # Bersihkan role lama jika ada
    await _clear_user_role(user_id)
    
    if role_type == "therapist":
        selected = random.choice(THERAPIST_CHARACTERS)
        await _activate_therapist(user_id, selected, update)
    elif role_type == "pelacur":
        selected = random.choice(PELACUR_CHARACTERS)
        await _activate_pelacur(user_id, selected, update)
    else:
        await update.message.reply_text(
            f"Role '{role_type}' gak ada. Pilih: therapist atau pelacur",
            parse_mode='Markdown'
        )


# =============================================================================
# CLEAR ROLE
# =============================================================================

async def _clear_user_role(user_id: int):
    """Bersihkan role lama user"""
    global _user_roles, _user_flows
    
    # Hentikan auto-send jika ada
    try:
        await _stop_auto_send(user_id)
    except ImportError:
        pass
    
    if user_id in _user_roles:
        del _user_roles[user_id]
    if user_id in _user_flows:
        del _user_flows[user_id]
    
    # Reset user mode
    await set_user_mode(user_id, 'chat', None)
    
    logger.info(f"🧹 Cleared role for user {user_id}")


# =============================================================================
# ACTIVATE THERAPIST
# =============================================================================

async def _activate_therapist(user_id: int, character_key: str, update: Update):
    """Aktifkan therapist character"""
    try:
        # Import karakter
        if character_key == "anya":
            from characters.therapist.anya import AnyaCharacter
            character = AnyaCharacter()
        elif character_key == "syifa":
            from characters.therapist.syifa import SyifaCharacter
            character = SyifaCharacter()
        elif character_key == "laura":
            from characters.therapist.laura import LauraCharacter
            character = LauraCharacter()
        elif character_key == "tara":
            from characters.therapist.tara import TaraCharacter
            character = TaraCharacter()
        elif character_key == "pevita":
            from characters.therapist.pevita import PevitaCharacter
            character = PevitaCharacter()
        elif character_key == "maudy":
            from characters.therapist.maudy import MaudyCharacter
            character = MaudyCharacter()
        elif character_key == "zara":
            from characters.therapist.zara import ZaraCharacter
            character = ZaraCharacter()
        elif character_key == "angela":
            from characters.therapist.angela import AngelaCharacter
            character = AngelaCharacter()
        else:
            await update.message.reply_text("Karakter tidak ditemukan.")
            return
        
        # Set booking info
        character.booking_price = 500000
        character.booking_location = "ruang pijat"
        
        # Simpan karakter dan flow
        _user_roles[user_id] = character
        _user_flows[user_id] = TherapistFlow(character)
        await set_user_mode(user_id, 'role', 'therapist')
        await set_active_role(user_id, 'therapist')
        await set_user_flow(user_id, _user_flows[user_id])
        
        # Start session via flow
        greeting = await _user_flows[user_id].start()
        
        logger.info(f"✅ Therapist activated: {character.name} for user {user_id}")
        await update.message.reply_text(greeting, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Activate therapist error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {str(e)}")


# =============================================================================
# ACTIVATE PELACUR
# =============================================================================

async def _activate_pelacur(user_id: int, character_key: str, update: Update):
    """Aktifkan pelacur character"""
    try:
        # Import karakter
        if character_key == "davina":
            from characters.pelacur.davina import DavinaCharacter
            character = DavinaCharacter()
        elif character_key == "michelle":
            from characters.pelacur.michelle import MichelleCharacter
            character = MichelleCharacter()
        elif character_key == "jihane":
            from characters.pelacur.jihane import JihaneCharacter
            character = JihaneCharacter()
        elif character_key == "tissa":
            from characters.pelacur.tissa import TissaCharacter
            character = TissaCharacter()
        elif character_key == "hana":
            from characters.pelacur.hana import HanaCharacter
            character = HanaCharacter()
        elif character_key == "shindy":
            from characters.pelacur.shindy import ShindyCharacter
            character = ShindyCharacter()
        elif character_key == "nadya":
            from characters.pelacur.nadya import NadyaCharacter
            character = NadyaCharacter()
        elif character_key == "alyssa":
            from characters.pelacur.alyssa import AlyssaCharacter
            character = AlyssaCharacter()
        else:
            await update.message.reply_text("Karakter tidak ditemukan.")
            return
        
        # Set booking info
        character.booking_price = 10000000
        character.booking_location = "lokasi booking"
        character.booking_duration = 10
        
        # Simpan karakter dan flow
        _user_roles[user_id] = character
        _user_flows[user_id] = PelacurSystem(character)
        await set_user_mode(user_id, 'role', 'pelacur')
        await set_active_role(user_id, 'pelacur')
        await set_user_flow(user_id, _user_flows[user_id])
        
        # Start session via flow
        greeting = await _user_flows[user_id].start(
            location=character.booking_location,
            price=character.booking_price,
            duration_hours=character.booking_duration
        )
        
        logger.info(f"✅ Pelacur activated: {character.name} for user {user_id}")
        await update.message.reply_text(greeting, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Activate pelacur error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {str(e)}")


# =============================================================================
# STATUS COMMAND
# =============================================================================

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /status - Lihat status sesi role yang aktif"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("❌ Maaf, command hanya untuk admin.")
        return
    
    mode = await get_user_mode(user_id)
    active_role = await get_active_role(user_id)
    flow = _user_flows.get(user_id)
    
    if mode != 'role' or not active_role:
        await update.message.reply_text(
            "📭 *Tidak ada sesi role yang aktif*\n\n"
            "Gunakan /role therapist atau /role pelacur untuk memulai, Mas.\n\n"
            "💜 *Nova tersenyum*\n\n\"Ada yang bisa Nova bantu?\"",
            parse_mode='Markdown'
        )
        return
    
    flow = _user_flows.get(user_id)
    if flow and hasattr(flow, 'get_status'):
        status_text = flow.get_status()
        await update.message.reply_text(status_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"✅ *Sesi {active_role} sedang aktif*\n\n"
            f"👤 Karakter: {_user_roles.get(user_id).name if _user_roles.get(user_id) else 'Unknown'}\n"
            f"\nKetik /batal untuk mengakhiri sesi.",
            parse_mode='Markdown'
        )


async def statusrole_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /statusrole - Lihat status role yang aktif (alias)"""
    await status_command(update, context)


# =============================================================================
# BATAL COMMAND
# =============================================================================

async def batal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /batal - Kembali ke mode chat dan bersihkan role"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        return
    
    # Bersihkan role
    await _clear_user_role(user_id)
    
    await update.message.reply_text(
        "💜 *KEMBALI KE NOVA* 💜\n\n"
        "Nova di sini, Mas. Ada yang bisa dibantu?",
        parse_mode='Markdown'
    )


# =============================================================================
# PAUSE AND RESUME COMMANDS
# =============================================================================

async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /pause - Jeda sesi sementara"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("❌ Maaf, command hanya untuk admin.")
        return
    
    mode = await get_user_mode(user_id)
    active_role = await get_active_role(user_id)
    flow = await get_user_flow(user_id)
    
    if mode != 'role' or not active_role:
        await update.message.reply_text("📭 Tidak ada sesi yang sedang berjalan.")
        return
    
    flow = _user_flows.get(user_id)
    if not flow:
        await update.message.reply_text("📭 Sesi tidak ditemukan.")
        return
    
    if not flow.is_active:
        await update.message.reply_text("📭 Sesi tidak aktif.")
        return
    
    if hasattr(flow, 'is_paused') and flow.is_paused:
        await update.message.reply_text("⏸️ Sesi sudah dalam keadaan pause.")
        return
    
    # Pause session
    if hasattr(flow, 'pause'):
        await flow.pause()
        await update.message.reply_text(
            "⏸️ *Sesi di-pause*\n\n"
            "Ketik /resume untuk melanjutkan sesi.\n"
            "Ketik /batal untuk mengakhiri sesi.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Fitur pause tidak tersedia untuk role ini.")


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /resume - Lanjutkan sesi yang di-pause"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("❌ Maaf, command hanya untuk admin.")
        return
    
    mode = await get_user_mode(user_id)
    active_role = await get_active_role(user_id)
    flow = await get_user_flow(user_id)
    
    if mode != 'role' or not active_role:
        await update.message.reply_text("📭 Tidak ada sesi yang sedang berjalan.")
        return
    
    flow = _user_flows.get(user_id)
    if not flow:
        await update.message.reply_text("📭 Sesi tidak ditemukan.")
        return
    
    if not hasattr(flow, 'is_paused') or not flow.is_paused:
        await update.message.reply_text("▶️ Tidak ada sesi yang di-pause.")
        return
    
    # Resume session
    if hasattr(flow, 'resume'):
        await flow.resume()
        await update.message.reply_text(
            "▶️ *Sesi dilanjutkan*\n\n"
            "Role akan melanjutkan aktivitas.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Fitur resume tidak tersedia untuk role ini.")
        

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /status - Lihat status sesi role yang aktif"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        await update.message.reply_text("❌ Maaf, command hanya untuk admin.")
        return
    
    from utils.user_mode import get_user_mode, get_active_role, get_user_flow
    
    mode = await get_user_mode(user_id)
    active_role = await get_active_role(user_id)
    flow = get_user_flow(user_id)
    
    if mode != 'role' or not active_role or not flow:
        await update.message.reply_text(
            "📭 *Tidak ada sesi role yang aktif*\n\n"
            "Gunakan /role therapist atau /role pelacur untuk memulai, Mas.\n\n"
            "💜 *Nova tersenyum*\n\n\"Ada yang bisa Nova bantu?\"",
            parse_mode='Markdown'
        )
        return
    
    # Cek apakah flow punya method get_status
    if hasattr(flow, 'get_status'):
        status_text = flow.get_status()
        await update.message.reply_text(status_text, parse_mode='Markdown')
    else:
        status_text = f"✅ *Sesi {active_role} sedang aktif*\n\n"
        if hasattr(flow, 'character'):
            status_text += f"👤 Karakter: {flow.character.name}\n"
        status_text += f"\nKetik /batal untuk mengakhiri sesi."
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
# =============================================================================
# REGISTER FUNCTION
# =============================================================================

def register_role_commands(app):
    """Register semua role commands"""
    app.add_handler(CommandHandler("role", role_command))
    app.add_handler(CommandHandler("status", cmd_status))  # ← TAMBAHKAN INI
    app.add_handler(CommandHandler("statusrole", statusrole_command))
    app.add_handler(CommandHandler("batal", batal_command))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("resume", resume_command))
    logger.info("✅ Role commands registered: /role, /status, /statusrole, /batal, /pause, /resume")
