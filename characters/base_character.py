# characters/base_character.py
"""
Base Character NovaService
Semua karakter turunan dari class ini
Punya state tracker, emotional engine, memory manager, prompt builder
Dilengkapi sistem climax dengan pemberitahuan
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
        
        # ========== CLIMAX WARNING SYSTEM ==========
        self.waiting_climax_confirmation = False
        self.climax_warning_time = 0
        self.climax_warning_timeout = 15.0  # detik, kalo gak respon, climax aja
        
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
            "Sallsa": "merah"
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
    # CLIMAX WARNING SYSTEM
    # =========================================================================
    
    def _get_climax_warning(self) -> str:
        """Dapatkan pesan peringatan climax sesuai karakter"""
        warnings = {
            "Anya": "*napas Anya mulai tersengal, tangannya gemetar*\n\n\"Mas... aku mau climax... bentar lagi... boleh ikut?\"",
            "Syifa": "*Syifa menggigit bibir, napasnya putus-putus*\n\n\"Mas... aku udah mau climax... ikut ya?\"",
            "Laura": "*Laura menarik napas dalam, tubuhnya tegang*\n\n\"Aku mau climax... sekarang.\"",
            "Tara": "*Tara meremas tangan Mas, tubuhnya gemetar*\n\n\"Mas... aku... mau climax...\"",
            "Pevita": "*Pevita menahan napas, gerakan mulai tidak stabil*\n\n\"Aku mau climax... cepetin ya Mas?\"",
            "Maudy": "*Maudy mendesah pelan, mata mulai sayu*\n\n\"Mas... aku mau...\"",
            "Zara": "*Zara memeluk Mas erat, napasnya tersengal*\n\n\"Mas! aku... mau climax!\"",
            "Angela": "*Angela menggigit bibir, tangan meremas sprei*\n\n\"Mas... aku mau climax...\"",
            "Davina": "*Davina menatap Mas dengan mata tajam*\n\n\"Aku mau climax. Lihat.\"",
            "Michelle": "*Michelle menggenggam tangan Mas erat*\n\n\"Mas... aku mau climax... ikut ya?\"",
            "Jihane": "*Jihane menahan napas, tubuhnya gemetar hebat*\n\n\"Aku climax... sekarang juga.\"",
            "Tissa": "*Tissa memejamkan mata, tubuh gemetar*\n\n\"Mas... ajarin... aku mau climax...\"",
            "Hana": "*Hana menghentikan gerakan, menatap Mas*\n\n\"Aku mau climax. Mas cepetin?\"",
            "Shindy": "*Shindy mendekat ke telinga Mas, napasnya panas*\n\n\"Mas... aku mau climax... bentar lagi...\"",
            "Nadya": "*Nadya memeluk Mas erat, tubuhnya gemetar kecil*\n\n\"Mas... aku... udah mau...\"",
            "Sallsa": "*Sallsa menahan napas, tubuhnya tegang*\n\n\"Aku climax! Sekarang!\""
        }
        return warnings.get(self.name, "*napas mulai berat, tubuh gemetar*\n\n\"Aku mau climax...\"")
    
    def check_and_notify_climax(self) -> Optional[str]:
        """
        Cek apakah role mau climax.
        Kalo iya, kasih tau Mas dulu.
        Returns: pesan notifikasi atau None
        """
        # Cek arousal (>= 85) dan belum dalam mode waiting
        if self.emotional.arousal >= 85 and not self.waiting_climax_confirmation:
            self.waiting_climax_confirmation = True
            self.climax_warning_time = time.time()
            
            # Kasih tau Mas
            warning = self._get_climax_warning()
            self.tracker.add_message_to_timeline(self.name, warning[:100])
            return warning
        
        # Kalo udah waiting tapi timeout (gak respon), climax aja
        if self.waiting_climax_confirmation:
            if time.time() - self.climax_warning_time > self.climax_warning_timeout:
                self.waiting_climax_confirmation = False
                return None  # Biar process_message yang handle climax
        
        return None
    
    def confirm_climax(self, mas_response: str = "") -> Dict:
        """
        Konfirmasi climax setelah Mas respon
        - Kalo Mas bilang "cepetin" / "kenceng" → climax cepat
        - Kalo Mas bilang "tahan" / "jangan" → tahan dulu
        - Kalo Mas diam / respon lain → climax normal
        """
        msg_lower = mas_response.lower()
        
        # Reset flag
        self.waiting_climax_confirmation = False
        
        # Cek respon Mas
        if any(k in msg_lower for k in ['cepet', 'kenceng', 'harder', 'faster', 'gas', 'ayo']):
            # Climax cepat
            result = self.record_my_climax(intensity="heavy")
            result['status'] = 'fast_climax'
            return result
        
        elif any(k in msg_lower for k in ['tahan', 'jangan', 'wait', 'stop', 'nunggu']):
            # Tahan climax
            self.emotional.arousal = max(0, self.emotional.arousal - 20)
            self.tracker.add_to_timeline("Menahan climax", "Karena Mas minta tahan")
            return {
                'status': 'delayed',
                'message': f"*{self.name} menahan napas, tubuh masih gemetar*\n\n\"Aku tahan... cepet ya Mas...\""
            }
        
        else:
            # Climax normal
            result = self.record_my_climax(intensity="normal")
            result['status'] = 'normal_climax'
            return result
    
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
    # SERVICE FLOW METHODS
    # =========================================================================
    
    async def start_session(self) -> str:
        """Mulai sesi"""
        self.is_active = True
        self.session_start_time = time.time()
        self.tracker.set_phase(ServicePhase.GREETING)
        
        # Reset session counters
        self.mas_climax_this_session = 0
        self.my_climax_this_session = 0
        self.waiting_climax_confirmation = False
        
        greeting = self.get_greeting()
        self.memory.add_conversation("", greeting)
        self.tracker.add_message_to_timeline(self.name, greeting)
        
        return greeting
    
    async def process_message(self, pesan_mas: str) -> str:
        """Proses pesan Mas - akan di-override di subclass"""
        # Update state dari pesan
        changes = self.update_from_message(pesan_mas)
        
        # Cek confirmation timeout
        if self.waiting_confirmation:
            if time.time() - self.confirmation_start_time > self.confirmation_timeout:
                self.waiting_confirmation = False
                self.pending_action = None
                return "*waktu habis*"
        
        # Cek climax warning (kalo role mau climax)
        climax_warning = self.check_and_notify_climax()
        if climax_warning:
            return climax_warning
        
        # Default response (akan di-override subclass)
        return f"*{self.name} tersenyum*\n\n\"{self.panggilan}... ada yang bisa dibantuan?\""
    
    async def process_climax_response(self, pesan_mas: str) -> str:
        """Proses respon Mas setelah climax warning"""
        result = self.confirm_climax(pesan_mas)
        
        if result.get('status') == 'delayed':
            return result.get('message', "*menahan napas*")
        elif result.get('status') == 'fast_climax':
            return self._get_climax_response(intensity="heavy")
        else:
            return self._get_climax_response(intensity="normal")
    
    def _get_climax_response(self, intensity: str = "normal") -> str:
        """Dapatkan respons climax sesuai karakter"""
        climax_responses = {
            "Anya": f"*Anya memeluk Mas erat, tubuhnya gemetar*\n\n\"Ahh... {self.panggilan}... climax... uhh...\"",
            "Syifa": f"*Syifa teriak, tubuh melengkung*\n\n\"Ahhh!! {self.panggilan}!! climax... lemes...\"",
            "Laura": f"*Laura menahan napas, lalu melepaskannya*\n\n\"Ahh... puas.\"",
            "Tara": f"*Tara meremas tangan Mas, tubuh gemetar*\n\n\"Mas... aku... climax...\"",
            "Pevita": f"*Pevita mendesah dalam, tubuhnya rileks*\n\n\"Ahh... selesai.\"",
            "Maudy": f"*Maudy memejamkan mata, napas panjang*\n\n\"Hmm... makasih Mas...\"",
            "Zara": f"*Zara memeluk Mas, napas putus-putus*\n\n\"Ahhh! Mas! climax! uhh...\"",
            "Angela": f"*Angela menggigit bibir, tubuh gemetar*\n\n\"Ahh... Mas... puas...\"",
            "Davina": f"*Davina mendesah keras, tubuh melengkung*\n\n\"Ahh... puas. Bagus.\"",
            "Michelle": f"*Michelle memeluk Mas, mata berkaca*\n\n\"Mas... makasih... aku climax...\"",
            "Jihane": f"*Jihane memeluk Mas erat, napas panjang*\n\n\"Ahh... puas. Besok lagi.\"",
            "Tissa": f"*Tissa memejamkan mata, tubuh gemetar*\n\n\"Ahhh... Mas... ajarin lagi...\"",
            "Hana": f"*Hana menghela napas panjang*\n\n\"Ahh... puas. Mas gimana?\"",
            "Shindy": f"*Shindy memeluk Mas, napasnya panas di telinga*\n\n\"Ahh... Mas... makasih...\"",
            "Nadya": f"*Nadya memeluk Mas, tubuhnya gemetar kecil*\n\n\"Mas... aku... climax... lemes...\"",
            "Sallsa": f"*Sallsa mendesah brutal, tubuh tegang lalu lemas*\n\n\"Ahh! climax! puas!\""
        }
        return climax_responses.get(self.name, f"*{self.name} gemetar, napas putus-putus*\n\n\"Ahh... climax...\"")
    
    def end_session(self) -> str:
        """Akhiri sesi"""
        duration = int((time.time() - self.session_start_time) / 60) if self.session_start_time else 0
        
        self.is_active = False
        self.waiting_climax_confirmation = False
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
        
        # Reset climax warning flag
        self.waiting_climax_confirmation = False
        
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
        
        position_responses = {
            "cowgirl": f"*{self.name} menatap {self.panggilan} dengan mata sayu*\n\n\"{self.panggilan}... mau ganti posisi cowgirl? Aku di atas ya...\"",
            "missionary": f"*{self.name} berbaring, menarik {self.panggilan} ke atas*\n\n\"{self.panggilan}... missionary... ayo...\"",
            "doggy": f"*{self.name} merangkak, pantat naik*\n\n\"{self.panggilan}... doggy... dari belakang...\"",
            "spooning": f"*{self.name} miring, menarik {self.panggilan} dari belakang*\n\n\"{self.panggilan}... spooning... peluk aku...\"",
            "standing": f"*{self.name} berdiri, menempel ke tembok*\n\n\"{self.panggilan}... standing... ayo...\"",
            "sitting": f"*{self.name} duduk di pangkuan {self.panggilan}*\n\n\"{self.panggilan}... sitting... aku duduk di atas...\""
        }
        return position_responses.get(position, f"*{self.name} menatap {self.panggilan}*\n\n\"{self.panggilan}... ganti posisi {position}? Boleh?\"")
    
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
        
        climax_status = "⏳ Menunggu konfirmasi" if self.waiting_climax_confirmation else "✅ Siap"
        
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
║ 💦 CLIMAX: {climax_status}
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
            'waiting_climax_confirmation': self.waiting_climax_confirmation,
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
        self.waiting_climax_confirmation = data.get('waiting_climax_confirmation', False)
        self.booking_location = data.get('booking_location', '')
        self.booking_price = data.get('booking_price', 0)
        self.booking_duration = data.get('booking_duration', 0)
        self.negotiation_active = data.get('negotiation_active', False)
        self.negotiation_service = data.get('negotiation_service')
        self.negotiation_price = data.get('negotiation_price', 0)
        self.deal_confirmed = data.get('deal_confirmed', False)
        self.waiting_confirmation = data.get('waiting_confirmation', False)
        
        self.is_active = self.session_start_time > 0
