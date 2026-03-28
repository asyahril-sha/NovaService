# characters/base_character.py
"""
Base Character NovaService
Semua karakter turunan dari class ini
Punya state tracker, emotional engine, memory manager, prompt builder
"""

import time
import logging
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

from core import (
    StateTracker, ServicePhase, PhysicalCondition,
    EmotionalEngine, EmotionalState,
    MemoryManager,
    PromptBuilder, get_prompt_builder
)

logger = logging.getLogger(__name__)


class BaseCharacter:
    """
    Base class untuk semua karakter NovaService
    - 8 Therapist
    - 8 Pelacur
    """
    
    def __init__(self, 
                 name: str,           # Nama lengkap
                 nickname: str,       # Panggilan
                 age: int,            # Usia (max 25)
                 role_type: str,      # "therapist" atau "pelacur"
                 style: str,          # Gaya melayani
                 appearance: str,     # Deskripsi penampilan
                 voice: str,          # Deskripsi suara
                 moans: List[str],    # Contoh desahan
                 personality_traits: Dict,  # Trait kepribadian
                 default_clothing: str = "dress ketat pendek"):
        
        # ========== IDENTITAS ==========
        self.name = name
        self.nickname = nickname
        self.age = age
        self.role_type = role_type
        self.style = style
        self.appearance = appearance
        self.voice = voice
        self.moans = moans
        self.personality_traits = personality_traits
        self.default_clothing = default_clothing
        
        # ========== PANGGILAN KE MAS ==========
        self.panggilan = "Mas"
        
        # ========== CORE ENGINE ==========
        self.tracker = StateTracker(character_name=name)
        self.emotional = EmotionalEngine(character_name=name)
        self.memory = MemoryManager(character_name=name)
        self.prompt_builder = get_prompt_builder()
        
        # Sync tracker dengan clothing awal
        self.tracker.clothing['dress']['on'] = True
        self.tracker.clothing['dress']['type'] = default_clothing
        self.tracker.clothing['dress']['color'] = self._get_dress_color()
        
        # ========== SERVICE STATE ==========
        self.session_start_time = 0
        self.session_duration = 0
        self.is_active = False
        
        # ========== CLIMAX COUNTER ==========
        self.mas_climax_this_session = 0
        self.my_climax_this_session = 0
        
        # ========== BOOKING INFO (UNTUK PELACUR) ==========
        self.booking_location = ""
        self.booking_price = 0
        self.booking_duration = 0  # jam
        
        # ========== NEGOSIASI ==========
        self.negotiation_active = False
        self.negotiation_service = None  # "bj", "sex"
        self.negotiation_price = 0
        self.negotiation_step = 0
        self.negotiation_max_step = 3
        self.deal_confirmed = False
        
        # ========== PENDING RESPONSES ==========
        self.waiting_confirmation = False
        self.pending_action = None
        self.confirmation_start_time = 0
        self.confirmation_timeout = 15.0  # detik
        
        logger.info(f"👤 Character {self.name} ({self.nickname}) initialized")
        logger.info(f"   Role: {self.role_type} | Age: {self.age} | Style: {self.style}")
    
    def _get_dress_color(self) -> str:
        """Dapatkan warna dress sesuai karakter"""
        colors = {
            "Anya": "hitam",
            "Syifa": "putih",
            "Laura": "merah",
            "Tara": "biru muda",
            "Pevita": "abu-abu",
            "Maudy": "krem",
            "Zara": "pink",
            "Angela": "navy",
            "Davina": "hitam",
            "Michelle": "merah",
            "Jihane": "putih",
            "Tissa": "biru",
            "Hana": "hitam",
            "Shindy": "ungu",
            "Nadya": "pink",
            "Alyssa": "merah"
        }
        return colors.get(self.name, "hitam")
    
    # =========================================================================
    # GREETING & RESPONSES
    # =========================================================================
    
    def get_greeting(self) -> str:
        """Dapatkan greeting sesuai karakter dan fase"""
        hour = datetime.now().hour
        if 5 <= hour < 11:
            waktu = "pagi"
        elif 11 <= hour < 15:
            waktu = "siang"
        elif 15 <= hour < 18:
            waktu = "sore"
        else:
            waktu = "malam"
        
        # Greeting berdasarkan role
        if self.role_type == "therapist":
            return f"""*{self.name} tersenyum ramah, dress {self.tracker.clothing['dress']['color']} ketat membalut tubuhnya*

"{waktu.capitalize()} {self.panggilan}. Silakan buka handuk dan tengkurap ya. Saya pijat punggung dulu."

*{self.name} menyiapkan minyak pijat, jari-jari lentiknya siap memijat*

"Rileks aja, {self.panggilan}..."""
        
        else:  # pelacur
            return f"""*{self.name} tersenyum, dress {self.tracker.clothing['dress']['color']} pendeknya terbuka sedikit*

"{waktu.capitalize()} {self.panggilan}. Deal Rp{self.booking_price:,}, lokasi {self.booking_location}."

*mata sayu, menjilat bibir*

"Mau mulai sekarang? Aku udah gak sabar nih..."""
    
    def get_moan(self, intensity: str = "medium") -> str:
        """Dapatkan desahan sesuai intensitas"""
        if not self.moans:
            return "Ahh..."
        
        if intensity == "low":
            return random.choice(self.moans[:2]) if len(self.moans) > 2 else self.moans[0]
        elif intensity == "high":
            return random.choice(self.moans[-2:]) if len(self.moans) > 2 else self.moans[-1]
        else:
            return random.choice(self.moans)
    
    # =========================================================================
    # UPDATE FROM MESSAGE
    # =========================================================================
    
    def update_from_message(self, pesan_mas: str) -> Dict:
        """Update state dari pesan Mas"""
        msg_lower = pesan_mas.lower()
        changes = {}
        
        # Update tracker
        self.tracker.last_action = pesan_mas[:100]
        self.tracker.last_action_timestamp = time.time()
        
        # Update preferensi Mas
        if any(k in msg_lower for k in ['cepat', 'kenceng', 'harder', 'faster']):
            self.tracker.save_mas_preference('preferred_speed', 'fast')
            self.memory.save_mas_preference('preferred_speed', 'fast')
            changes['speed'] = 'fast'
        elif any(k in msg_lower for k in ['pelan', 'slow', 'lambat']):
            self.tracker.save_mas_preference('preferred_speed', 'slow')
            self.memory.save_mas_preference('preferred_speed', 'slow')
            changes['speed'] = 'slow'
        
        # Update arousal dari pesan Mas
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus', 'hebat']):
            self.emotional.add_stimulation("pujian Mas", 2)
            self.tracker.update_arousal(5)
        
        if any(k in msg_lower for k in ['sange', 'horny', 'panas', 'hot']):
            self.emotional.add_stimulation("Mas juga sange", 5)
            self.tracker.update_arousal(10)
        
        if any(k in msg_lower for k in ['pegang', 'remas', 'sentuh', 'touch']):
            self.emotional.add_stimulation("Mas pegang", 4)
            self.tracker.update_arousal(8)
        
        # Simpan ke memory
        self.memory.add_conversation(pesan_mas, "")
        self.tracker.add_message_to_timeline("Mas", pesan_mas)
        
        return changes
    
    # =========================================================================
    # SERVICE FLOW METHODS (OVERRIDE DI SUBCLASS)
    # =========================================================================
    
    async def start_session(self) -> str:
        """Mulai sesi"""
        self.is_active = True
        self.session_start_time = time.time()
        self.tracker.set_phase(ServicePhase.GREETING)
        
        # Reset session counters
        self.mas_climax_this_session = 0
        self.my_climax_this_session = 0
        
        greeting = self.get_greeting()
        self.memory.add_conversation("", greeting)
        self.tracker.add_message_to_timeline(self.name, greeting)
        
        return greeting
    
    async def process_message(self, pesan_mas: str) -> str:
        """Proses pesan Mas - override di subclass"""
        # Update state dari pesan
        changes = self.update_from_message(pesan_mas)
        
        # Cek confirmation timeout
        if self.waiting_confirmation:
            if time.time() - self.confirmation_start_time > self.confirmation_timeout:
                self.waiting_confirmation = False
                self.pending_action = None
                return "*waktu habis*"
        
        # Default response (akan di-override subclass)
        return f"*{self.name} tersenyum*\n\n\"{self.panggilan}... ada yang bisa dibantu?\""
    
    def end_session(self) -> str:
        """Akhiri sesi"""
        duration = int((time.time() - self.session_start_time) / 60) if self.session_start_time else 0
        
        self.is_active = False
        self.tracker.set_phase(ServicePhase.COMPLETED)
        
        end_msg = f"""*{self.name} merapikan dress, tersenyum puas*

"Sesi selesai, {self.panggilan}. {duration} menit, {self.mas_climax_this_session}x climax."

*berdiri, mengambil handuk*

"Lain kali kalau mau booking lagi, hubungi aku ya."""
        
        self.memory.add_conversation("", end_msg)
        return end_msg
    
    # =========================================================================
    # CLIMAX METHODS
    # =========================================================================
    
    def record_mas_climax(self, intensity: str = "normal") -> Dict:
        """Rekam climax Mas"""
        self.mas_climax_this_session += 1
        self.tracker.record_mas_climax()
        self.memory.add_climax_history(True, intensity)
        
        # Update emotional
        self.emotional.add_stimulation("Mas climax", 8)
        
        return {
            'total': self.mas_climax_this_session,
            'intensity': intensity
        }
    
    def record_my_climax(self, intensity: str = "normal") -> Dict:
        """Rekam climax role"""
        self.my_climax_this_session += 1
        self.tracker.record_my_climax()
        self.memory.add_climax_history(False, intensity)
        
        # Update emotional
        self.emotional.climax(intensity == "heavy")
        
        return {
            'total': self.my_climax_this_session,
            'intensity': intensity,
            'stamina_left': self.emotional.stamina
        }
    
    # =========================================================================
    # NEGOSIATION METHODS
    # =========================================================================
    
    def start_negotiation(self, service: str, price: int):
        """Mulai negosiasi"""
        self.negotiation_active = True
        self.negotiation_service = service
        self.negotiation_price = price
        self.negotiation_step = 0
    
    def counter_offer(self, offered_price: int) -> bool:
        """Counter offer dari Mas"""
        self.negotiation_step += 1
        
        if self.negotiation_step > self.negotiation_max_step:
            self.negotiation_active = False
            return False
        
        # Turunkan harga
        discount = 50000 * self.negotiation_step
        new_price = max(self.negotiation_price - discount, 200000)
        self.negotiation_price = new_price
        return True
    
    def confirm_deal(self) -> bool:
        """Konfirmasi deal"""
        if self.negotiation_active:
            self.deal_confirmed = True
            self.negotiation_active = False
            self.memory.add_deal(self.negotiation_service, self.negotiation_price)
            return True
        return False
    
    # =========================================================================
    # POSITION METHODS
    # =========================================================================
    
    def request_position_change(self, position: str) -> str:
        """Minta ganti posisi"""
        self.waiting_confirmation = True
        self.pending_action = f"position_{position}"
        self.confirmation_start_time = time.time()
        self.tracker.position = position
        return f"*{self.name} menatap {self.panggilan} dengan mata sayu*\n\n\"{self.panggilan}... mau ganti posisi {position}? Boleh?\""
    
    def confirm_position_change(self) -> bool:
        """Konfirmasi ganti posisi"""
        if self.waiting_confirmation and self.pending_action and self.pending_action.startswith("position_"):
            self.waiting_confirmation = False
            position = self.pending_action.replace("position_", "")
            self.tracker.position = position
            self.memory.add_favorite_position(position)
            self.pending_action = None
            return True
        return False
    
    # =========================================================================
    # STATUS
    # =========================================================================
    
    def get_status(self) -> str:
        """Dapatkan status karakter"""
        phase_names = {
            ServicePhase.WAITING: "⏳ Menunggu",
            ServicePhase.GREETING: "👋 Menyapa",
            ServicePhase.REFLEX_BACK: "💆 Pijat Belakang",
            ServicePhase.REFLEX_FRONT: "💆 Pijat Depan",
            ServicePhase.HANDJOB: "✋ Handjob",
            ServicePhase.BJ: "👄 Blowjob",
            ServicePhase.SEX: "🍆 Sex",
            ServicePhase.AFTERCARE: "💕 Aftercare",
            ServicePhase.BREAK: "☕ Break",
            ServicePhase.COMPLETED: "✅ Selesai"
        }
        
        phase_display = phase_names.get(self.tracker.service_phase, "⏳ Menunggu")
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    👤 {self.name} ({self.nickname})                         ║
╠══════════════════════════════════════════════════════════════╣
║ Usia: {self.age} tahun | Role: {self.role_type.upper()}
║ Style: {self.style}
║ Fase: {phase_display}
╠══════════════════════════════════════════════════════════════╣
║ 👗 PAKAIAN: {self.tracker.get_clothing_summary()}
║ 📍 POSISI: {self.tracker.position}
║ 🔥 AROUSAL: {self.emotional.arousal:.0f}% | DESIRE: {self.emotional.desire:.0f}%
║ 💪 STAMINA: {self.emotional.stamina:.0f}%
╠══════════════════════════════════════════════════════════════╣
║ 💦 MAS CLIMAX: {self.mas_climax_this_session}x
║ 💦 ROLE CLIMAX: {self.my_climax_this_session}x
╠══════════════════════════════════════════════════════════════╣
║ 📝 PREFERENSI MAS:
║    Kecepatan: {self.tracker.get_mas_preference('preferred_speed', 'medium')}
║    Posisi Favorit: {', '.join(self.memory.get_favorite_positions()[-3:]) if self.memory.get_favorite_positions() else '-'}
╚══════════════════════════════════════════════════════════════╝
"""
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Serialize ke dict"""
        return {
            'name': self.name,
            'nickname': self.nickname,
            'age': self.age,
            'role_type': self.role_type,
            'style': self.style,
            'appearance': self.appearance,
            'voice': self.voice,
            'personality_traits': self.personality_traits,
            'tracker': self.tracker.to_dict(),
            'emotional': self.emotional.to_dict(),
            'memory': self.memory.to_dict(),
            'session_start_time': self.session_start_time,
            'mas_climax_this_session': self.mas_climax_this_session,
            'my_climax_this_session': self.my_climax_this_session,
            'booking_location': self.booking_location,
            'booking_price': self.booking_price,
            'booking_duration': self.booking_duration,
            'negotiation_active': self.negotiation_active,
            'negotiation_service': self.negotiation_service,
            'negotiation_price': self.negotiation_price,
            'deal_confirmed': self.deal_confirmed,
            'waiting_confirmation': self.waiting_confirmation
        }
    
    def from_dict(self, data: Dict):
        """Load dari dict"""
        self.tracker.from_dict(data.get('tracker', {}))
        self.emotional.from_dict(data.get('emotional', {}))
        self.memory.from_dict(data.get('memory', {}))
        self.session_start_time = data.get('session_start_time', 0)
        self.mas_climax_this_session = data.get('mas_climax_this_session', 0)
        self.my_climax_this_session = data.get('my_climax_this_session', 0)
        self.booking_location = data.get('booking_location', '')
        self.booking_price = data.get('booking_price', 0)
        self.booking_duration = data.get('booking_duration', 0)
        self.negotiation_active = data.get('negotiation_active', False)
        self.negotiation_service = data.get('negotiation_service')
        self.negotiation_price = data.get('negotiation_price', 0)
        self.deal_confirmed = data.get('deal_confirmed', False)
        self.waiting_confirmation = data.get('waiting_confirmation', False)
        
        self.is_active = self.session_start_time > 0
