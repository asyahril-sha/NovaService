# service/pelacur_core.py
"""
Pelacur Core - Base class untuk semua pelacur flow
Berisi: Class init, AI client, timer methods, import memory & prompts
"""

import asyncio
import time
import logging
from typing import Dict, Optional, List, Any

from core import ServicePhase
from core.prompt_builder import get_prompt_builder
from core.emotional_engine import EmotionalEngine
from config import get_settings

# Import memory dan prompts
from service.pelacur_memory import PelacurMemory
from service.pelacur_prompts import PelacurPromptBuilder

logger = logging.getLogger(__name__)


class PelacurCore:
    """
    Core class untuk Pelacur Flow
    Semua class lain akan inherit dari class ini
    """
    
    # ========== KONFIGURASI DURASI ==========
    TOTAL_BOOKING_HOURS = 6                    # 6 jam total
    TOTAL_BOOKING_SECONDS = TOTAL_BOOKING_HOURS * 3600  # 21600 detik
    
    BJ_DURATION = 1800                         # 30 menit
    KISSING_DURATION = 1800                    # 30 menit
    SCENE_INTERVAL = 30                        # 30 detik per scene
    
    BJ_SCENES = 60                             # 30 menit / 30 detik
    KISSING_SCENES = 60                        # 30 menit / 30 detik
    
    # ========== WARNING SCHEDULE (NATURAL) ==========
    WARNING_SCHEDULE = {
        3600: "Mas... udah 1 jam kita bareng... masih kuat?",
        7200: "Wah, udah 2 jam Mas... aku masih pengen terus sama Mas...",
        10800: "3 jam Mas... luar biasa... belum pernah kayak gini...",
        14400: "4 jam ya Mas... aku masih nggak mau berhenti...",
        18000: "Mas... tinggal 1 jam lagi... aku bakal kangen...",
        19800: "30 menit lagi ya Mas... masih mau lanjut?",
        21000: "10 menit lagi Mas... aku pengen banget sama Mas...",
        21540: "1 menit lagi Mas... aku sayang Mas...",
    }
    
    def __init__(self, character):
        """Inisialisasi Core dengan memory dan prompt builder"""
        self.character = character
        self._ai_client = None
        
        # ========== MEMORY SYSTEM ==========
        self.memory = PelacurMemory(character.name)
        
        # ========== PROMPT BUILDER ==========
        self.prompt_builder = PelacurPromptBuilder(character)
        
        # ========== BOOKING STATE ==========
        self.is_active = False
        self.booking_start_time = 0
        self.booking_end_time = 0
        self.current_cycle = 1
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
        
        # ========== CLIMAX TRACKING (NATURAL) ==========
        self.mas_climax_count = 0
        self.role_climax_count = 0
        self.last_climax_time = 0
        
        # ========== WAITING FOR RESPONSE ==========
        self.waiting_for_response = False
        self.waiting_for_type = None
        self.waiting_start_time = 0
        self.WAITING_TIMEOUT = 60
        
        # ========== AFTERCARE ==========
        self.aftercare_active = False
        
        # ========== CONVERSATION HISTORY ==========
        self.conversation_history: List[str] = []
        
        # ========== WARNING TRACKING ==========
        self._sent_warnings: List[int] = []
        
        # ========== AUTO SEND TASK ==========
        self.auto_send_task = None
        self.auto_send_running = False
        
        logger.info(f"🔥 PelacurCore initialized for {character.name}")
    
    # =========================================================================
    # AI CLIENT & GENERATE SCENE
    # =========================================================================
    
    async def _get_ai_client(self):
        """Dapatkan AI client (DeepSeek)"""
        if self._ai_client is None:
            try:
                import openai
                settings = get_settings()
                self._ai_client = openai.OpenAI(
                    api_key=settings.deepseek_api_key,
                    base_url="https://api.deepseek.com/v1"
                )
            except Exception as e:
                logger.error(f"AI init failed: {e}", exc_info=True)
                raise
        return self._ai_client
    
    async def _generate_scene(self, prompt: str, retry_count: int = 3) -> str:
        """Generate scene menggunakan AI dengan retry mechanism"""
        for attempt in range(retry_count):
            try:
                client = await self._get_ai_client()
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.9,
                    max_tokens=500,
                    timeout=25
                )
                
                scene = response.choices[0].message.content.strip()
                
                if not scene.startswith("*"):
                    scene = f"*{scene}*"
                
                return scene
                
            except asyncio.TimeoutError:
                logger.warning(f"AI timeout attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except Exception as e:
                logger.error(f"AI error attempt {attempt + 1}: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(1)
                    continue
        
        # Fallback
        return f"*{self.character.name} terus melayani Mas dengan penuh cinta.*"
    
    # =========================================================================
    # TIMER METHODS
    # =========================================================================
    
    def _get_phase_elapsed(self) -> int:
        """Dapatkan waktu yang sudah berlalu di fase saat ini (detik)"""
        if self.phase_start_time == 0:
            return 0
        return int(time.time() - self.phase_start_time)
    
    def _get_booking_elapsed(self) -> int:
        """Dapatkan waktu yang sudah berlalu sejak booking dimulai (detik)"""
        if self.booking_start_time == 0:
            return 0
        return int(time.time() - self.booking_start_time)
    
    def _get_remaining_time(self) -> int:
        """Dapatkan sisa waktu booking (detik)"""
        elapsed = self._get_booking_elapsed()
        return max(0, self.TOTAL_BOOKING_SECONDS - elapsed)
    
    def _should_send_next_auto_scene(self) -> bool:
        """
        Cek apakah sudah waktunya kirim scene auto berikutnya
        Scene ke-1: detik 0-29, scene ke-2: detik 30-59, dst
        """
        elapsed = self._get_phase_elapsed()
        expected_scene = (elapsed // self.SCENE_INTERVAL) + 1
        
        if expected_scene > self.scene_count:
            self.scene_count = expected_scene
            logger.info(f"📤 Auto scene #{expected_scene} (elapsed={elapsed}s)")
            return True
        return False
    
    def _is_auto_phase_complete(self) -> bool:
        """Cek apakah auto phase sudah selesai"""
        elapsed = self._get_phase_elapsed()
        
        if self.current_phase_name == "bj":
            return elapsed >= self.BJ_DURATION
        elif self.current_phase_name == "kissing":
            return elapsed >= self.KISSING_DURATION
        
        return False
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _update_emotional_state(self):
        """Update emotional state dan sinkronisasi dengan memory"""
        self.character.emotional.update()
        
        # Sinkronisasi ke memory
        arousal = self.character.emotional.arousal
        stamina = self.character.emotional.stamina
        
        # Update body state berdasarkan arousal
        if arousal >= 85:
            self.memory.update_body_state(
                napas='putus-putus',
                gemetar=True,
                detak_jantung='kencang'
            )
        elif arousal >= 70:
            self.memory.update_body_state(
                napas='tersengal',
                gemetar=True,
                detak_jantung='cepat'
            )
        elif arousal >= 50:
            self.memory.update_body_state(
                napas='berat',
                detak_jantung='cepat'
            )
        
        # Update suhu berdasarkan arousal
        if arousal >= 70:
            self.memory.update_body_state(suhu='panas')
        elif arousal >= 40:
            self.memory.update_body_state(suhu='hangat')
        
        # Update perasaan
        if arousal >= 85:
            self.memory.update_feeling('pengen climax', int(arousal))
        elif arousal >= 70:
            self.memory.update_feeling('sange', int(arousal))
        elif arousal >= 50:
            self.memory.update_feeling('enak', int(arousal))
        
        # Update stamina ke memory
        if stamina < 30:
            self.memory.update_body_state(keringat='banyak', otot='kaku')
        elif stamina < 60:
            self.memory.update_body_state(keringat='banyak')
    
    def _get_time_string(self, seconds: int) -> str:
        """Dapatkan string waktu yang natural"""
        if seconds < 0:
            return "0 menit"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours} jam {minutes} menit"
        else:
            return f"{minutes} menit"
