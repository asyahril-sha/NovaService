# service/pelacur_flow_FIXED.py
"""
Pelacur Flow NovaService - FIXED VERSION
- Booking 6 jam FULL BOOKING (bebas berapa kali sesi)
- Setiap sesi Mas bisa climax kapan saja, tidak dibatasi
- Role bisa climax kapan saja (natural, tanpa minta izin)
- Memory system AGAR TIDAK NGELANTUR (ingat posisi, gerakan, perasaan)
- Manual mode dengan AI (respons dinamis, tidak hardcoded)
- Auto phase: BJ (30 menit), Kissing (30 menit) dengan timing fixed
- Warning booking otomatis setiap 1 jam dan 30 menit sebelum selesai
- Loop otomatis setelah satu cycle selesai (dengan konfirmasi)
"""

import asyncio
import time
import logging
import re
import random
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime
from enum import Enum

from core import ServicePhase, StateTracker
from core.prompt_builder import get_prompt_builder
from core.emotional_engine import EmotionalEngine
from config import get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# MEMORY SYSTEM - AGAR ROLE TIDAK NGELANTUR
# =============================================================================

class PelacurMemory:
    """
    Memory System untuk Pelacur Flow
    Menyimpan semua informasi agar role konsisten dan tidak ngelantur
    """
    
    def __init__(self, character_name: str = "Nova"):
        self.character_name = character_name
        
        # ========== POSITION & MOVEMENT ==========
        self.last_position: Optional[str] = None          # cowgirl, missionary, doggy, dll
        self.position_changes: List[Dict] = []            # history ganti posisi
        self.last_movement: Optional[str] = None          # naik turun, maju mundur, bergoyang
        self.last_speed: str = "sedang"                   # pelan, sedang, cepat
        self.last_depth: str = "sedang"                   # dangkal, sedang, dalam (untuk BJ)
        
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
        self.last_sound: Optional[str] = None             # desahan terakhir (ahh, hhngg, dll)
        
        # ========== WHAT JUST HAPPENED ==========
        self.last_action_from_mas: Optional[str] = None   # aksi terakhir dari Mas
        self.last_response_from_role: Optional[str] = None # respons terakhir role
        self.last_interaction_time: float = 0              # waktu interaksi terakhir
        self.interaction_count: int = 0                    # jumlah interaksi dalam sesi
        
        # ========== INTIMACY BUILDUP ==========
        self.intimacy_moments: List[Dict] = []             # momen-momen intim yang terjadi
        self.last_compliment: Optional[str] = None         # pujian terakhir dari Mas
        self.last_touch_area: Optional[str] = None         # area terakhir yang disentuh Mas
        
        logger.info(f"🧠 PelacurMemory initialized for {character_name}")
    
    def update_from_response(self, response: str, phase: str):
        """Ekstrak dan simpan informasi dari response role"""
        
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
        # Napas
        if any(k in response_lower for k in ['napas putus-putus', 'putus-putus', 'ngos-ngosan']):
            self.body_state['napas'] = 'putus-putus'
        elif any(k in response_lower for k in ['napas tersengal', 'tersengal', 'sengal']):
            self.body_state['napas'] = 'tersengal'
        elif any(k in response_lower for k in ['napas berat', 'berat']):
            self.body_state['napas'] = 'berat'
        
        # Suhu
        if any(k in response_lower for k in ['panas', 'gerah', 'hangat']):
            self.body_state['suhu'] = 'panas'
        
        # Gemetar
        if 'gemetar' in response_lower:
            self.body_state['gemetar'] = True
        
        # Keringat
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
                # Keep last 50
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
        dialog_match = re.search(r'"([^"]+)"', response)
        if dialog_match:
            self.last_words = dialog_match.group(1)
        
        # ========== DETEKSI DESAHAN ==========
        sounds = ['ahh', 'hhngg', 'uhh', 'aah', 'ohh', 'ya', 'yes']
        for sound in sounds:
            if sound in response_lower:
                self.last_sound = sound
                break
        
        # Update waktu interaksi
        self.last_response_from_role = response
        self.last_interaction_time = time.time()
        self.interaction_count += 1
    
    def update_from_mas(self, pesan_mas: str):
        """Update memory dari pesan Mas"""
        self.last_action_from_mas = pesan_mas
        
        pesan_lower = pesan_mas.lower()
        
        # Deteksi area sentuhan
        touch_areas = ['paha', 'dada', 'payudara', 'toket', 'pinggul', 'pantat', 'memek', 'klitoris']
        for area in touch_areas:
            if area in pesan_lower:
                self.last_touch_area = area
                break
        
        # Deteksi pujian
        compliments = ['enak', 'mantap', 'bagus', 'hebat', 'keren', 'sexy', 'cantik']
        for comp in compliments:
            if comp in pesan_lower:
                self.last_compliment = comp
                self.intimacy_moments.append({
                    'type': 'compliment',
                    'content': comp,
                    'time': time.time()
                })
                break
    
    def get_memory_context(self) -> str:
        """Dapatkan konteks memory untuk prompt AI"""
        
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
║                         📝 MEMORY ROLE (JANGAN LUPA!)                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────────────────────┐
│ POSISI & GERAKAN:                                                             │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Posisi terakhir: {self.last_position or 'belum ditentukan'}                          │
│ • Gerakan terakhir: {self.last_movement or 'belum ada'}                                 │
│ • Kecepatan: {self.last_speed}                                                          │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ KONDISI TUBUH SAAT INI:                                                        │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Napas: {napas_desc.get(self.body_state['napas'], self.body_state['napas'])}                 │
│ • Suhu tubuh: {suhu_desc.get(self.body_state['suhu'], self.body_state['suhu'])}               │
│ • Gemetar: {'Ya, tubuh mulai gemetar' if self.body_state['gemetar'] else 'Tidak, masih stabil'} │
│ • Keringat: {self.body_state['keringat']}                                                     │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ PERASAAN & EKSPRESI:                                                           │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Perasaan: {self.current_feeling or 'normal, menikmati'}                               │
│ • Ekspresi: {self.last_expression or 'normal, menatap Mas'}                            │
│ • Kata terakhir: "{self.last_words or 'belum bicara'}"                                    │
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ APA YANG BARU SAJA TERJADI:                                                    │
├───────────────────────────────────────────────────────────────────────────────┤
│ • Aksi Mas terakhir: {self.last_action_from_mas[:100] if self.last_action_from_mas else 'belum ada'} │
│ • Area disentuh: {self.last_touch_area or 'belum ada'}                                    │
│ • Interaksi ke-{self.interaction_count} dalam sesi ini                                   │
└───────────────────────────────────────────────────────────────────────────────┘

⚠️ ATURAN KONSISTENSI (WAJIB DIPATUHI!):
1. JANGAN LUPA POSISI TERAKHIR! Kamu sedang di posisi {self.last_position or 'belum ditentukan'}
2. JANGAN LUPA GERAKAN TERAKHIR! Lanjutkan gerakan {self.last_movement or 'yang sedang kamu lakukan'}
3. JANGAN LUPA KONDISI TUBUHMU! Napasmu {napas_desc.get(self.body_state['napas'], self.body_state['napas'])}
4. JANGAN TIBA-TIBA BERUBAH! Jika napasmu berat, jangan tiba-tiba jadi normal
5. LANJUTKAN CERITA! Jangan mundur ke kejadian yang sudah lewat
6. RESPONLAH SECARA NATURAL! Tunjukkan apa yang kamu rasakan saat ini
"""


# =============================================================================
# MAIN CLASS: PelacurFlow
# =============================================================================

class PelacurFlow:
    """
    Alur service Pelacur dengan AI generate setiap scene - FIXED VERSION
    
    FITUR:
    - Booking 6 jam FULL BOOKING
    - Bebas climax kapan saja (natural)
    - Memory system agar tidak ngelantur
    - Manual mode dengan AI (dinamis)
    - Auto phase: BJ (30 menit), Kissing (30 menit)
    - Warning booking natural setiap 1 jam
    - Loop otomatis dengan konfirmasi
    """
    
    # ========== DURASI KONFIGURASI ==========
    TOTAL_BOOKING_HOURS = 6                    # 6 jam total
    TOTAL_BOOKING_SECONDS = TOTAL_BOOKING_HOURS * 3600  # 21600 detik
    
    BJ_DURATION = 1800                         # 30 menit
    KISSING_DURATION = 1800                    # 30 menit
    SCENE_INTERVAL = 30                        # 30 detik per scene
    
    # Scene count untuk auto phase
    BJ_SCENES = 60                             # 30 menit / 30 detik
    KISSING_SCENES = 60                        # 30 menit / 30 detik
    
    # ========== WARNING SCHEDULE (NATURAL) ==========
    # Waktu dalam detik sejak mulai booking
    WARNING_SCHEDULE = {
        3600: "Mas... udah 1 jam kita bareng... masih kuat?",           # 1 jam
        7200: "Wah, udah 2 jam Mas... aku masih pengen terus sama Mas...",  # 2 jam
        10800: "3 jam Mas... luar biasa... belum pernah kayak gini...",      # 3 jam
        14400: "4 jam ya Mas... aku masih nggak mau berhenti...",            # 4 jam
        18000: "Mas... tinggal 1 jam lagi... aku bakal kangen...",           # 5 jam (1 jam sisa)
        19800: "30 menit lagi ya Mas... masih mau lanjut?",                  # 5.5 jam (30 menit sisa)
        21000: "10 menit lagi Mas... aku pengen banget sama Mas...",         # 5.83 jam (10 menit sisa)
        21540: "1 menit lagi Mas... aku sayang Mas...",                      # 5.98 jam (1 menit sisa)
    }
    
    # Warning yang sudah dikirim (agar tidak spam)
    _sent_warnings: List[int] = []
    
    def __init__(self, character):
        """Inisialisasi PelacurFlow dengan memory system"""
        self.character = character
        self.prompt_builder = get_prompt_builder()
        self._ai_client = None
        
        # ========== MEMORY SYSTEM ==========
        self.memory = PelacurMemory(character.name)
        
        # ========== BOOKING STATE ==========
        self.is_active = False
        self.booking_start_time = 0
        self.booking_end_time = 0
        self.current_cycle = 1
        self.max_cycles = 3                      # 6 jam / 2 jam per cycle = 3 cycle
        self.cycle_start_time = 0
        
        # ========== PHASE STATE ==========
        self.current_phase = ServicePhase.WAITING
        self.current_phase_name = "confirmation"  # confirmation, bj, kissing, foreplay, cowgirl, cunnilingus, missionary, doggy, position_change, aftercare
        self.phase_start_time = 0
        self.auto_send_active = False
        self.manual_mode_active = False
        self.manual_mode_type = None
        
        # ========== TIMER TRACKING ==========
        self.scene_count = 0
        self.total_scenes = 0
        
        # ========== CLIMAX TRACKING (NATURAL, TIDAK DIBATASI) ==========
        self.mas_climax_count = 0                # Total climax Mas sepanjang sesi
        self.role_climax_count = 0               # Total climax role sepanjang sesi
        self.last_climax_time = 0
        self.waiting_climax_confirmation = False  # TIDAK DIGUNAKAN LAGI (natural)
        
        # ========== WAITING FOR RESPONSE ==========
        self.waiting_for_response = False
        self.waiting_for_type = None              # "start_cycle", "continue_cycle", dll
        self.waiting_start_time = 0
        self.WAITING_TIMEOUT = 60
        
        # ========== AFTERCARE ==========
        self.aftercare_active = False
        
        # ========== CONVERSATION HISTORY (untuk manual mode) ==========
        self.conversation_history: List[str] = []
        
        # ========== AUTO SEND TASK ==========
        self.auto_send_task = None
        self.auto_send_running = False
        
        logger.info(f"🔥 PelacurFlow FIXED initialized for {character.name}")
        logger.info(f"   Booking duration: {self.TOTAL_BOOKING_HOURS} hours")
        logger.info(f"   Auto phases: BJ ({self.BJ_DURATION//60} min), Kissing ({self.KISSING_DURATION//60} min)")
