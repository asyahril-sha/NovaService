# service/pelacur_memory.py
"""
Pelacur Memory System - Konsistensi penuh untuk role
Mengingat posisi, gerakan, perasaan, kondisi tubuh, ekspresi
"""

import time
import logging
from typing import Dict, List, Optional, Any
from collections import deque

logger = logging.getLogger(__name__)


class PelacurMemory:
    """
    Memory system untuk pelacur - AGAR TIDAK NGELANTUR
    Role mengingat:
    - Posisi terakhir dan history ganti posisi
    - Gerakan dan kecepatan
    - Kondisi tubuh (napas, suhu, gemetar, keringat)
    - Perasaan dan ekspresi
    - Kata-kata terakhir
    - Aksi terakhir dari Mas dan response role
    """
    
    def __init__(self, character_name: str = "Nova"):
        self.character_name = character_name
        
        # ========== POSITION MEMORY ==========
        self.last_position: Optional[str] = None
        self.position_history: List[Dict] = []  # [{position, time, phase}]
        self.position_changes_count = 0
        
        # ========== MOVEMENT MEMORY ==========
        self.last_movement: Optional[str] = None  # "naik turun", "maju mundur", "bergoyang", "berputar"
        self.last_speed: str = "sedang"  # "pelan", "sedang", "cepat"
        self.movement_history: List[Dict] = []
        
        # ========== BODY STATE MEMORY ==========
        self.body_state = {
            'napas': 'stabil',        # "stabil", "berat", "tersengal", "putus-putus"
            'suhu': 'normal',          # "normal", "hangat", "panas"
            'gemetar': False,
            'keringat': 'sedikit',     # "sedikit", "banyak", "membasahi"
            'detak_jantung': 'normal', # "normal", "cepat", "kencang"
            'otot': 'rileks',          # "rileks", "tegang", "kaku"
        }
        
        # ========== FEELING MEMORY ==========
        self.current_feeling: Optional[str] = None  # "enak", "nikmat", "panas", "pengen climax", "lelah"
        self.feeling_history: List[Dict] = []
        self.intensity_level: int = 0  # 0-100, seberapa intens perasaan
        
        # ========== EXPRESSION MEMORY ==========
        self.last_expression: Optional[str] = None  # "mata sayu", "bibir tergigit", "mata terpejam", dll
        self.last_words: Optional[str] = None
        self.last_sound: Optional[str] = None  # "desahan", "teriak", "erangan"
        
        # ========== ACTION MEMORY ==========
        self.last_mas_action: Optional[str] = None
        self.last_role_response: Optional[str] = None
        self.last_action_time: float = 0
        
        # ========== CONTINUITY CHECK ==========
        self.conversation_context: deque = deque(maxlen=20)  # 20 percakapan terakhir
        self.scene_context: deque = deque(maxlen=10)  # 10 scene terakhir
        
        # ========== INTIMATE CUMULATIVE ==========
        self.cum_count: int = 0  # Sudah berapa kali climax
        self.cum_locations: List[str] = []  # Di mana climax terjadi
        self.last_cum_time: float = 0
        
        logger.info(f"🧠 PelacurMemory initialized for {character_name}")
    
    # =========================================================================
    # POSITION MEMORY
    # =========================================================================
    
    def update_position(self, position: str, phase: str = ""):
        """Update posisi terakhir"""
        if position == self.last_position:
            return
        
        self.position_history.append({
            'position': position,
            'time': time.time(),
            'phase': phase,
            'from': self.last_position
        })
        self.last_position = position
        self.position_changes_count += 1
        
        logger.info(f"📌 Position changed to {position} (total: {self.position_changes_count})")
    
    def get_position_context(self) -> str:
        """Dapatkan konteks posisi untuk prompt"""
        if not self.last_position:
            return "Belum ada posisi"
        
        history_str = ""
        if len(self.position_history) > 1:
            last_change = self.position_history[-2]
            history_str = f" (sebelumnya {last_change['position']})"
        
        return f"Posisi saat ini: {self.last_position}{history_str}"
    
    # =========================================================================
    # MOVEMENT MEMORY
    # =========================================================================
    
    def update_movement(self, movement: str, speed: str = None):
        """Update gerakan dan kecepatan"""
        if movement:
            self.last_movement = movement
            self.movement_history.append({
                'movement': movement,
                'time': time.time()
            })
            if len(self.movement_history) > 20:
                self.movement_history.pop(0)
        
        if speed:
            self.last_speed = speed
        
        logger.info(f"💃 Movement: {movement}, speed: {self.last_speed}")
    
    def get_movement_context(self) -> str:
        """Dapatkan konteks gerakan"""
        if not self.last_movement:
            return "Belum ada gerakan"
        
        return f"Gerakan: {self.last_movement} dengan kecepatan {self.last_speed}"
    
    # =========================================================================
    # BODY STATE MEMORY
    # =========================================================================
    
    def update_body_state(self, **kwargs):
        """Update kondisi tubuh"""
        for key, value in kwargs.items():
            if key in self.body_state:
                old = self.body_state[key]
                self.body_state[key] = value
                if old != value:
                    logger.info(f"🫀 Body state: {key} changed from {old} to {value}")
    
    def get_body_state_context(self) -> str:
        """Dapatkan konteks kondisi tubuh"""
        napas_desc = {
            'stabil': 'napas stabil, masih terkendali',
            'berat': 'napas mulai berat, dada naik turun',
            'tersengal': 'napas tersengal, suara mulai bergetar',
            'putus-putus': 'napas putus-putus, hampir climax'
        }
        
        suhu_desc = {
            'normal': 'suhu tubuh normal',
            'hangat': 'tubuh mulai hangat',
            'panas': 'tubuh panas, membara'
        }
        
        gemetar_desc = "tubuh gemetar" if self.body_state['gemetar'] else "tubuh masih stabil"
        
        return f"""
KONDISI TUBUH SAAT INI:
- Napas: {napas_desc.get(self.body_state['napas'], self.body_state['napas'])}
- Suhu: {suhu_desc.get(self.body_state['suhu'], self.body_state['suhu'])}
- Gemetar: {gemetar_desc}
- Keringat: {self.body_state['keringat']}
- Detak jantung: {self.body_state['detak_jantung']}
"""
    
    # =========================================================================
    # FEELING MEMORY
    # =========================================================================
    
    def update_feeling(self, feeling: str, intensity: int = None):
        """Update perasaan"""
        self.current_feeling = feeling
        self.feeling_history.append({
            'feeling': feeling,
            'intensity': intensity or self.intensity_level,
            'time': time.time()
        })
        if len(self.feeling_history) > 30:
            self.feeling_history.pop(0)
        
        if intensity is not None:
            self.intensity_level = min(100, max(0, intensity))
        
        logger.info(f"💖 Feeling: {feeling} (intensity: {self.intensity_level})")
    
    def get_feeling_context(self) -> str:
        """Dapatkan konteks perasaan"""
        if not self.current_feeling:
            return "Belum ada perasaan tertentu"
        
        intensity_bar = "🔥" * (self.intensity_level // 10) + "⚪" * (10 - self.intensity_level // 10)
        return f"""
PERASAAN SAAT INI: {self.current_feeling.upper()}
INTENSITAS: {self.intensity_level}% {intensity_bar}
"""
    
    # =========================================================================
    # EXPRESSION MEMORY
    # =========================================================================
    
    def update_expression(self, expression: str = None, words: str = None, sound: str = None):
        """Update ekspresi, kata-kata, dan suara"""
        if expression:
            self.last_expression = expression
        if words:
            self.last_words = words
        if sound:
            self.last_sound = sound
    
    def get_expression_context(self) -> str:
        """Dapatkan konteks ekspresi"""
        parts = []
        if self.last_expression:
            parts.append(f"Ekspresi: {self.last_expression}")
        if self.last_words:
            parts.append(f"Kata terakhir: \"{self.last_words}\"")
        if self.last_sound:
            parts.append(f"Suara: {self.last_sound}")
        
        return "\n".join(parts) if parts else "Belum ada ekspresi"
    
    # =========================================================================
    # ACTION MEMORY
    # =========================================================================
    
    def record_action(self, mas_action: str, role_response: str = ""):
        """Rekam aksi dan respons"""
        self.last_mas_action = mas_action
        self.last_role_response = role_response
        self.last_action_time = time.time()
        
        self.conversation_context.append({
            'mas': mas_action[:200],
            'role': role_response[:200] if role_response else "",
            'time': self.last_action_time
        })
    
    def get_recent_context(self, count: int = 5) -> str:
        """Dapatkan konteks percakapan terakhir"""
        recent = list(self.conversation_context)[-count:]
        if not recent:
            return "Belum ada percakapan"
        
        lines = []
        for i, ctx in enumerate(recent, 1):
            lines.append(f"{i}. Mas: {ctx['mas']}")
            if ctx['role']:
                lines.append(f"   {self.character_name}: {ctx['role']}")
        return "\n".join(lines)
    
    # =========================================================================
    # CLIMAX MEMORY
    # =========================================================================
    
    def record_climax(self, is_mas: bool, location: str = "", intensity: str = "normal"):
        """Rekam climax"""
        self.cum_count += 1
        if location:
            self.cum_locations.append(location)
        self.last_cum_time = time.time()
        
        logger.info(f"💦 CLIMAX #{self.cum_count} recorded - {'Mas' if is_mas else 'Role'} - {location}")
    
    def get_climax_context(self) -> str:
        """Dapatkan konteks climax"""
        if self.cum_count == 0:
            return "Belum ada climax"
        
        locations = ", ".join(self.cum_locations) if self.cum_locations else "belum tercatat"
        return f"""
RIWAYAT CLIMAX:
- Total climax: {self.cum_count}x
- Lokasi climax: {locations}
- Terakhir climax: {int(time.time() - self.last_cum_time)} detik yang lalu
"""
    
    # =========================================================================
    # CONTINUITY CHECK
    # =========================================================================
    
    def get_full_context(self) -> str:
        """Dapatkan semua konteks memory untuk prompt"""
        return f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🧠 MEMORY {self.character_name.upper()} - JANGAN LUPA!                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────────────────────┐
│ 📍 POSISI & GERAKAN                                                           │
├───────────────────────────────────────────────────────────────────────────────┤
│ {self.get_position_context()}                                                 │
│ {self.get_movement_context()}                                                 │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ 🫀 KONDISI TUBUH                                                              │
├───────────────────────────────────────────────────────────────────────────────┤
│ {self.get_body_state_context()}                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ 💖 PERASAAN & EKSPRESI                                                        │
├───────────────────────────────────────────────────────────────────────────────┤
│ {self.get_feeling_context()}                                                  │
│ {self.get_expression_context()}                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ 📝 PERCAKAPAN TERAKHIR                                                        │
├───────────────────────────────────────────────────────────────────────────────┤
│ {self.get_recent_context(5)}                                                  │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ 💦 CLIMAX                                                                     │
├───────────────────────────────────────────────────────────────────────────────┤
│ {self.get_climax_context()}                                                   │
└───────────────────────────────────────────────────────────────────────────────┘

⚠️ ATURAN KONSISTENSI WAJIB:
1. LANJUTKAN dari posisi terakhir: {self.last_position or 'belum ada'}
2. LANJUTKAN gerakan: {self.last_movement or 'belum ada'} dengan kecepatan {self.last_speed}
3. JANGAN LUPA kondisi tubuhmu: napas {self.body_state['napas']}, {self.body_state['suhu']}
4. JANGAN LUPA perasaanmu: {self.current_feeling or 'normal'}
5. JANGAN MUNDUR waktu! Lanjutkan dari percakapan terakhir!
"""
    
    # =========================================================================
    # RESET FOR NEW CYCLE
    # =========================================================================
    
    def reset_for_new_cycle(self):
        """Reset memory untuk cycle baru (tapi tetap ingat climax history)"""
        self.last_position = None
        self.last_movement = None
        self.last_speed = "sedang"
        self.body_state = {
            'napas': 'stabil',
            'suhu': 'normal',
            'gemetar': False,
            'keringat': 'sedikit',
            'detak_jantung': 'normal',
            'otot': 'rileks',
        }
        self.current_feeling = None
        self.intensity_level = 0
        self.last_expression = None
        self.last_words = None
        self.last_sound = None
        self.last_mas_action = None
        self.last_role_response = None
        # conversation_context tetap, scene_context tetap
        logger.info(f"🔄 Memory reset for new cycle (climax history preserved: {self.cum_count}x)")
