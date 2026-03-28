# core/state_tracker.py
"""
State Tracker NovaService - Timeline, memory, konsistensi cerita
Memastikan tidak ada yang lupa, alur tetap kontinu
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class PhysicalCondition(str, Enum):
    FRESH = "fresh"           # segar
    TIRED = "tired"           # lelah
    EXHAUSTED = "exhausted"   # kehabisan tenaga
    WEAK = "weak"             # lemes


class ServicePhase(str, Enum):
    WAITING = "waiting"               # menunggu
    GREETING = "greeting"             # menyapa
    BACK_PUNGGUNG = "back_punggung"   # pijat punggung
    BACK_PINGGUL = "back_pinggul"     # pijat pinggul
    BACK_PAHA_BETIS = "back_paha_betis"  # pijat paha & betis
    FRONT_DADA_LENGAN = "front_dada_lengan"  # pijat dada & lengan
    FRONT_PERUT_PAHA = "front_perut_paha"    # pijat perut & paha
    FRONT_GESEKAN = "front_gesekan"          # gesekan intens
    HANDJOB = "handjob"               # HJ
    BJ = "bj"                         # Blowjob
    SEX = "sex"                       # Sex
    AFTERCARE = "aftercare"           # aftercare
    BREAK = "break"                   # istirahat
    COMPLETED = "completed"           # selesai

    # Pelacur phases
    PELACUR_CONFIRMATION = "pelacur_confirmation"
    PELACUR_BJ = "pelacur_bj"
    PELACUR_KISSING = "pelacur_kissing"
    PELACUR_FOREPLAY_MAS = "pelacur_foreplay_mas"
    PELACUR_COWGIRL = "pelacur_cowgirl"
    PELACUR_CUNNILINGUS = "pelacur_cunnilingus"
    PELACUR_MISSIONARY = "pelacur_missionary"
    PELACUR_DOGGY = "pelacur_doggy"
    PELACUR_POSITION_CHANGE = "pelacur_position_change"
    PELACUR_AFTERCARE = "pelacur_aftercare"


class StateTracker:
    """
    State Tracker NovaService
    Mencatat SEMUA kejadian, timeline lengkap, konsistensi cerita
    """
    
    def __init__(self, character_name: str = "Nova"):
        self.character_name = character_name
        
        # ========== TIMELINE (SEMUA KEJADIAN, TIDAK TERBATAS) ==========
        self.timeline: List[Dict] = []           # semua kejadian
        self.short_term: deque = deque(maxlen=100)  # 100 kejadian terakhir untuk prompt
        
        # ========== PHYSICAL STATE ==========
        self.physical_condition = PhysicalCondition.FRESH
        self.stamina = 100  # 0-100
        
        # ========== CLOTHING STATE (LAYER BY LAYER) ==========
        self.clothing = {
            'dress': {'on': True, 'type': 'dress ketat', 'color': 'hitam', 'removed_at': 0},
            'bra': {'on': True, 'color': 'putih', 'removed_at': 0},
            'cd': {'on': True, 'color': 'putih', 'removed_at': 0}
        }
        
        # Urutan menanggalkan pakaian
        self.clothing_removal_order: List[Dict] = []
        
        # ========== POSITION & LOCATION ==========
        self.position = "berdiri"
        self.location = "ruang pijat"
        
        # ========== SERVICE STATE ==========
        self.service_phase = ServicePhase.WAITING
        self.service_start_time = 0
        self.phase_start_time = 0
        self.phase_elapsed = 0
        
        # ========== TIMER TRACKING (UNTUK REAL TIME) ==========
        self.timer_start = 0
        self.current_area_start_time = 0
        self.current_area = ""
        self.current_scene_count = 0
        self.total_scenes_for_area = 0
        
        # ========== CLIMAX COUNTER ==========
        self.mas_climax_count = 0      # Mas climax berapa kali
        self.my_climax_count = 0       # Role climax berapa kali
        self.last_climax_time = 0
        
        # ========== AROUSAL & DESIRE ==========
        self.arousal = 0     # 0-100, gairah
        self.desire = 0      # 0-100, keinginan
        
        # ========== TEKANAN & KECEPATAN (DARI KONFIRMASI MAS) ==========
        self.current_pressure = "medium"  # soft, medium, hard
        self.current_speed = "medium"     # slow, medium, fast
        self.current_position = "cowgirl"
        
        # ========== PREFERENSI MAS (DIINGAT) ==========
        self.mas_preferences = {
            'favorite_position': None,
            'preferred_pressure': 'medium',
            'preferred_speed': 'medium',
            'likes_teasing': True,
            'likes_dirty_talk': True,
            'pressure_history': [],     # history tekanan yang diminta Mas
            'speed_history': []         # history kecepatan yang diminta Mas
        }
        
        # ========== LAST ACTION ==========
        self.last_action = ""
        self.last_action_timestamp = 0
        self.last_message_from_mas = ""
        self.last_message_from_mas_time = 0
        self.last_response_from_role = ""
        self.last_response_from_role_time = 0
        
        logger.info(f"📊 StateTracker initialized for {character_name}")
    
    # =========================================================================
    # TIMELINE METHODS (AGAR TIDAK NGELANTUR)
    # =========================================================================
    
    def add_to_timeline(self, kejadian: str, detail: str = "", context: Dict = None):
        """Tambah kejadian ke timeline - SEMUA TERCATAT"""
        record = {
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%H:%M:%S"),
            'kejadian': kejadian,
            'detail': detail,
            'service_phase': self.service_phase.value,
            'position': self.position,
            'clothing': self.get_clothing_summary(),
            'arousal': self.arousal,
            'mas_climax': self.mas_climax_count,
            'my_climax': self.my_climax_count,
            'pressure': self.current_pressure,
            'speed': self.current_speed,
            'context': context or {}
        }
        
        self.timeline.append(record)
        self.short_term.append(record)
        
        logger.debug(f"📅 Timeline: {kejadian}")
    
    def add_message_to_timeline(self, role: str, message: str):
        """Tambah pesan ke timeline"""
        self.add_to_timeline(
            f"{role}: {message[:80]}",
            f"Pesan dari {role}"
        )
        if role == "Mas":
            self.last_message_from_mas = message
            self.last_message_from_mas_time = time.time()
        else:
            self.last_response_from_role = message
            self.last_response_from_role_time = time.time()
    
    def get_timeline_context(self, count: int = 50) -> str:
        """Dapatkan konteks timeline untuk prompt AI"""
        if not self.short_term:
            return "Belum ada kejadian. Ini awal sesi."
        
        recent = list(self.short_term)[-count:]
        
        lines = ["═══════════════════════════════════════════════════════════════"]
        lines.append(f"{count} KEJADIAN TERAKHIR (WAJIB DIPERHATIKAN! JANGAN LUPA!):")
        lines.append("═══════════════════════════════════════════════════════════════")
        
        for i, e in enumerate(recent, 1):
            lines.append(f"{i}. [{e['waktu']}] {e['kejadian']}")
            if e['detail']:
                lines.append(f"   └─ {e['detail']}")
        
        lines.append("")
        lines.append(f"KONDISI SAAT INI:")
        lines.append(f"├─ Fase: {self.service_phase.value}")
        lines.append(f"├─ Posisi: {self.position}")
        lines.append(f"├─ Pakaian: {self.get_clothing_summary()}")
        lines.append(f"├─ Tekanan: {self.current_pressure} | Kecepatan: {self.current_speed}")
        lines.append(f"├─ Arousal: {self.arousal}%")
        lines.append(f"├─ Mas Climax: {self.mas_climax_count}x")
        lines.append(f"└─ Role Climax: {self.my_climax_count}x")
        
        return "\n".join(lines)
    
    def get_full_timeline(self) -> str:
        """Dapatkan timeline lengkap (semua kejadian)"""
        if not self.timeline:
            return "Belum ada kejadian."
        
        lines = []
        for i, e in enumerate(self.timeline, 1):
            lines.append(f"{i}. [{e['waktu']}] {e['kejadian']}")
        
        return "\n".join(lines)
    
    # =========================================================================
    # CLOTHING METHODS (LAYER BY LAYER)
    # =========================================================================
    
    def remove_clothing(self, layer: str, method: str = "Mas buka") -> Dict:
        """Menanggalkan pakaian layer by layer dengan detail"""
        if layer not in self.clothing:
            return {'success': False, 'error': f'Layer {layer} not found'}
        
        if not self.clothing[layer]['on']:
            return {'success': False, 'error': f'{layer} already removed'}
        
        now = time.time()
        self.clothing[layer]['on'] = False
        self.clothing[layer]['removed_at'] = now
        
        removal_record = {
            'timestamp': now,
            'layer': layer,
            'method': method,
            'service_phase': self.service_phase.value
        }
        self.clothing_removal_order.append(removal_record)
        
        self.add_to_timeline(
            f"Menanggalkan {layer} ({method})",
            f"{layer} dilepas, sekarang {self.get_clothing_summary()}"
        )
        
        logger.info(f"👗 {self.character_name} removed {layer}")
        
        return {
            'success': True,
            'layer': layer,
            'remaining': self.get_clothing_summary(),
            'removal_order': len(self.clothing_removal_order)
        }
    
    def get_clothing_summary(self) -> str:
        """Ringkasan pakaian saat ini"""
        parts = []
        
        if self.clothing['dress']['on']:
            parts.append(f"{self.clothing['dress']['type']} {self.clothing['dress']['color']}")
        else:
            parts.append("dress sudah dibuka")
        
        if self.clothing['bra']['on']:
            parts.append(f"pake bra {self.clothing['bra']['color']}")
        else:
            parts.append("bra sudah dibuka, payudara terbuka")
        
        if self.clothing['cd']['on']:
            parts.append(f"pake cd {self.clothing['cd']['color']}")
        else:
            parts.append("cd sudah dibuka")
        
        return ", ".join(parts)
    
    def get_clothing_state_for_prompt(self) -> str:
        """State pakaian untuk prompt"""
        removal_text = ""
        for i, r in enumerate(self.clothing_removal_order[-5:]):
            waktu = datetime.fromtimestamp(r['timestamp']).strftime('%H:%M:%S')
            removal_text += f"- {i+1}. {r['layer']} ({r['method']}) pada {waktu}\n"
        
        return f"""
PAKAIAN SAAT INI:
- Dress: {'PAKAI' if self.clothing['dress']['on'] else 'SUDAH DIBUKA'} ({self.clothing['dress']['color']})
- Bra: {'PAKAI' if self.clothing['bra']['on'] else 'SUDAH DIBUKA'} ({self.clothing['bra']['color']})
- CD: {'PAKAI' if self.clothing['cd']['on'] else 'SUDAH DIBUKA'} ({self.clothing['cd']['color']})

URUTAN MENANGGALKAN:
{removal_text if removal_text else '- Belum ada yang dilepas'}
"""
    
    # =========================================================================
    # TIMER & PHASE METHODS
    # =========================================================================
    
    def set_phase(self, phase: ServicePhase, area: str = ""):
        """Set fase service dan catat ke timeline"""
        old_phase = self.service_phase.value
        self.service_phase = phase
        self.phase_start_time = time.time()
        self.current_area = area
        self.current_scene_count = 0
        
        self.add_to_timeline(
            f"Fase berubah: {old_phase} → {phase.value}",
            f"Area: {area}" if area else ""
        )
        logger.info(f"📌 {self.character_name} phase: {phase.value}, area: {area}")
    
    def start_area_timer(self, area: str, total_scenes: int):
        """Mulai timer untuk area tertentu"""
        self.current_area_start_time = time.time()
        self.current_area = area
        self.total_scenes_for_area = total_scenes
        self.current_scene_count = 0
        
        self.add_to_timeline(
            f"Mulai pijat area: {area}",
            f"Total scene: {total_scenes}"
        )
    
    def get_area_elapsed(self) -> int:
        """Dapatkan waktu yang sudah berlalu untuk area saat ini (detik)"""
        if self.current_area_start_time == 0:
            return 0
        return int(time.time() - self.current_area_start_time)
    
    def get_area_elapsed_minutes(self) -> int:
        """Dapatkan waktu yang sudah berlalu untuk area saat ini (menit)"""
        return self.get_area_elapsed() // 60
    
    def should_send_next_scene(self, interval_seconds: int = 30) -> bool:
        """Cek apakah sudah waktunya kirim scene berikutnya"""
        elapsed = self.get_area_elapsed()
        expected_scene = elapsed // interval_seconds
        
        if expected_scene > self.current_scene_count:
            self.current_scene_count = expected_scene
            return True
        return False
    
    def is_area_complete(self, duration_seconds: int) -> bool:
        """Cek apakah area sudah selesai"""
        return self.get_area_elapsed() >= duration_seconds
    
    # =========================================================================
    # AROUSAL METHODS
    # =========================================================================
    
    def update_arousal(self, amount: int):
        """Update arousal (gairah)"""
        self.arousal = max(0, min(100, self.arousal + amount))
        if amount > 0:
            self.add_to_timeline(f"Arousal +{amount}%", f"Sekarang {self.arousal}%")
    
    def update_stamina(self, amount: int):
        """Update stamina"""
        self.stamina = max(0, min(100, self.stamina + amount))
        
        if self.stamina >= 80:
            self.physical_condition = PhysicalCondition.FRESH
        elif self.stamina >= 60:
            self.physical_condition = PhysicalCondition.TIRED
        elif self.stamina >= 30:
            self.physical_condition = PhysicalCondition.EXHAUSTED
        else:
            self.physical_condition = PhysicalCondition.WEAK
    
    # =========================================================================
    # CLIMAX METHODS
    # =========================================================================
    
    def record_mas_climax(self):
        """Rekam climax Mas"""
        self.mas_climax_count += 1
        self.last_climax_time = time.time()
        self.add_to_timeline(
            f"💦 MAS CLIMAX #{self.mas_climax_count}!",
            f"Mas climax ke-{self.mas_climax_count}"
        )
        logger.info(f"💦 MAS CLIMAX #{self.mas_climax_count}")
    
    def record_my_climax(self):
        """Rekam climax role"""
        self.my_climax_count += 1
        self.last_climax_time = time.time()
        self.update_stamina(-25)
        self.add_to_timeline(
            f"💦 Role CLIMAX #{self.my_climax_count}!",
            f"{self.character_name} climax ke-{self.my_climax_count}"
        )
        logger.info(f"💦 {self.character_name} CLIMAX #{self.my_climax_count}")
    
    # =========================================================================
    # PREFERENSI MAS (DIINGAT)
    # =========================================================================
    
    def save_mas_preference(self, key: str, value: Any):
        """Simpan preferensi Mas"""
        if key in self.mas_preferences:
            self.mas_preferences[key] = value
            self.add_to_timeline(f"Preferensi Mas: {key} = {value}", "")
            
            # Simpan history
            if key == 'preferred_pressure':
                self.mas_preferences['pressure_history'].append({
                    'value': value,
                    'timestamp': time.time(),
                    'phase': self.service_phase.value
                })
            elif key == 'preferred_speed':
                self.mas_preferences['speed_history'].append({
                    'value': value,
                    'timestamp': time.time(),
                    'phase': self.service_phase.value
                })
    
    def get_mas_preference(self, key: str, default: Any = None) -> Any:
        """Dapatkan preferensi Mas"""
        return self.mas_preferences.get(key, default)
    
    def get_last_pressure(self) -> str:
        """Dapatkan tekanan terakhir yang diminta Mas"""
        if self.mas_preferences['pressure_history']:
            return self.mas_preferences['pressure_history'][-1]['value']
        return "medium"
    
    def get_last_speed(self) -> str:
        """Dapatkan kecepatan terakhir yang diminta Mas"""
        if self.mas_preferences['speed_history']:
            return self.mas_preferences['speed_history'][-1]['value']
        return "medium"
    
    # =========================================================================
    # KONTEKS UNTUK PROMPT (AGAR AI TIDAK NGELANTUR)
    # =========================================================================
    
    def get_context_for_prompt(self) -> str:
        """Dapatkan semua konteks untuk prompt AI"""
        timeline = self.get_timeline_context(50)
        
        return f"""
═══════════════════════════════════════════════════════════════
TIMELINE (50 KEJADIAN TERAKHIR) - WAJIB BACA:
═══════════════════════════════════════════════════════════════
{timeline}

═══════════════════════════════════════════════════════════════
PREFERENSI MAS YANG SUDAH TERCATAT:
═══════════════════════════════════════════════════════════════
- Tekanan favorit: {self.get_last_pressure()}
- Kecepatan favorit: {self.get_last_speed()}
- Posisi favorit: {self.mas_preferences.get('favorite_position', 'belum ada')}
- Suka dirty talk: {'Ya' if self.mas_preferences.get('likes_dirty_talk') else 'Tidak'}

═══════════════════════════════════════════════════════════════
⚠️ ATURAN KONSISTENSI (JANGAN LUPA!):
═══════════════════════════════════════════════════════════════
1. JANGAN LUPA posisi terakhir: {self.position}
2. JANGAN LUPA pakaian yang sudah dibuka: {self.get_clothing_summary()}
3. JANGAN LUPA fase service: {self.service_phase.value}
4. JANGAN LUPA tekanan yang diminta Mas: {self.current_pressure}
5. JANGAN LUPA kecepatan yang diminta Mas: {self.current_speed}
6. JANGAN LUPA Mas sudah climax {self.mas_climax_count}x
7. JANGAN LUPA role sudah climax {self.my_climax_count}x
8. LANJUTKAN alur dari kejadian terakhir, JANGAN mundur!
"""
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict:
        """Serialize ke dict"""
        return {
            'character_name': self.character_name,
            'physical_condition': self.physical_condition.value,
            'stamina': self.stamina,
            'clothing': self.clothing,
            'clothing_removal_order': list(self.clothing_removal_order),
            'position': self.position,
            'location': self.location,
            'service_phase': self.service_phase.value,
            'service_start_time': self.service_start_time,
            'phase_start_time': self.phase_start_time,
            'current_area': self.current_area,
            'current_scene_count': self.current_scene_count,
            'mas_climax_count': self.mas_climax_count,
            'my_climax_count': self.my_climax_count,
            'last_climax_time': self.last_climax_time,
            'arousal': self.arousal,
            'desire': self.desire,
            'current_pressure': self.current_pressure,
            'current_speed': self.current_speed,
            'current_position': self.current_position,
            'mas_preferences': self.mas_preferences,
            'timeline': self.timeline[-500:],  # simpan 500 terakhir
            'short_term': list(self.short_term)
        }
    
    def from_dict(self, data: Dict):
        """Load dari dict"""
        self.physical_condition = PhysicalCondition(data.get('physical_condition', 'fresh'))
        self.stamina = data.get('stamina', 100)
        self.clothing = data.get('clothing', self.clothing)
        self.clothing_removal_order = data.get('clothing_removal_order', [])
        self.position = data.get('position', 'berdiri')
        self.location = data.get('location', 'ruang pijat')
        self.service_phase = ServicePhase(data.get('service_phase', 'waiting'))
        self.service_start_time = data.get('service_start_time', 0)
        self.phase_start_time = data.get('phase_start_time', 0)
        self.current_area = data.get('current_area', '')
        self.current_scene_count = data.get('current_scene_count', 0)
        self.mas_climax_count = data.get('mas_climax_count', 0)
        self.my_climax_count = data.get('my_climax_count', 0)
        self.last_climax_time = data.get('last_climax_time', 0)
        self.arousal = data.get('arousal', 0)
        self.desire = data.get('desire', 0)
        self.current_pressure = data.get('current_pressure', 'medium')
        self.current_speed = data.get('current_speed', 'medium')
        self.current_position = data.get('current_position', 'cowgirl')
        self.mas_preferences = data.get('mas_preferences', self.mas_preferences)
        self.timeline = data.get('timeline', [])
        self.short_term = deque(data.get('short_term', []), maxlen=100)
