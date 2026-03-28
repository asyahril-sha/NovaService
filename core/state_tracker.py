# core/state_tracker.py
"""
State Tracker NovaService - Timeline 100 pesan, pakaian layer by layer, konsistensi
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
    REFLEX_BACK = "reflex_back"       # pijat belakang
    REFLEX_FRONT = "reflex_front"     # pijat depan
    VITALITAS_OFFER = "vitalitas_offer"   # ← TAMBAHKAN INI
    HANDJOB = "handjob"               # HJ
    BJ = "bj"                         # Blowjob
    SEX = "sex"                       # Sex
    AFTERCARE = "aftercare"           # aftercare
    BREAK = "break"                   # istirahat
    COMPLETED = "completed"           # selesai


class StateTracker:
    """
    State Tracker NovaService
    Mencatat semua kejadian, timeline 100 pesan terakhir
    """
    
    def __init__(self, character_name: str = "Nova"):
        self.character_name = character_name
        
        # ========== TIMELINE (100 PESAN TERAKHIR) ==========
        self.timeline: deque = deque(maxlen=100)      # 100 kejadian terakhir
        self.short_term: deque = deque(maxlen=50)     # 50 kejadian untuk prompt
        
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
        self.position = "duduk di atas Mas"  # posisi awal therapist
        self.location = "ruang pijat"
        
        # ========== SERVICE STATE ==========
        self.service_phase = ServicePhase.WAITING
        self.service_start_time = 0
        self.service_duration = 0
        
        # ========== CLIMAX COUNTER ==========
        self.mas_climax_count = 0      # Mas climax berapa kali
        self.my_climax_count = 0       # Role climax berapa kali
        self.last_climax_time = 0
        
        # ========== AROUSAL & DESIRE ==========
        self.arousal = 0     # 0-100, gairah
        self.desire = 0      # 0-100, keinginan
        
        # ========== PREFERENSI MAS (DIINGAT) ==========
        self.mas_preferences = {
            'favorite_position': None,
            'preferred_speed': 'medium',  # slow, medium, fast
            'preferred_intensity': 'medium',
            'likes_teasing': True,
            'likes_dirty_talk': True
        }
        
        # ========== LAST ACTION ==========
        self.last_action = ""
        self.last_action_timestamp = 0
        
        logger.info(f"📊 StateTracker initialized for {character_name}")
    
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
        
        # Catat urutan menanggalkan
        removal_record = {
            'timestamp': now,
            'layer': layer,
            'method': method,
            'service_phase': self.service_phase.value
        }
        self.clothing_removal_order.append(removal_record)
        
        # Catat ke timeline
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
    # TIMELINE METHODS (100 PESAN TERAKHIR)
    # =========================================================================
    
    def add_to_timeline(self, kejadian: str, detail: str = ""):
        """Tambah kejadian ke timeline (max 100)"""
        record = {
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%H:%M:%S"),
            'kejadian': kejadian,
            'detail': detail,
            'service_phase': self.service_phase.value,
            'clothing': self.get_clothing_summary(),
            'position': self.position,
            'mas_climax': self.mas_climax_count,
            'my_climax': self.my_climax_count,
            'arousal': self.arousal
        }
        
        self.timeline.append(record)
        self.short_term.append(record)
    
    def add_message_to_timeline(self, role: str, message: str):
        """Tambah pesan ke timeline"""
        self.add_to_timeline(
            f"{role}: {message[:100]}",
            f"Pesan dari {role}"
        )
    
    def get_timeline_context(self, count: int = 50) -> str:
        """Dapatkan konteks timeline untuk prompt (50 terakhir)"""
        if not self.short_term:
            return "Belum ada kejadian."
        
        recent = list(self.short_term)[-count:]
        
        lines = ["═══════════════════════════════════════════════════════════════"]
        lines.append(f"{count} KEJADIAN TERAKHIR (WAJIB DIPERHATIKAN!):")
        lines.append("═══════════════════════════════════════════════════════════════")
        
        for i, e in enumerate(recent, 1):
            lines.append(f"{i}. [{e['waktu']}] {e['kejadian']}")
            if e['detail']:
                lines.append(f"   └─ {e['detail']}")
        
        lines.append("")
        lines.append(f"KONDISI SAAT INI:")
        lines.append(f"├─ Pakaian: {self.get_clothing_summary()}")
        lines.append(f"├─ Posisi: {self.position}")
        lines.append(f"├─ Fase: {self.service_phase.value}")
        lines.append(f"├─ Mas Climax: {self.mas_climax_count}x")
        lines.append(f"├─ Role Climax: {self.my_climax_count}x")
        lines.append(f"├─ Arousal: {self.arousal}%")
        lines.append(f"└─ Stamina: {self.stamina}%")
        
        return "\n".join(lines)
    
    def get_full_timeline(self) -> str:
        """Dapatkan timeline lengkap (100 pesan)"""
        if not self.timeline:
            return "Belum ada kejadian."
        
        lines = []
        for i, e in enumerate(self.timeline, 1):
            lines.append(f"{i}. [{e['waktu']}] {e['kejadian']}")
        
        return "\n".join(lines)
    
    # =========================================================================
    # SERVICE PHASE METHODS
    # =========================================================================
    
    def set_phase(self, phase: ServicePhase):
        """Set fase service dan catat ke timeline"""
        old_phase = self.service_phase.value
        self.service_phase = phase
        self.add_to_timeline(
            f"Fase berubah: {old_phase} → {phase.value}",
            f"Masuk fase {phase.value}"
        )
        logger.info(f"📌 {self.character_name} phase: {phase.value}")
    
    def update_arousal(self, amount: int):
        """Update arousal (gairah)"""
        self.arousal = max(0, min(100, self.arousal + amount))
        if amount > 0:
            self.add_to_timeline(f"Arousal +{amount}%", f"Sekarang {self.arousal}%")
    
    def update_stamina(self, amount: int):
        """Update stamina"""
        self.stamina = max(0, min(100, self.stamina + amount))
        
        # Update physical condition
        if self.stamina >= 80:
            self.physical_condition = PhysicalCondition.FRESH
        elif self.stamina >= 60:
            self.physical_condition = PhysicalCondition.TIRED
        elif self.stamina >= 30:
            self.physical_condition = PhysicalCondition.EXHAUSTED
        else:
            self.physical_condition = PhysicalCondition.WEAK
    
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
        self.update_stamina(-25)  # Climax kurangi stamina
        self.add_to_timeline(
            f"💦 Role CLIMAX #{self.my_climax_count}!",
            f"{self.character_name} climax ke-{self.my_climax_count}"
        )
        logger.info(f"💦 {self.character_name} CLIMAX #{self.my_climax_count}")
    
    # =========================================================================
    # PREFERENSI MAS
    # =========================================================================
    
    def save_mas_preference(self, key: str, value: Any):
        """Simpan preferensi Mas"""
        if key in self.mas_preferences:
            self.mas_preferences[key] = value
            self.add_to_timeline(f"Preferensi Mas: {key} = {value}", "")
    
    def get_mas_preference(self, key: str, default: Any = None) -> Any:
        """Dapatkan preferensi Mas"""
        return self.mas_preferences.get(key, default)
    
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
            'mas_climax_count': self.mas_climax_count,
            'my_climax_count': self.my_climax_count,
            'last_climax_time': self.last_climax_time,
            'arousal': self.arousal,
            'desire': self.desire,
            'mas_preferences': self.mas_preferences,
            'timeline': list(self.timeline),
            'short_term': list(self.short_term)
        }
    
    def from_dict(self, data: Dict):
        """Load dari dict"""
        self.physical_condition = PhysicalCondition(data.get('physical_condition', 'fresh'))
        self.stamina = data.get('stamina', 100)
        self.clothing = data.get('clothing', self.clothing)
        self.clothing_removal_order = data.get('clothing_removal_order', [])
        self.position = data.get('position', 'duduk di atas Mas')
        self.location = data.get('location', 'ruang pijat')
        self.service_phase = ServicePhase(data.get('service_phase', 'waiting'))
        self.service_start_time = data.get('service_start_time', 0)
        self.mas_climax_count = data.get('mas_climax_count', 0)
        self.my_climax_count = data.get('my_climax_count', 0)
        self.last_climax_time = data.get('last_climax_time', 0)
        self.arousal = data.get('arousal', 0)
        self.desire = data.get('desire', 0)
        self.mas_preferences = data.get('mas_preferences', self.mas_preferences)
        self.timeline = deque(data.get('timeline', []), maxlen=100)
        self.short_term = deque(data.get('short_term', []), maxlen=50)
