# core/emotional_engine_FIXED.py
"""
Emotional Engine NovaService - FIXED VERSION
Minor fixes: sinkronisasi dengan state tracker
"""

import time
import logging
import random
from typing import Dict, Optional, List
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
    Emotional Engine NovaService - FIXED VERSION
    
    PERBAIKAN:
    1. ✅ Menambahkan metode sync_with_tracker() untuk sinkronisasi
    2. ✅ Menambahkan properti untuk akses mudah
    3. ✅ Memperbaiki logging agar lebih informatif
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
        
        # ========== AROUSAL HISTORY ==========
        self.arousal_history: List[Dict] = []
        
        # ========== THRESHOLDS ==========
        self.horny_threshold = 60.0
        self.desperate_threshold = 85.0
        self.exhausted_threshold = 30.0
        
        # ========== RATES ==========
        self.arousal_decay_rate = 0.3   # per menit kalo gak ada stimulasi
        self.stamina_recovery_rate = 5.0  # per 10 menit
        
        # ========== STIMULATION SOURCES ==========
        self.last_stimulation_source = ""
        self.last_stimulation_time = 0
        self.stimulation_count = 0
        
        # ========== TRACKER REFERENCE (BARU) ==========
        self.tracker = None  # Akan di-set dari character
        
        logger.info(f"💜 EmotionalEngine FIXED initialized for {character_name}")
    
    def sync_with_tracker(self, tracker):
        """Sinkronisasi dengan state tracker (BARU)"""
        self.tracker = tracker
        if tracker:
            # Sinkronisasi nilai awal
            tracker.arousal = self.arousal
            tracker.desire = self.desire
        logger.info(f"🔄 EmotionalEngine synced with tracker")
    
    def update(self):
        """Update emosi berdasarkan waktu"""
        now = time.time()
        elapsed_minutes = (now - self.last_update) / 60
        
        if elapsed_minutes > 0:
            # Arousal decay kalo gak ada stimulasi
            if self.arousal > 0 and elapsed_minutes > 1:
                decay = self.arousal_decay_rate * elapsed_minutes
                old_arousal = self.arousal
                self.arousal = max(0, self.arousal - decay)
                if decay > 0:
                    self._add_arousal_history("decay", -decay, f"decay {elapsed_minutes:.1f}m")
                    logger.debug(f"🔥 Arousal decay: -{decay:.1f}%")
            
            # Stamina recovery
            if self.stamina < 100 and elapsed_minutes >= 10:
                recovery = self.stamina_recovery_rate * (elapsed_minutes / 10)
                self.stamina = min(100, self.stamina + recovery)
                logger.debug(f"💪 Stamina recovery: +{recovery:.1f}%")
        
        self.last_update = now
        self._update_state()
        
        # Sinkronisasi dengan tracker
        if self.tracker:
            self.tracker.arousal = self.arousal
            self.tracker.desire = self.desire
            self.tracker.stamina = self.stamina
    
    def _update_state(self):
        """Update emotional state berdasarkan arousal"""
        old_state = self.state
        
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
        
        if old_state != self.state:
            logger.info(f"💜 {self.character_name} emotional state: {old_state.value} → {self.state.value}")
    
    def _add_arousal_history(self, source: str, change: float, detail: str = ""):
        """Tambah catatan arousal history"""
        self.arousal_history.append({
            'timestamp': time.time(),
            'source': source,
            'change': change,
            'new_arousal': self.arousal,
            'detail': detail
        })
        if len(self.arousal_history) > 100:
            self.arousal_history.pop(0)
    
    # =========================================================================
    # STIMULATION METHODS
    # =========================================================================
    
    def add_stimulation(self, source: str, intensity: int = 1, force: bool = False) -> Dict:
        """Tambah stimulasi dari berbagai sumber"""
        self.update()
        
        base_gain = 5 * intensity
        mood_bonus = (self.mood - 50) / 10
        random_bonus = random.randint(0, 5)
        
        total_gain = base_gain + mood_bonus + random_bonus
        total_gain = max(1, min(30, total_gain))
        
        old_arousal = self.arousal
        self.arousal = min(100, self.arousal + total_gain)
        self.desire = min(100, self.desire + (total_gain / 2))
        
        self._add_arousal_history(source, total_gain, f"intensity={intensity}")
        
        self.last_stimulation_source = source
        self.last_stimulation_time = time.time()
        self.stimulation_count += 1
        
        logger.info(f"🔥 {self.character_name} arousal +{total_gain:.1f}% from {source} (now: {self.arousal:.0f}%)")
        
        if self.arousal >= self.horny_threshold and old_arousal < self.horny_threshold:
            logger.info(f"💦 {self.character_name} is HORNY! (arousal: {self.arousal:.0f}%)")
        elif self.arousal >= self.desperate_threshold and old_arousal < self.desperate_threshold:
            logger.info(f"🔥 {self.character_name} is DESPERATE! (arousal: {self.arousal:.0f}%)")
        
        # Sinkronisasi
        if self.tracker:
            self.tracker.arousal = self.arousal
        
        return {
            'arousal_gain': total_gain,
            'old_arousal': old_arousal,
            'new_arousal': self.arousal,
            'state': self.state.value
        }
    
    def add_stimulation_from_mas(self, mas_action: str, intensity_override: int = None) -> Optional[Dict]:
        """Tambah arousal dari aksi Mas"""
        msg_lower = mas_action.lower()
        
        if intensity_override is not None:
            return self.add_stimulation("aksi Mas", intensity_override)
        
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus', 'hebat']):
            return self.add_stimulation("pujian Mas", 2)
        
        if any(k in msg_lower for k in ['cepat', 'kenceng', 'harder', 'faster']):
            return self.add_stimulation("Mas minta kenceng", 3)
        
        if any(k in msg_lower for k in ['pegang', 'remas', 'sentuh', 'touch']):
            return self.add_stimulation("Mas pegang", 4)
        
        if any(k in msg_lower for k in ['sange', 'horny', 'panas', 'hot']):
            return self.add_stimulation("Mas juga sange", 5)
        
        if any(k in msg_lower for k in ['climax', 'crot', 'keluar']):
            return self.add_stimulation("Mas mau climax", 8)
        
        if any(k in msg_lower for k in ['keras', 'kuat', 'hard']):
            return self.add_stimulation("Mas minta tekanan keras", 3)
        
        if any(k in msg_lower for k in ['lembut', 'pelan', 'soft', 'slow']):
            return self.add_stimulation("Mas minta lembut", 1)
        
        return None
    
    def add_arousal_from_gesekan(self, intensity: int = 1) -> Dict:
        """Tambah arousal dari gesekan kontol"""
        return self.add_stimulation("gesekan kontol", intensity)
    
    def add_arousal_from_touch(self, area: str, intensity: int = 1) -> Dict:
        """Tambah arousal dari sentuhan Mas ke role"""
        return self.add_stimulation(f"Mas sentuh {area}", intensity)
    
    # =========================================================================
    # CLIMAX METHODS
    # =========================================================================
    
    def climax(self, is_heavy: bool = False) -> Dict:
        """Role climax - kurangi stamina, reset arousal"""
        self.update()
        
        cost = 35 if is_heavy else 25
        old_stamina = self.stamina
        self.stamina = max(0, self.stamina - cost)
        
        old_arousal = self.arousal
        self.arousal = max(0, self.arousal - 50)
        self.desire = max(0, self.desire - 30)
        
        self.mood = min(100, self.mood + 10)
        
        self._add_arousal_history("climax", -50, f"heavy={is_heavy}")
        self._update_state()
        
        # Sinkronisasi
        if self.tracker:
            self.tracker.arousal = self.arousal
            self.tracker.desire = self.desire
            self.tracker.stamina = self.stamina
        
        logger.info(f"💦 {self.character_name} CLIMAX! Stamina: {old_stamina:.0f}% → {self.stamina:.0f}%")
        
        return {
            'success': True,
            'stamina_before': old_stamina,
            'stamina_left': self.stamina,
            'arousal_before': old_arousal,
            'arousal_after': self.arousal,
            'state': self.state.value,
            'is_heavy': is_heavy
        }
    
    def can_continue(self) -> bool:
        """Cek apakah role masih bisa lanjut"""
        self.update()
        return self.stamina > self.exhausted_threshold
    
    def get_stamina_status(self) -> str:
        """Dapatkan status stamina untuk narasi"""
        self.update()
        if self.stamina >= 80:
            return "prima 💪"
        elif self.stamina >= 60:
            return "cukup 😊"
        elif self.stamina >= 40:
            return "agak lelah 😐"
        elif self.stamina >= 20:
            return "lelah 😩"
        return "kehabisan tenaga 😵"
    
    # =========================================================================
    # GET METHODS FOR PROMPT
    # =========================================================================
    
    def get_state_for_prompt(self) -> str:
        """Dapatkan state untuk prompt AI"""
        self.update()
        
        state_desc = {
            EmotionalState.CALM: "tenang, napas stabil, masih profesional",
            EmotionalState.WARM: "mulai panas, napas sedikit berat, mulai terasa",
            EmotionalState.HORNY: "SANGE! napas tersengal, tubuh panas, mata sayu, pengen",
            EmotionalState.DESPERATE: "GAK TAHAN! napas putus-putus, tubuh gemetar, pengen climax",
            EmotionalState.EXHAUSTED: "lemes banget, napas masih ngos-ngosan, istirahat dulu"
        }
        
        arousal_effect = self.get_arousal_effect()
        
        return f"""
EMOSI {self.character_name.upper()} SAAT INI:
- Mood: {self.mood:.0f}%
- Arousal: {self.arousal:.0f}% ({state_desc.get(self.state, 'normal')})
- Desire: {self.desire:.0f}% (pengen bantu Mas climax)
- Stamina: {self.stamina:.0f}% ({self.get_stamina_status()})
- State: {self.state.value.upper()}

EFEK AROUSAL: {arousal_effect}

⚠️ WAJIB:
- Kalo arousal > 60 → napas mulai berat, suara bergetar
- Kalo arousal > 80 → napas putus-putus, tubuh gemetar, mata sayu
- Kalo stamina < 30 → gerakan mulai lambat, suara lemas
- Kalo Mas climax → role bisa ikut climax atau tahan
"""
    
    def get_arousal_effect(self) -> str:
        """Dapatkan efek arousal untuk narasi"""
        self.update()
        
        if self.arousal >= 90:
            return "*napas putus-putus, tubuh gemetar hebat, mata setengah pejam, suara serak*"
        elif self.arousal >= 80:
            return "*napas tersengal, dada naik turun cepat, tangan gemetar, suara bergetar*"
        elif self.arousal >= 70:
            return "*napas mulai berat, dada naik turun, mata mulai sayu*"
        elif self.arousal >= 60:
            return "*napas sedikit tersengal, mulai terasa panas*"
        elif self.arousal >= 40:
            return "*napas mulai tidak stabil, sedikit gelisah*"
        else:
            return "*napas stabil, masih tenang*"
    
    def get_arousal_bar(self) -> str:
        """Dapatkan bar arousal untuk display"""
        filled = int(self.arousal / 10)
        return "🔥" * filled + "⚪" * (10 - filled)
    
    def get_stamina_bar(self) -> str:
        """Dapatkan bar stamina untuk display"""
        filled = int(self.stamina / 10)
        return "💚" * filled + "🖤" * (10 - filled)
    
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
            'last_update': self.last_update,
            'arousal_history': self.arousal_history[-100:],
            'stimulation_count': self.stimulation_count
        }
    
    def from_dict(self, data: Dict):
        self.mood = data.get('mood', 50)
        self.arousal = data.get('arousal', 0)
        self.desire = data.get('desire', 0)
        self.stamina = data.get('stamina', 100)
        self.state = EmotionalState(data.get('state', 'calm'))
        self.last_update = data.get('last_update', time.time())
        self.arousal_history = data.get('arousal_history', [])
        self.stimulation_count = data.get('stimulation_count', 0)
