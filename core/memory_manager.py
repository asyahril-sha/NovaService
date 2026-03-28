# core/memory_manager.py
"""
Memory Manager NovaService - 100 pesan terakhir, timeline, long-term memory
Memastikan tidak ada yang lupa, alur tetap konsisten
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory Manager NovaService
    - 100 pesan terakhir (short-term)
    - Timeline kejadian
    - Long-term memory (preferensi Mas, momen penting)
    """
    
    def __init__(self, character_name: str = "Nova"):
        self.character_name = character_name
        
        # ========== SHORT-TERM MEMORY (100 PESAN TERAKHIR) ==========
        self.conversations: deque = deque(maxlen=100)  # 100 pesan terakhir
        
        # ========== TIMELINE (100 KEJADIAN TERAKHIR) ==========
        self.timeline: deque = deque(maxlen=100)       # 100 kejadian terakhir
        
        # ========== LONG-TERM MEMORY ==========
        self.long_term: Dict[str, List] = {
            'mas_preferences': [],      # preferensi Mas (posisi, kecepatan, dll)
            'mas_habits': [],           # kebiasaan Mas
            'important_moments': [],    # momen penting
            'deals_made': [],           # deal harga yang pernah terjadi
            'favorite_positions': [],   # posisi favorit Mas dari history
            'climax_history': []        # history climax Mas
        }
        
        # ========== STATE SAAT INI (AGAR KONSISTEN) ==========
        self.current_state = {
            'position': None,
            'clothing': None,
            'phase': None,
            'mas_climax_count': 0,
            'my_climax_count': 0,
            'last_action': None,
            'last_action_time': 0
        }
        
        logger.info(f"🧠 MemoryManager initialized for {character_name}")
        logger.info(f"   Max conversations: 100 | Max timeline: 100")
    
    # =========================================================================
    # SHORT-TERM MEMORY (100 PESAN TERAKHIR)
    # =========================================================================
    
    def add_conversation(self, mas_msg: str, role_msg: str = ""):
        """Tambah percakapan ke memory"""
        self.conversations.append({
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%H:%M:%S"),
            'mas': mas_msg[:500] if mas_msg else "",
            'role': role_msg[:500] if role_msg else ""
        })
        
        logger.debug(f"📝 Conversation added. Total: {len(self.conversations)}")
    
    def get_recent_conversations(self, count: int = 100) -> str:
        """Dapatkan percakapan terakhir (max 100)"""
        if not self.conversations:
            return "Belum ada percakapan."
        
        recent = list(self.conversations)[-count:]
        lines = []
        
        for i, conv in enumerate(recent, 1):
            if conv.get('mas'):
                lines.append(f"[{i}] Mas: {conv['mas']}")
            if conv.get('role'):
                lines.append(f"[{i}] {self.character_name}: {conv['role']}")
        
        return "\n".join(lines)
    
    def get_last_message(self) -> Optional[str]:
        """Dapatkan pesan terakhir"""
        if self.conversations:
            return self.conversations[-1].get('mas')
        return None
    
    # =========================================================================
    # TIMELINE (100 KEJADIAN TERAKHIR)
    # =========================================================================
    
    def add_to_timeline(self, kejadian: str, detail: str = "", context: Dict = None):
        """Tambah kejadian ke timeline"""
        record = {
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%H:%M:%S"),
            'kejadian': kejadian,
            'detail': detail,
            'context': context or {}
        }
        
        self.timeline.append(record)
        logger.debug(f"📅 Timeline added: {kejadian}")
    
    def get_timeline(self, count: int = 50) -> str:
        """Dapatkan timeline untuk prompt (50 terakhir cukup)"""
        if not self.timeline:
            return "Belum ada kejadian."
        
        recent = list(self.timeline)[-count:]
        lines = ["═══════════════════════════════════════════════════════════════"]
        lines.append(f"{count} KEJADIAN TERAKHIR (WAJIB DIPERHATIKAN!):")
        lines.append("═══════════════════════════════════════════════════════════════")
        
        for i, e in enumerate(recent, 1):
            lines.append(f"{i}. [{e['waktu']}] {e['kejadian']}")
            if e['detail']:
                lines.append(f"   └─ {e['detail']}")
        
        return "\n".join(lines)
    
    def get_full_timeline(self) -> str:
        """Dapatkan timeline lengkap (100 kejadian)"""
        if not self.timeline:
            return "Belum ada kejadian."
        
        lines = []
        for i, e in enumerate(self.timeline, 1):
            lines.append(f"{i}. [{e['waktu']}] {e['kejadian']}")
        
        return "\n".join(lines)
    
    # =========================================================================
    # LONG-TERM MEMORY
    # =========================================================================
    
    def save_mas_preference(self, key: str, value: Any):
        """Simpan preferensi Mas"""
        self.long_term['mas_preferences'].append({
            'key': key,
            'value': value,
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Keep only last 50
        if len(self.long_term['mas_preferences']) > 50:
            self.long_term['mas_preferences'] = self.long_term['mas_preferences'][-50:]
        
        logger.info(f"📌 Mas preference saved: {key} = {value}")
    
    def get_mas_preference(self, key: str, default: Any = None) -> Any:
        """Dapatkan preferensi Mas terbaru"""
        for pref in reversed(self.long_term['mas_preferences']):
            if pref['key'] == key:
                return pref['value']
        return default
    
    def get_all_preferences(self) -> str:
        """Dapatkan semua preferensi Mas untuk prompt"""
        if not self.long_term['mas_preferences']:
            return "Belum ada preferensi Mas tercatat."
        
        lines = ["PREFERENSI MAS (YANG SUDAH TERCATAT):"]
        for pref in self.long_term['mas_preferences'][-10:]:
            lines.append(f"- {pref['key']}: {pref['value']}")
        
        return "\n".join(lines)
    
    def add_mas_habit(self, habit: str):
        """Simpan kebiasaan Mas"""
        self.long_term['mas_habits'].append({
            'habit': habit,
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        if len(self.long_term['mas_habits']) > 50:
            self.long_term['mas_habits'] = self.long_term['mas_habits'][-50:]
    
    def add_important_moment(self, moment: str):
        """Simpan momen penting"""
        self.long_term['important_moments'].append({
            'moment': moment,
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        if len(self.long_term['important_moments']) > 30:
            self.long_term['important_moments'] = self.long_term['important_moments'][-30:]
    
    def add_deal(self, service: str, price: int):
        """Simpan deal yang pernah terjadi"""
        self.long_term['deals_made'].append({
            'service': service,
            'price': price,
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        if len(self.long_term['deals_made']) > 20:
            self.long_term['deals_made'] = self.long_term['deals_made'][-20:]
    
    def add_favorite_position(self, position: str):
        """Simpan posisi favorit Mas"""
        self.long_term['favorite_positions'].append({
            'position': position,
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        if len(self.long_term['favorite_positions']) > 30:
            self.long_term['favorite_positions'] = self.long_term['favorite_positions'][-30:]
    
    def get_favorite_positions(self) -> List[str]:
        """Dapatkan daftar posisi favorit Mas"""
        positions = [p['position'] for p in self.long_term['favorite_positions']]
        return list(dict.fromkeys(positions))  # unique
    
    def add_climax_history(self, is_mas: bool, intensity: str = "normal"):
        """Simpan history climax"""
        self.long_term['climax_history'].append({
            'is_mas': is_mas,
            'intensity': intensity,
            'timestamp': time.time(),
            'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        if len(self.long_term['climax_history']) > 50:
            self.long_term['climax_history'] = self.long_term['climax_history'][-50:]
    
    # =========================================================================
    # CURRENT STATE (UNTUK KONSISTENSI)
    # =========================================================================
    
    def update_current_state(self, state: Dict):
        """Update current state"""
        self.current_state.update(state)
        self.current_state['last_action_time'] = time.time()
    
    def get_current_state(self) -> Dict:
        """Dapatkan current state"""
        return self.current_state
    
    def get_context_for_prompt(self) -> str:
        """Dapatkan semua konteks untuk prompt AI"""
        recent_convo = self.get_recent_conversations(50)
        timeline = self.get_timeline(50)
        preferences = self.get_all_preferences()
        
        return f"""
═══════════════════════════════════════════════════════════════
MEMORY & KONTEKS (WAJIB BACA, JANGAN LUPA!):
═══════════════════════════════════════════════════════════════

{timeline}

{recent_convo}

{preferences}

STATE SAAT INI:
- Posisi: {self.current_state.get('position', 'belum diketahui')}
- Pakaian: {self.current_state.get('clothing', 'belum diketahui')}
- Fase: {self.current_state.get('phase', 'belum diketahui')}
- Mas Climax: {self.current_state.get('mas_climax_count', 0)}x
- Role Climax: {self.current_state.get('my_climax_count', 0)}x
- Aksi Terakhir: {self.current_state.get('last_action', '-')}

⚠️ ATURAN KONSISTENSI:
1. JANGAN LUPA posisi terakhir!
2. JANGAN LUPA pakaian yang udah dibuka!
3. JANGAN LUPA fase service yang sedang berjalan!
4. JANGAN tiba-tiba berubah tanpa alasan!
5. Ikuti timeline, jangan maju mundur!
"""
    
    # =========================================================================
    # RESET & CLEANUP
    # =========================================================================
    
    def reset_session(self):
        """Reset session (tapi keep long-term memory)"""
        self.conversations.clear()
        self.timeline.clear()
        self.current_state = {
            'position': None,
            'clothing': None,
            'phase': None,
            'mas_climax_count': 0,
            'my_climax_count': 0,
            'last_action': None,
            'last_action_time': 0
        }
        logger.info(f"🔄 Session reset for {self.character_name}")
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict:
        return {
            'character_name': self.character_name,
            'conversations': list(self.conversations),
            'timeline': list(self.timeline),
            'long_term': self.long_term,
            'current_state': self.current_state
        }
    
    def from_dict(self, data: Dict):
        self.character_name = data.get('character_name', self.character_name)
        self.conversations = deque(data.get('conversations', []), maxlen=100)
        self.timeline = deque(data.get('timeline', []), maxlen=100)
        self.long_term = data.get('long_term', self.long_term)
        self.current_state = data.get('current_state', self.current_state)
