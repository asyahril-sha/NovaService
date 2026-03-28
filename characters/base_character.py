# characters/base_character.py
"""
Base Character NovaService - Semua karakter turunan dari class ini
Punya personality, memory, state tracker, dan service flow
"""

import time
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import deque

from core.state_tracker import StateTracker, ServicePhase, PhysicalCondition
from core.emotional_engine import EmotionalEngine, EmotionalStyle
from core.relationship import RelationshipManager, RelationshipPhase

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
        
        # ========== STATE TRACKER ==========
        self.tracker = StateTracker(character_name=name)
        
        # Sync tracker dengan clothing awal
        self.tracker.clothing['dress']['on'] = True
        self.tracker.clothing['dress']['type'] = default_clothing
        self.tracker.clothing['dress']['color'] = self._get_dress_color()
        
        # ========== EMOTIONAL ENGINE ==========
        self.emotional = EmotionalEngine()
        
        # ========== RELATIONSHIP (LEVEL SYSTEM) ==========
        self.relationship = RelationshipManager()
        self.relationship.level = 7  # Start level 7
        self.relationship.phase = RelationshipPhase.CLOSE
        
        # ========== CONVERSATIONS (100 PESAN TERAKHIR) ==========
        self.conversations: deque = deque(maxlen=100)
        
        # ========== SERVICE STATE ==========
        self.service_phase = ServicePhase.WAITING
        self.session_start_time = 0
        self.session_duration = 0
        
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
        self.deal_confirmed = False
        
        # ========== PENDING RESPONSES ==========
        self._pending_response = False
        self._response_type = None
        
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
        if intensity == "low":
            return random.choice(self.moans[:3]) if len(self.moans) > 3 else self.moans[0]
        elif intensity == "high":
            return random.choice(self.moans[-3:]) if len(self.moans) > 3 else self.moans[-1]
        else:
            return random.choice(self.moans)
    
    # =========================================================================
    # MEMORY METHODS
    # =========================================================================
    
    def add_conversation(self, mas_msg: str, role_msg: str = ""):
        """Tambah percakapan ke memory (max 100)"""
        self.conversations.append({
            'timestamp': time.time(),
            'mas': mas_msg[:500],
            'role': role_msg[:500]
        })
        
        # Juga tambah ke tracker timeline
        if mas_msg:
            self.tracker.add_message_to_timeline("Mas", mas_msg)
        if role_msg:
            self.tracker.add_message_to_timeline(self.name, role_msg)
    
    def get_recent_conversations(self, count: int = 100) -> str:
        """Dapatkan percakapan terakhir"""
        if not self.conversations:
            return "Belum ada percakapan."
        
        recent = list(self.conversations)[-count:]
        lines = []
        
        for i, conv in enumerate(recent, 1):
            if conv.get('mas'):
                lines.append(f"[{i}] Mas: {conv['mas']}")
            if conv.get('role'):
                lines.append(f"[{i}] {self.name}: {conv['role']}")
        
        return "\n".join(lines)
    
    # =========================================================================
    # UPDATE FROM MESSAGE
    # =========================================================================
    
    def update_from_message(self, pesan_mas: str) -> Dict:
        """Update state dari pesan Mas"""
        msg_lower = pesan_mas.lower()
        changes = {}
        
        # Update preferensi Mas
        if 'cepat' in msg_lower or 'kenceng' in msg_lower:
            self.tracker.save_mas_preference('preferred_speed', 'fast')
            changes['speed'] = 'fast'
        elif 'pelan' in msg_lower:
            self.tracker.save_mas_preference('preferred_speed', 'slow')
            changes['speed'] = 'slow'
        
        # Update arousal dari pesan Mas
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus']):
            self.tracker.update_arousal(5)
        
        if any(k in msg_lower for k in ['sange', 'horny', 'panas']):
            self.tracker.update_arousal(10)
        
        # Update stamina kalo Mas minta lebih
        if any(k in msg_lower for k in ['lebih', 'tambah', 'lagi']):
            self.tracker.update_stamina(-5)
        
        # Simpan ke memory
        self.add_conversation(pesan_mas, "")
        
        return changes
    
    # =========================================================================
    # SERVICE FLOW METHODS (OVERRIDE DI SUBCLASS)
    # =========================================================================
    
    async def start_session(self) -> str:
        """Mulai sesi - override di subclass"""
        self.session_start_time = time.time()
        self.tracker.set_phase(ServicePhase.GREETING)
        return self.get_greeting()
    
    async def process_message(self, pesan_mas: str) -> str:
        """Proses pesan Mas - override di subclass"""
        self.update_from_message(pesan_mas)
        
        # Default response
        return f"*{self.name} tersenyum*\n\n\"{self.panggilan}... ada yang bisa dibantu?\""
    
    def end_session(self) -> str:
        """Akhiri sesi"""
        duration = int((time.time() - self.session_start_time) / 60) if self.session_start_time else 0
        
        self.tracker.set_phase(ServicePhase.COMPLETED)
        
        return f"""*{self.name} merapikan dress, tersenyum puas*

"Sesi selesai, {self.panggilan}. {duration} menit, {self.mas_climax_this_session}x climax."

*berdiri, mengambil handuk*

"Lain kali kalau mau booking lagi, hubungi aku ya."""
    
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
║ 🔥 AROUSAL: {self.tracker.arousal}% | DESIRE: {self.tracker.desire}%
║ 💪 STAMINA: {self.tracker.stamina}%
╠══════════════════════════════════════════════════════════════╣
║ 💦 MAS CLIMAX: {self.mas_climax_this_session}x
║ 💦 ROLE CLIMAX: {self.my_climax_this_session}x
╠══════════════════════════════════════════════════════════════╣
║ 📝 PREFERENSI MAS:
║    Posisi Favorit: {self.tracker.get_mas_preference('favorite_position', '-')}
║    Kecepatan: {self.tracker.get_mas_preference('preferred_speed', 'medium')}
║    Intensitas: {self.tracker.get_mas_preference('preferred_intensity', 'medium')}
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
            'relationship': self.relationship.to_dict(),
            'conversations': list(self.conversations),
            'service_phase': self.service_phase.value,
            'session_start_time': self.session_start_time,
            'mas_climax_this_session': self.mas_climax_this_session,
            'my_climax_this_session': self.my_climax_this_session,
            'booking_location': self.booking_location,
            'booking_price': self.booking_price
        }
    
    def from_dict(self, data: Dict):
        """Load dari dict"""
        self.tracker.from_dict(data.get('tracker', {}))
        self.emotional.from_dict(data.get('emotional', {}))
        self.relationship.from_dict(data.get('relationship', {}))
        self.conversations = deque(data.get('conversations', []), maxlen=100)
        self.service_phase = ServicePhase(data.get('service_phase', 'waiting'))
        self.session_start_time = data.get('session_start_time', 0)
        self.mas_climax_this_session = data.get('mas_climax_this_session', 0)
        self.my_climax_this_session = data.get('my_climax_this_session', 0)
        self.booking_location = data.get('booking_location', '')
        self.booking_price = data.get('booking_price', 0)


# Helper untuk random
import random
