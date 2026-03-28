# service/pelacur_memory.py
"""
Pelacur Memory System - Versi Lengkap & Rapi
Konsistensi penuh untuk role, tidak ngelantur, tidak minta buka celana
"""

import time
import logging
from typing import Dict, List, Optional, Any
from collections import deque

logger = logging.getLogger(__name__)


class PelacurMemory:
    """
    Memory System untuk Pelacur Flow
    Menyimpan semua informasi agar role konsisten dan tidak ngelantur
    
    FITUR:
    - Posisi, gerakan, kecepatan
    - Kondisi tubuh (napas, suhu, gemetar, keringat)
    - Perasaan dan ekspresi
    - Status pakaian Mas (SUDAH TELANJANG)
    - Percakapan dan scene context
    - Climax tracking
    """
    
    def __init__(self, character_name: str = "Nova"):
        self.character_name = character_name
        self.last_update = time.time()
        
        # ========== POSITION & MOVEMENT ==========
        self.last_position: Optional[str] = None          # cowgirl, missionary, doggy, dll
        self.position_changes: List[Dict] = []            # history ganti posisi
        self.last_movement: Optional[str] = None          # naik turun, maju mundur, bergoyang
        self.last_speed: str = "sedang"                   # pelan, sedang, cepat
        self.last_depth: str = "sedang"                   # dangkal, sedang, dalam
        
        # ========== BODY STATE ==========
        self.body_state = {
            'napas': "stabil",        # stabil, berat, tersengal, putus-putus
            'suhu': "normal",         # normal, hangat, panas
            'gemetar': False,         # apakah tubuh gemetar
            'keringat': "sedikit",    # sedikit, banyak, membasahi
            'detak_jantung': "normal", # normal, cepat, kencang
            'otot': "rileks",         # rileks, tegang, kaku
        }
        
        # ========== FEELINGS & EXPRESSIONS ==========
        self.current_feeling: Optional[str] = None        # enak, nikmat, sange, capek, lelah
        self.feeling_history: List[Dict] = []             # history perasaan
        self.last_expression: Optional[str] = None        # mata sayu, bibir tergigit, mata terpejam
        self.last_words: Optional[str] = None             # kata terakhir yang diucapkan
        self.last_sound: Optional[str] = None             # desahan terakhir
        
        # ========== ACTION MEMORY ==========
        self.last_mas_action: Optional[str] = None        # aksi terakhir dari Mas
        self.last_role_response: Optional[str] = None     # respons terakhir role
        self.last_action_time: float = 0                  # waktu interaksi terakhir
        self.interaction_count: int = 0                   # jumlah interaksi
        
        # ========== CONTEXT MEMORY (UNTUK KONSISTENSI) ==========
        self.conversation_context: deque = deque(maxlen=30)   # 30 percakapan terakhir
        self.scene_context: deque = deque(maxlen=20)          # 20 scene terakhir
        
        # ========== STATUS PAKAIAN MAS (KRITIS!) ==========
        self.mas_clothing = {
            'celana': 'SUDAH DIBUKA',      # Mas sudah telanjang dari awal
            'cd': 'SUDAH DIBUKA',          # CD sudah dibuka
            'baju': 'masih pakai',         # Baju masih ada
        }
        
        # ========== CLIMAX TRACKING ==========
        self.mas_climax_count: int = 0          # Total climax Mas
        self.role_climax_count: int = 0         # Total climax Role
        self.cum_locations: List[str] = []      # Lokasi climax
        self.last_cum_time: float = 0           # Waktu climax terakhir
        
        # ========== INTIMACY MOMENTS ==========
        self.intimacy_moments: List[Dict] = []  # Momen intim (pujian, sentuhan)
        self.last_compliment: Optional[str] = None
        self.last_touch_area: Optional[str] = None
        self.position_request: Optional[str] = None
        
        logger.info(f"🧠 PelacurMemory initialized for {character_name}")
        logger.info(f"   Mas clothing status: CELANA SUDAH DIBUKA (jangan minta buka lagi)")
    
    # =========================================================================
    # UPDATE METHODS
    # =========================================================================
    
    def update_from_mas(self, pesan_mas: str):
        """Update memory dari pesan Mas"""
        self.last_mas_action = pesan_mas
        self.last_action_time = time.time()
        self.interaction_count += 1
        
        pesan_lower = pesan_mas.lower()
        
        # Deteksi area sentuhan
        touch_areas = ['paha', 'dada', 'payudara', 'toket', 'pinggul', 'pantat', 'memek', 'klitoris', 'kontol']
        for area in touch_areas:
            if area in pesan_lower:
                self.last_touch_area = area
                break
        
        # Deteksi pujian
        compliments = ['enak', 'mantap', 'bagus', 'hebat', 'keren', 'sexy', 'cantik', 'hot', 'sange']
        for comp in compliments:
            if comp in pesan_lower:
                self.last_compliment = comp
                self.intimacy_moments.append({
                    'type': 'compliment',
                    'content': comp,
                    'time': time.time()
                })
                break
        
        # Deteksi request posisi
        positions = ['cowgirl', 'missionary', 'doggy', 'spooning', 'standing', 'sitting', 'sofa', 'berdiri']
        for pos in positions:
            if pos in pesan_lower:
                self.position_request = pos
                break
        
        # Simpan ke conversation context
        self.conversation_context.append(f"Mas: {pesan_mas[:150]}")
    
    def update_from_response(self, response: str, phase: str):
        """Update memory dari response role (setelah AI generate)"""
        self.last_role_response = response
        self.last_action_time = time.time()
        
        response_lower = response.lower()
        
        # ========== DETEKSI POSISI ==========
        positions = {
            'cowgirl': ['cowgirl', 'duduk di atas', 'naik turun', 'atas kontol'],
            'missionary': ['missionary', 'telentang', 'di bawah', 'mas di atas'],
            'doggy': ['doggy', 'merangkak', 'dari belakang', 'pantat naik'],
            'spooning': ['spooning', 'menyamping', 'dari samping'],
            'standing': ['berdiri', 'standing', 'menempel tembok'],
            'sitting': ['duduk', 'sitting', 'sofa', 'pangkuan']
        }
        
        for pos, keywords in positions.items():
            if any(k in response_lower for k in keywords):
                if self.last_position != pos:
                    self.position_changes.append({
                        'from': self.last_position,
                        'to': pos,
                        'time': time.time(),
                        'phase': phase
                    })
                self.last_position = pos
                break
        
        # ========== DETEKSI GERAKAN ==========
        movements = {
            'naik turun': ['naik turun', 'naik-turun', 'bangkit', 'turun'],
            'maju mundur': ['maju mundur', 'maju-mundur', 'gesek', 'menggesek'],
            'bergoyang': ['bergoyang', 'goyang', 'memutar', 'lingkar'],
            'berputar': ['berputar', 'putar', 'lingkar pinggul']
        }
        
        for movement, keywords in movements.items():
            if any(k in response_lower for k in keywords):
                self.last_movement = movement
                break
        
        # ========== DETEKSI KECEPATAN ==========
        if any(k in response_lower for k in ['cepat', 'kencang', 'fast', 'harder']):
            self.last_speed = 'cepat'
        elif any(k in response_lower for k in ['pelan', 'lambat', 'slow']):
            self.last_speed = 'pelan'
        
        # ========== DETEKSI KONDISI TUBUH ==========
        if any(k in response_lower for k in ['napas putus-putus', 'putus-putus', 'ngos-ngosan']):
            self.body_state['napas'] = 'putus-putus'
        elif any(k in response_lower for k in ['napas tersengal', 'tersengal', 'sengal']):
            self.body_state['napas'] = 'tersengal'
        elif any(k in response_lower for k in ['napas berat', 'berat']):
            self.body_state['napas'] = 'berat'
        
        if any(k in response_lower for k in ['panas', 'gerah', 'hangat']):
            self.body_state['suhu'] = 'panas'
        
        if 'gemetar' in response_lower:
            self.body_state['gemetar'] = True
        
        if any(k in response_lower for k in ['keringat', 'basah', 'membasahi']):
            self.body_state['keringat'] = 'banyak'
        
        # ========== DETEKSI PERASAAN ==========
        feelings = ['enak', 'nikmat', 'puas', 'sange', 'horny', 'capek', 'lelah', 'pusing', 'lemas']
        for feeling in feelings:
            if feeling in response_lower:
                self.current_feeling = feeling
                self.feeling_history.append({
                    'feeling': feeling,
                    'time': time.time(),
                    'phase': phase
                })
                if len(self.feeling_history) > 50:
                    self.feeling_history.pop(0)
                break
        
        # ========== DETEKSI EKSPRESI ==========
        expressions = {
            'mata sayu': ['mata sayu', 'sayu', 'mata setengah pejam'],
            'bibir tergigit': ['bibir tergigit', 'gigit bibir', 'bibir digigit'],
            'mata terpejam': ['mata terpejam', 'pejam', 'terpejam'],
            'dahi berkeringat': ['dahi berkeringat', 'keringat di dahi'],
            'pipi memerah': ['pipi memerah', 'merah', 'blush']
        }
        
        for expr, keywords in expressions.items():
            if any(k in response_lower for k in keywords):
                self.last_expression = expr
                break
        
        # ========== DETEKSI KATA TERAKHIR ==========
        import re
        dialog_match = re.search(r'"([^"]+)"', response)
        if dialog_match:
            self.last_words = dialog_match.group(1)
        
        # ========== DETEKSI DESAHAN ==========
        sounds = ['ahh', 'hhngg', 'uhh', 'aah', 'ohh', 'ya', 'yes']
        for sound in sounds:
            if sound in response_lower:
                self.last_sound = sound
                break
        
        # Simpan ke scene context
        self.scene_context.append(f"{phase}: {response[:100]}...")
        
        # Simpan ke conversation context
        self.conversation_context.append(f"{self.character_name}: {response[:150]}")
    
    def update_body_state(self, **kwargs):
        """Update kondisi tubuh"""
        for key, value in kwargs.items():
            if key in self.body_state:
                old = self.body_state[key]
                if old != value:
                    self.body_state[key] = value
                    logger.debug(f"🫀 Body state: {key} changed from {old} to {value}")
    
    def update_feeling(self, feeling: str, intensity: int = 50):
        """Update perasaan"""
        self.current_feeling = feeling
        self.feeling_history.append({
            'feeling': feeling,
            'intensity': intensity,
            'time': time.time()
        })
        if len(self.feeling_history) > 50:
            self.feeling_history.pop(0)
    
    def update_position(self, position: str, phase: str = ""):
        """Update posisi terakhir"""
        if position == self.last_position:
            return
        
        self.position_changes.append({
            'position': position,
            'time': time.time(),
            'phase': phase,
            'from': self.last_position
        })
        self.last_position = position
    
    def update_movement(self, movement: str, speed: str = None):
        """Update gerakan dan kecepatan"""
        if movement:
            self.last_movement = movement
        if speed:
            self.last_speed = speed
    
    def update_expression(self, expression: str = None, words: str = None, sound: str = None):
        """Update ekspresi"""
        if expression:
            self.last_expression = expression
        if words:
            self.last_words = words
        if sound:
            self.last_sound = sound
    
    def record_action(self, mas_action: str, role_response: str = ""):
        """Rekam aksi dan respons"""
        self.last_mas_action = mas_action
        self.last_role_response = role_response
        self.last_action_time = time.time()
    
    def record_climax(self, is_mas: bool, location: str = "", intensity: str = "normal"):
        """Rekam climax"""
        if is_mas:
            self.mas_climax_count += 1
        else:
            self.role_climax_count += 1
        
        if location:
            self.cum_locations.append(location)
        
        self.last_cum_time = time.time()
        
        logger.info(f"💦 Climax recorded - Mas: {self.mas_climax_count}x, Role: {self.role_climax_count}x")
    
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
        self.last_expression = None
        self.last_words = None
        self.last_sound = None
        self.last_mas_action = None
        self.last_role_response = None
        self.last_touch_area = None
        self.last_compliment = None
        self.position_request = None
        # conversation_context tetap, scene_context tetap
        logger.info(f"🔄 Memory reset for new cycle (climax: Mas={self.mas_climax_count}x, Role={self.role_climax_count}x)")
    
    # =========================================================================
    # GET CONTEXT METHODS (UNTUK PROMPT AI)
    # =========================================================================
    
    def get_position_context(self) -> str:
        """Dapatkan konteks posisi"""
        if not self.last_position:
            return "Posisi: belum ditentukan"
        return f"Posisi saat ini: {self.last_position}"
    
    def get_movement_context(self) -> str:
        """Dapatkan konteks gerakan"""
        if not self.last_movement:
            return "Gerakan: belum ada"
        return f"Gerakan: {self.last_movement} dengan kecepatan {self.last_speed}"
    
    def get_body_state_context(self) -> str:
        """Dapatkan konteks kondisi tubuh"""
        napas_desc = {
            'stabil': "napas stabil, masih terkendali",
            'berat': "napas mulai berat, dada naik turun",
            'tersengal': "napas tersengal, suara mulai bergetar",
            'putus-putus': "napas putus-putus, hampir climax"
        }
        
        suhu_desc = {
            'normal': "suhu tubuh normal",
            'hangat': "tubuh mulai hangat",
            'panas': "tubuh panas, membara"
        }
        
        gemetar_desc = "tubuh gemetar" if self.body_state['gemetar'] else "tubuh masih stabil"
        
        return f"""
KONDISI TUBUH:
- Napas: {napas_desc.get(self.body_state['napas'], self.body_state['napas'])}
- Suhu: {suhu_desc.get(self.body_state['suhu'], self.body_state['suhu'])}
- Gemetar: {gemetar_desc}
- Keringat: {self.body_state['keringat']}
- Detak jantung: {self.body_state['detak_jantung']}
"""
    
    def get_feeling_context(self) -> str:
        """Dapatkan konteks perasaan"""
        if not self.current_feeling:
            return "Perasaan: normal, menikmati"
        
        intensity = self.feeling_history[-1].get('intensity', 50) if self.feeling_history else 50
        intensity_bar = "🔥" * (intensity // 10) + "⚪" * (10 - intensity // 10)
        return f"Perasaan: {self.current_feeling.upper()} {intensity_bar}"
    
    def get_expression_context(self) -> str:
        """Dapatkan konteks ekspresi"""
        parts = []
        if self.last_expression:
            parts.append(f"Ekspresi: {self.last_expression}")
        if self.last_words:
            parts.append(f"Kata terakhir: \"{self.last_words}\"")
        if self.last_sound:
            parts.append(f"Suara: {self.last_sound}")
        return "\n".join(parts) if parts else "Ekspresi: normal"
    
    def get_recent_context(self, count: int = 5) -> str:
        """Dapatkan konteks percakapan terakhir"""
        recent = list(self.conversation_context)[-count:]
        if not recent:
            return "Belum ada percakapan"
        
        lines = []
        for i, ctx in enumerate(recent, 1):
            lines.append(f"{i}. {ctx}")
        return "\n".join(lines)
    
    def get_climax_context(self) -> str:
        """Dapatkan konteks climax"""
        if self.mas_climax_count == 0 and self.role_climax_count == 0:
            return "Belum ada climax"
        
        locations = ", ".join(self.cum_locations) if self.cum_locations else "belum tercatat"
        time_ago = int(time.time() - self.last_cum_time) if self.last_cum_time > 0 else 0
        
        return f"""
RIWAYAT CLIMAX:
- Mas climax: {self.mas_climax_count}x
- Role climax: {self.role_climax_count}x
- Lokasi climax: {locations}
- Terakhir climax: {time_ago} detik yang lalu
"""
    
    def get_mas_clothing_context(self) -> str:
        """Dapatkan konteks status pakaian Mas (KRITIS!)"""
        return f"""
┌───────────────────────────────────────────────────────────────────────────────┐
│ 👕 STATUS PAKAIAN MAS (WAJIB DIPATUHI! JANGAN ULANG!)                        │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Celana: {self.mas_clothing.get('celana', 'SUDAH DIBUKA')}                            │
│ • CD: {self.mas_clothing.get('cd', 'SUDAH DIBUKA')}                                    │
│ • Baju: {self.mas_clothing.get('baju', 'masih pakai')}                                 │
│                                                                               │
│ ⚠️ PERINGATAN WAJIB:                                                          │
│ • Mas SUDAH TELANJANG dari awal sesi!                                         │
│ • JANGAN PERNAH minta Mas buka celana lagi!                                   │
│ • JANGAN PERNAH bicara tentang membuka pakaian!                               │
│ • Fokus pada aktivitas yang sedang berlangsung!                               │
│ • Jika kamu berpikir "buka celana", INGAT: celana sudah terbuka!              │
└───────────────────────────────────────────────────────────────────────────────┘
"""
    
    def get_full_context(self) -> str:
        """Dapatkan SEMUA konteks memory untuk prompt AI (gabungan)"""
        
        # Status napas
        napas_desc = {
            'stabil': "napas masih stabil, belum terpengaruh",
            'berat': "napas sudah mulai berat, dada naik turun",
            'tersengal': "napas tersengal-sengal, mulai tidak terkontrol",
            'putus-putus': "napas putus-putus, nyaris kehabisan napas"
        }
        
        # Status suhu
        suhu_desc = {
            'normal': "suhu tubuh normal",
            'hangat': "tubuh mulai hangat",
            'panas': "tubuh terasa panas, menggairahkan"
        }
        
        return f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         📝 MEMORY ROLE - JANGAN LUPA!                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

{self.get_mas_clothing_context()}

┌───────────────────────────────────────────────────────────────────────────────┐
│ 📍 POSISI & GERAKAN:                                                          │
├───────────────────────────────────────────────────────────────────────────────┤
│ • {self.get_position_context()}                                               │
│ • {self.get_movement_context()}                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ 🫀 KONDISI TUBUH:                                                             │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Napas: {napas_desc.get(self.body_state['napas'], self.body_state['napas'])} │
│ • Suhu: {suhu_desc.get(self.body_state['suhu'], self.body_state['suhu'])}     │
│ • Gemetar: {'Ya' if self.body_state['gemetar'] else 'Tidak'}                  │
│ • Keringat: {self.body_state['keringat']}                                     │
│ • Detak jantung: {self.body_state['detak_jantung']}                           │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ 💖 PERASAAN & EKSPRESI:                                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│ • {self.get_feeling_context()}                                                │
│ • {self.get_expression_context()}                                             │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ 📝 PERCAKAPAN TERAKHIR (5):                                                   │
├───────────────────────────────────────────────────────────────────────────────┤
│ {self.get_recent_context(5)}                                                  │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ 💦 CLIMAX:                                                                    │
├───────────────────────────────────────────────────────────────────────────────┤
│ {self.get_climax_context()}                                                   │
└───────────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════════╗
║ ⚠️ ATURAN KONSISTENSI WAJIB (JANGAN LUPA!):                                   ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ 1. LANJUTKAN dari posisi terakhir: {self.last_position or 'belum ada'}                │
║ 2. LANJUTKAN gerakan: {self.last_movement or 'belum ada'} dengan kecepatan {self.last_speed} │
║ 3. JANGAN LUPA kondisi tubuhmu: napas {self.body_state['napas']}                       │
║ 4. JANGAN MUNDUR! Mas SUDAH TELANJANG dari awal sesi!                          │
║ 5. JANGAN PERNAH minta Mas buka celana lagi!                                  │
║ 6. LANJUTKAN dari percakapan terakhir, jangan ulang dari awal!                │
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
