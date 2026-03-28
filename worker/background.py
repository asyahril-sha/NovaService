# worker/background.py
"""
NovaService Background Worker
Berjalan di background untuk:
- Auto save state ke database
- Cleanup session
- Auto backup database
"""

import asyncio
import time
import logging
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class NovaWorker:
    """
    Background worker untuk NovaService
    Menjalankan task-task periodic
    """
    
    def __init__(self):
        self.is_running = False
        self.tasks = []
        
        # Interval dalam detik
        self.save_interval = 60       # 1 menit
        self.cleanup_interval = 3600  # 1 jam
        self.backup_interval = 21600  # 6 jam
        
        # Last run times
        self.last_save_run = 0
        self.last_cleanup_run = 0
        self.last_backup_run = 0
        
        # Application reference
        self.application = None
        self.user_id = None
        
        # Backup directory
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🔄 NovaWorker initialized")
    
    async def start(self, application=None, user_id: int = None):
        """Start background worker"""
        self.is_running = True
        self.application = application
        self.user_id = user_id
        
        # Start all loops
        self.tasks = [
            asyncio.create_task(self._save_loop()),
            asyncio.create_task(self._cleanup_loop()),
            asyncio.create_task(self._backup_loop()),
        ]
        
        logger.info("🔄 All background loops started")
    
    async def stop(self):
        """Stop all background tasks"""
        self.is_running = False
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("🔄 All background loops stopped")
    
    # =========================================================================
    # SAVE STATE LOOP
    # =========================================================================
    
    async def _save_loop(self):
        """Save state ke database setiap 1 menit"""
        while self.is_running:
            now = time.time()
            elapsed = now - self.last_save_run
            
            if elapsed >= self.save_interval:
                await self._save_all_states()
                self.last_save_run = now
            
            await asyncio.sleep(30)
    
    async def _save_all_states(self):
        """Simpan semua state ke database"""
        try:
            from memory.persistent import get_nova_persistent
            from roles.manager import get_role_manager
            
            persistent = await get_nova_persistent()
            role_manager = get_role_manager()
            
            # Save role state
            if self.user_id:
                role = role_manager.get_role(self.user_id)
                if role:
                    await persistent.save_character_state(role)
            
            logger.debug("💾 All states saved")
            
        except Exception as e:
            logger.error(f"Save state error: {e}")
    
    # =========================================================================
    # CLEANUP LOOP
    # =========================================================================
    
    async def _cleanup_loop(self):
        """Cleanup session dan expired data setiap 1 jam"""
        while self.is_running:
            now = time.time()
            elapsed = now - self.last_cleanup_run
            
            if elapsed >= self.cleanup_interval:
                await self._cleanup()
                self.last_cleanup_run = now
            
            await asyncio.sleep(600)
    
    async def _cleanup(self):
        """Bersihkan data yang sudah expired"""
        try:
            from memory.persistent import get_nova_persistent
            
            persistent = await get_nova_persistent()
            
            # Cleanup old conversations (lebih dari 7 hari)
            cutoff = time.time() - (7 * 24 * 3600)
            
            # Log cleanup
            logger.info("🧹 Cleanup old data...")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    # =========================================================================
    # AUTO BACKUP LOOP
    # =========================================================================
    
    async def _backup_loop(self):
        """Auto backup database setiap 6 jam"""
        while self.is_running:
            now = time.time()
            elapsed = now - self.last_backup_run
            
            if elapsed >= self.backup_interval:
                await self._auto_backup()
                self.last_backup_run = now
            
            await asyncio.sleep(3600)
    
    async def _auto_backup(self):
        """Auto backup database"""
        try:
            from memory.persistent import get_nova_persistent
            
            persistent = await get_nova_persistent()
            db_path = persistent.db_path
            
            if db_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.backup_dir / f"novaservice_auto_{timestamp}.db"
                shutil.copy(db_path, backup_path)
                
                # Hapus backup auto yang lebih dari 7 hari
                for b in self.backup_dir.glob("novaservice_auto_*.db"):
                    age = time.time() - b.stat().st_mtime
                    if age > 7 * 24 * 3600:
                        b.unlink()
                        logger.info(f"🗑️ Deleted old backup: {b.name}")
                
                logger.info(f"💾 Auto backup saved: {backup_path.name}")
                
        except Exception as e:
            logger.error(f"Auto backup error: {e}")
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    async def manual_backup(self) -> str:
        """Manual backup database"""
        try:
            from memory.persistent import get_nova_persistent
            
            persistent = await get_nova_persistent()
            db_path = persistent.db_path
            
            if not db_path.exists():
                return "Database tidak ditemukan."
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"novaservice_manual_{timestamp}.db"
            shutil.copy(db_path, backup_path)
            
            return f"✅ Backup saved: {backup_path.name}"
            
        except Exception as e:
            return f"❌ Backup error: {e}"
    
    async def get_backup_list(self) -> List[str]:
        """Dapatkan daftar backup"""
        backups = []
        for b in self.backup_dir.glob("novaservice_*.db"):
            backups.append({
                'name': b.name,
                'size_kb': round(b.stat().st_size / 1024, 2),
                'modified': datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        return sorted(backups, key=lambda x: x['modified'], reverse=True)


# =============================================================================
# SINGLETON
# =============================================================================

_nova_worker: Optional['NovaWorker'] = None


def get_nova_worker() -> NovaWorker:
    global _nova_worker
    if _nova_worker is None:
        _nova_worker = NovaWorker()
    return _nova_worker


nova_worker = get_nova_worker()
