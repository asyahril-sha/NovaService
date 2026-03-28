# commands/role.py
"""
Role Commands NovaService
/role therapist, /role pelacur, /statusrole
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import get_settings
from utils.user_mode import set_user_mode, get_user_mode, get_active_role

logger = logging.getLogger(__name__)


# Daftar karakter
THERAPIST_CHARACTERS = [
    "anya", "syifa", "laura", "tara", "pevita", "maudy", "zara", "angela"
]

PELACUR_CHARACTERS = [
    "davina", "michelle", "jihane", "tissa", "hana", "shindy", "nadya", "alyssa"
]


async def role_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /role [therapist/pelacur]"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "Gunakan: `/role therapist` atau `/role pelacur`\n\n"
            "Therapist: Anya, Syifa, Laura, Tara, Pevita, Maudy, Zara, Angela\n"
            "Pelacur: Davina, Michelle, Jihane, Tissa, Hana, Shindy, Nadya, Alyssa",
            parse_mode='Markdown'
        )
        return
    
    role_type = args[0].lower()
    
    if role_type == "therapist":
        # Pilih karakter random
        selected = random.choice(THERAPIST_CHARACTERS)
        await _activate_therapist(user_id, selected, update)
    
    elif role_type == "pelacur":
        # Pilih karakter random
        selected = random.choice(PELACUR_CHARACTERS)
        await _activate_pelacur(user_id, selected, update)
    
    else:
        await update.message.reply_text(
            f"Role '{role_type}' gak ada. Pilih: therapist atau pelacur",
            parse_mode='Markdown'
        )


async def _activate_therapist(user_id: int, character_key: str, update: Update):
    """Aktifkan therapist character"""
    from roles.manager import get_role_manager
    from characters.therapist import (
        AnyaCharacter, SyifaCharacter, LauraCharacter,
        TaraCharacter, PevitaCharacter, MaudyCharacter,
        ZaraCharacter, AngelaCharacter
    )
    
    character_map = {
        "anya": AnyaCharacter,
        "syifa": SyifaCharacter,
        "laura": LauraCharacter,
        "tara": TaraCharacter,
        "pevita": PevitaCharacter,
        "maudy": MaudyCharacter,
        "zara": ZaraCharacter,
        "angela": AngelaCharacter
    }
    
    character_class = character_map.get(character_key)
    if not character_class:
        await update.message.reply_text("Karakter tidak ditemukan.")
        return
    
    # Buat instance karakter
    character = character_class()
    
    # Set booking info (default untuk therapist)
    character.booking_price = 500000  # HJ + extra
    character.booking_location = "ruang pijat"
    
    # Simpan ke role manager
    role_manager = get_role_manager()
    role_manager.set_role(user_id, character, "therapist")
    
    # Set user mode
    await set_user_mode(user_id, 'role', 'therapist')
    
    # Start session
    greeting = await character.start_session()
    
    await update.message.reply_text(greeting, parse_mode='Markdown')


async def _activate_pelacur(user_id: int, character_key: str, update: Update):
    """Aktifkan pelacur character"""
    from roles.manager import get_role_manager
    from characters.pelacur import (
        DavinaCharacter, MichelleCharacter, JihaneCharacter,
        TissaCharacter, HanaCharacter, ShindyCharacter,
        NadyaCharacter, AlyssaCharacter
    )
    
    character_map = {
        "davina": DavinaCharacter,
        "michelle": MichelleCharacter,
        "jihane": JihaneCharacter,
        "tissa": TissaCharacter,
        "hana": HanaCharacter,
        "shindy": ShindyCharacter,
        "nadya": NadyaCharacter,
        "alyssa": AlyssaCharacter
    }
    
    character_class = character_map.get(character_key)
    if not character_class:
        await update.message.reply_text("Karakter tidak ditemukan.")
        return
    
    # Buat instance karakter
    character = character_class()
    
    # Set booking info
    character.booking_price = 10000000  # 10jt
    character.booking_location = "lokasi booking"
    character.booking_duration = 10  # 10 jam
    
    # Simpan ke role manager
    role_manager = get_role_manager()
    role_manager.set_role(user_id, character, "pelacur")
    
    # Set user mode
    await set_user_mode(user_id, 'role', 'pelacur')
    
    # Start session
    greeting = await character.start_session()
    
    await update.message.reply_text(greeting, parse_mode='Markdown')


async def statusrole_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /statusrole - Lihat status role yang aktif"""
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
    
    from roles.manager import get_role_manager
    role_manager = get_role_manager()
    role = role_manager.get_role(user_id)
    
    if role:
        status_text = role.get_status()
        await update.message.reply_text(status_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "Role tidak ditemukan. Coba pilih role lagi, Mas.",
            parse_mode='Markdown'
        )


def register_role_commands(app):
    """Register role commands"""
    app.add_handler(CommandHandler("role", role_command))
    app.add_handler(CommandHandler("statusrole", statusrole_command))
