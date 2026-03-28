# memory/persistent.py
"""
NovaService Persistent Memory
Simpan semua state ke database SQLite
"""

import time
import json
import aiosqlite
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class NovaPersistentMemory:
    """
    Persistent memory untuk NovaService
    Menyimpan semua state ke database SQLite
    """
    
    def __init__(self, db_path: Path = Path("data/novaservice.db")):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
    
    async def init(self):
        """Inisialisasi database dan tabel"""
        self._conn = await aiosqlite.connect(str(self.db_path))
        self._conn.row_factory = aiosqlite.Row
        
        # ========== TABEL UTAMA ==========
        await self._conn.execute('''
            CREATE TABLE IF NOT EXISTS nova_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        ''')
        
        # ========== TABEL CHARACTER STATE ==========
        await self._conn.execute('''
            CREATE TABLE IF NOT EXISTS character_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                character_name TEXT NOT NULL,
                character_data TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        ''')
        
        # ========== TABEL CONVERSATIONS ==========
        await self._conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        
        # ========== TABEL SESSIONS ==========
        await self._conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                character_name TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                mas_climax INTEGER DEFAULT 0,
                role_climax INTEGER DEFAULT 0,
                duration_minutes INTEGER DEFAULT 0
            )
        ''')
        
        # ========== INDEXES ==========
        await self._conn.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)')
        await self._conn.execute('CREATE INDEX IF NOT EXISTS idx_conversations_time ON conversations(timestamp)')
        await self._conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_session ON sessions(session_id)')
        
        await self._conn.commit()
        
        # Inisialisasi state awal
        await self._init_state()
        
        logger.info(f"💾 NovaService Persistent Memory initialized at {self.db_path}")
    
    async def _init_state(self):
        """Inisialisasi state awal"""
        cursor = await self._conn.execute("SELECT COUNT(*) FROM character_state")
        count = await cursor.fetchone()
        
        if count[0] == 0:
            await self._conn.execute(
                "INSERT INTO character_state (id, character_name, character_data, updated_at) VALUES (1, 'none', '{}', ?)",
                (time.time(),)
            )
            await self._conn.commit()
    
    # =========================================================================
    # STATE METHODS
    # =========================================================================
    
    async def get_state(self, key: str) -> Optional[str]:
        """Ambil state dari database"""
        cursor = await self._conn.execute("SELECT value FROM nova_state WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None
    
    async def set_state(self, key: str, value: str):
        """Simpan state ke database"""
        await self._conn.execute(
            "INSERT OR REPLACE INTO nova_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, time.time())
        )
        await self._conn.commit()
    
    async def get_all_states(self) -> Dict[str, str]:
        """Ambil semua state"""
        cursor = await self._conn.execute("SELECT key, value FROM nova_state")
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    
    # =========================================================================
    # CHARACTER STATE METHODS
    # =========================================================================
    
    async def save_character_state(self, character):
        """Simpan state karakter"""
        try:
            data = character.to_dict()
            await self._conn.execute(
                "INSERT OR REPLACE INTO character_state (id, character_name, character_data, updated_at) VALUES (1, ?, ?, ?)",
                (character.name, json.dumps(data, default=str), time.time())
            )
            await self._conn.commit()
        except Exception as e:
            logger.error(f"Error saving character state: {e}")
    
    async def load_character_state(self) -> Optional[Dict]:
        """Load state karakter"""
        try:
            cursor = await self._conn.execute(
                "SELECT character_name, character_data FROM character_state WHERE id = 1"
            )
            row = await cursor.fetchone()
            if row:
                return {
                    'character_name': row[0],
                    'character_data': json.loads(row[1])
                }
            return None
        except Exception as e:
            logger.error(f"Error loading character state: {e}")
            return None
    
    # =========================================================================
    # CONVERSATION METHODS
    # =========================================================================
    
    async def save_conversation(self, user_id: int, role: str, message: str):
        """Simpan percakapan"""
        await self._conn.execute(
            "INSERT INTO conversations (user_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, role, message[:2000], time.time())
        )
        await self._conn.commit()
    
    async def get_recent_conversations(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Ambil percakapan terakhir (max 100)"""
        cursor = await self._conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows][::-1]
    
    # =========================================================================
    # SESSION METHODS
    # =========================================================================
    
    async def start_session(self, session_id: str, character_name: str) -> str:
        """Mulai sesi baru"""
        await self._conn.execute(
            "INSERT INTO sessions (session_id, character_name, start_time) VALUES (?, ?, ?)",
            (session_id, character_name, time.time())
        )
        await self._conn.commit()
        return session_id
    
    async def end_session(self, session_id: str, mas_climax: int, role_climax: int, duration_minutes: int):
        """Akhiri sesi"""
        await self._conn.execute(
            "UPDATE sessions SET end_time = ?, mas_climax = ?, role_climax = ?, duration_minutes = ? WHERE session_id = ?",
            (time.time(), mas_climax, role_climax, duration_minutes, session_id)
        )
        await self._conn.commit()
    
    async def get_session_history(self, limit: int = 10) -> List[Dict]:
        """Ambil history sesi"""
        cursor = await self._conn.execute(
            "SELECT * FROM sessions ORDER BY start_time DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    async def get_stats(self) -> Dict:
        """Dapatkan statistik database"""
        stats = {}
        tables = ['nova_state', 'character_state', 'conversations', 'sessions']
        for table in tables:
            cursor = await self._conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = await cursor.fetchone()
            stats[f"{table}_count"] = count[0]
        
        if self.db_path.exists():
            stats['db_size_mb'] = round(self.db_path.stat().st_size / (1024 * 1024), 2)
        
        return stats
    
    async def vacuum(self):
        """Optimasi database"""
        await self._conn.execute("VACUUM")
    
    async def close(self):
        """Tutup koneksi database"""
        if self._conn:
            await self._conn.close()


# =============================================================================
# SINGLETON
# =============================================================================

_nova_persistent: Optional[NovaPersistentMemory] = None


async def get_nova_persistent() -> NovaPersistentMemory:
    global _nova_persistent
    if _nova_persistent is None:
        _nova_persistent = NovaPersistentMemory()
        await _nova_persistent.init()
    return _nova_persistent


nova_persistent = None
