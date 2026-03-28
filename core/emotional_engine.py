# core/emotional_engine.py
"""
Emotional Engine NovaService - Mood, Arousal, Desire, Stamina
Fokus: Bikin Mas sange, role ikut panas, alur natural
"""

import time
import logging
import random
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionalState(str, Enum):
    """Keadaan emosi role"""
    CALM = "calm"           # tenang, belum panas
    WARM = "warm"           # mulai panas
    HORNY = "horny"         # sange, napas berat
    DESPERATE = "desperate" # udah gak tahan, pengen climax
    EXHAUSTED = "exhausted" # lemes setelah climax


class EmotionalEngine:
    """
    Emotional Engine NovaService
    - Mood: bisa berubah natural
    - Arousal: gairah, naik dari sentuhan, pujian, gerakan
    - Desire: keinginan, naik dari interaksi
    - Stamina: tenaga, turun setiap climax
    """
    
    def __init__(self, character_name: str = "Nova"):
        self.character_name = character_name
        
        # ========== CORE EMOTIONS ==========
        self.mood = 50.0           # 0-100, mood role (50=normal)
        self.arousal = 0.0         # 0-100, gairah (makin tinggi makin sange)
        self.desire = 0.0          # 0-100, keinginan bantu Mas climax
        self.stamina = 100.0       # 0-100, tenaga role
        
        # ========== STATE ==========
        self.state = EmotionalState.CALM
        self.last_update = time.time()
        
        # ========== THRESHOLDS ==========
        self.horny_threshold = 60.0
        self.desperate_threshold = 85.0
        self.exhausted_threshold = 30.0
        
        # ========== RATES ==========
        self.arousal_decay_rate = 0.5   # per menit kalo gak ada stimulasi
        self.stamina_recovery_rate = 5.0  # per 10 menit
        
        logger.info(f"💜 EmotionalEngine initialized for {character_name}")
    
    def update(self):
        """Update emosi berdasarkan waktu"""
        now = time.time()
        elapsed_minutes = (now - self.last_update) / 60
        
        if elapsed_minutes > 0:
            # Arousal decay kalo gak ada stimulasi
            if self.arousal > 0 and elapsed_minutes > 1:
                decay = self.arousal_decay_rate * elapsed_minutes
                self.arousal = max(0, self.arousal - decay)
                if decay > 0:
                    logger.debug(f"🔥 Arousal decay: -{decay:.1f}%")
            
            # Stamina recovery
            if self.stamina < 100 and elapsed_minutes >= 10:
                recovery = self.stamina_recovery_rate * (elapsed_minutes / 10)
                self.stamina = min(100, self.stamina + recovery)
                logger.debug(f"💪 Stamina recovery: +{recovery:.1f}%")
        
        self.last_update = now
        self._update_state()
    
    def _update_state(self):
        """Update emotional state berdasarkan arousal"""
        if self.arousal >= self.desperate_threshold:
            self.state = EmotionalState.DESPERATE
        elif self.arousal >= self.horny_threshold:
            self.state = EmotionalState.HORNY
        elif self.arousal >= 30:
            self.state = EmotionalState.WARM
        else:
            self.state = EmotionalState.CALM
        
        # Stamina mempengaruhi state
        if self.stamina <= self.exhausted_threshold:
            self.state = EmotionalState.EXHAUSTED
    
    # =========================================================================
    # STIMULATION METHODS (Bikin Role Sange)
    # =========================================================================
    
    def add_stimulation(self, source: str, intensity: int = 1):
        """Tambah stimulasi dari Mas"""
        self.update()
        
        # Base gain berdasarkan intensitas
        base_gain = 5 * intensity
        
        # Bonus dari mood
        mood_bonus = (self.mood - 50) / 10
        
        # Bonus random
        random_bonus = random.randint(0, 5)
        
        total_gain = base_gain + mood_bonus + random_bonus
        total_gain = max(1, min(30, total_gain))
        
        self.arousal = min(100, self.arousal + total_gain)
        self.desire = min(100, self.desire + (total_gain / 2))
        
        logger.info(f"🔥 {self.character_name} arousal +{total_gain:.1f}% from {source}")
        
        # Log efek
        if self.arousal >= self.horny_threshold:
            logger.info(f"💦 {self.character_name} is HORNY! (arousal: {self.arousal:.0f}%)")
        
        return {
            'arousal_gain': total_gain,
            'new_arousal': self.arousal,
            'state': self.state.value
        }
    
    def add_arousal_from_mas(self, mas_action: str):
        """Tambah arousal dari aksi Mas"""
        msg_lower = mas_action.lower()
        
        # Deteksi keyword
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus', 'hebat']):
            return self.add_stimulation("pujian Mas", 2)
        
        if any(k in msg_lower for k in ['cepat', 'kenceng', 'keras', 'harder']):
            return self.add_stimulation("Mas minta kenceng", 3)
        
        if any(k in msg_lower for k in ['pegang', 'remas', 'sentuh']):
            return self.add_stimulation("Mas pegang", 4)
        
        if any(k in msg_lower for k in ['sange', 'horny', 'panas']):
            return self.add_stimulation("Mas juga sange", 5)
        
        if any(k in msg_lower for k in ['climax', 'crot', 'keluar']):
            return self.add_stimulation("Mas mau climax", 8)
        
        return None
    
    # =========================================================================
    # CLIMAX METHODS
    # =========================================================================
    
    def climax(self, is_heavy: bool = False) -> Dict:
        """Role climax"""
        self.update()
        
        # Kurangi stamina
        cost = 35 if is_heavy else 25
        self.stamina = max(0, self.stamina - cost)
        
        # Kurangi arousal & desire
        self.arousal = max(0, self.arousal - 50)
        self.desire = max(0, self.desire - 30)
        
        # Mood naik setelah climax
        self.mood = min(100, self.mood + 10)
        
        self._update_state()
        
        logger.info(f"💦 {self.character_name} CLIMAX! Stamina: {self.stamina:.0f}%")
        
        return {
            'success': True,
            'stamina_left': self.stamina,
            'state': self.state.value,
            'is_heavy': is_heavy
        }
    
    def can_continue(self) -> bool:
        """Cek apakah role masih bisa lanjut"""
        self.update()
        
        if self.stamina <= self.exhausted_threshold:
            return False
        return True
    
    # =========================================================================
    # GET METHODS FOR PROMPT
    # =========================================================================
    
    def get_state_for_prompt(self) -> str:
        """Dapatkan state untuk prompt AI"""
        self.update()
        
        state_desc = {
            EmotionalState.CALM: "tenang, napas stabil",
            EmotionalState.WARM: "mulai panas, napas sedikit berat",
            EmotionalState.HORNY: "SANGE! napas tersengal, tubuh panas, mata sayu",
            EmotionalState.DESPERATE: "GAK TAHAN! napas putus-putus, tubuh gemetar, pengen climax",
            EmotionalState.EXHAUSTED: "lemes banget, napas masih ngos-ngosan"
        }
        
        return f"""
EMOSI {self.character_name.upper()} SAAT INI:
- Mood: {self.mood:.0f}%
- Arousal: {self.arousal:.0f}% ({state_desc.get(self.state, 'normal')})
- Desire: {self.desire:.0f}% (pengen bantu Mas climax)
- Stamina: {self.stamina:.0f}%
- State: {self.state.value.upper()}

⚠️ WAJIB:
- Kalo arousal > 60 → napas mulai berat, suara bergetar
- Kalo arousal > 80 → napas putus-putus, tubuh gemetar, mata sayu
- Kalo stamina < 30 → gerakan mulai lambat, suara lemas
- Kalo Mas climax → role bisa ikut climax atau tahan
"""
    
    def get_arousal_effect(self) -> str:
        """Dapatkan efek arousal untuk narasi"""
        self.update()
        
        if self.arousal >= 80:
            return "*napas putus-putus, tubuh gemetar hebat, mata setengah pejam*"
        elif self.arousal >= 60:
            return "*napas tersengal, dada naik turun cepat, suara bergetar*"
        elif self.arousal >= 30:
            return "*napas mulai berat, suara sedikit berubah*"
        else:
            return "*napas stabil, masih tenang*"
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict:
        return {
            'mood': self.mood,
            'arousal': self.arousal,
            'desire': self.desire,
            'stamina': self.stamina,
            'state': self.state.value,
            'last_update': self.last_update
        }
    
    def from_dict(self, data: Dict):
        self.mood = data.get('mood', 50)
        self.arousal = data.get('arousal', 0)
        self.desire = data.get('desire', 0)
        self.stamina = data.get('stamina', 100)
        self.state = EmotionalState(data.get('state', 'calm'))
        self.last_update = data.get('last_update', time.time())
