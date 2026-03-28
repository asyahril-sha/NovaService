# commands/role.py
"""
Role Commands NovaService
/role therapist, /role pelacur
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import get_settings
from utils.user_mode import set_user_mode
from service.therapist_flow import TherapistFlow
from service.pelacur_flow import PelacurFlow

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
        
        # Start session via flow
        greeting = await _user_flows[user_id].start()
        
        logger.info(f"Session started for {character.name}")
        await update.message.reply_text(greeting, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Activate therapist error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {str(e)}")


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
        _user_flows[user_id] = PelacurFlow(character)
        await set_user_mode(user_id, 'role', 'pelacur')
        
        # Start session via flow
        greeting = await _user_flows[user_id].start(
            location=character.booking_location,
            price=character.booking_price,
            duration_hours=character.booking_duration
        )
        
        logger.info(f"Session started for {character.name}")
        await update.message.reply_text(greeting, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Activate pelacur error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def statusrole_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /statusrole - Lihat status role yang aktif"""
    user_id = update.effective_user.id
    settings = get_settings()
    
    if user_id != settings.admin_id:
        return
    
    role = _user_roles.get(user_id)
    if role:
        status_text = role.get_status()
        await update.message.reply_text(status_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "💜 Tidak ada role yang aktif.\n\n"
            "Gunakan `/role therapist` atau `/role pelacur` untuk mulai, Mas.",
            parse_mode='Markdown'
        )


def register_role_commands(app):
    """Register role commands"""
    app.add_handler(CommandHandler("role", role_command))
    app.add_handler(CommandHandler("statusrole", statusrole_command))
