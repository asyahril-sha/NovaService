# service/therapist_flow_FIXED.py
"""
Therapist Flow NovaService - FIXED VERSION
Perbaikan: timing logic, timeout, flow perpindahan area, auto-send task
"""

import asyncio
import time
import logging
import random
from typing import Dict, Optional, List, Any
from datetime import datetime

from core import ServicePhase, StateTracker
from core.prompt_builder import get_prompt_builder
from core.emotional_engine import EmotionalEngine
from config import get_settings

logger = logging.getLogger(__name__)


class TherapistFlow:
    """
    Alur service therapist dengan AI generate setiap scene - FIXED VERSION
    
    PERBAIKAN:
    1. ✅ Logika timing _should_send_next_scene() diperbaiki
    2. ✅ Implementasi timeout waiting (60 detik)
    3. ✅ Flow perpindahan area tidak macet
    4. ✅ Fallback scene hanya ketika tidak waiting
    5. ✅ Auto-send background task dengan asyncio
    6. ✅ Intimate phase terintegrasi ke prompt
    7. ✅ Emotional state terintegrasi ke prompt
    """
    
    # Durasi dalam detik
    AREA_DURATION = 600          # 10 menit per area
    SCENE_INTERVAL = 30          # 30 detik per scene
    CONFIRM_INTERVAL = 180       # 3 menit konfirmasi Mas
    WAITING_TIMEOUT = 60         # 60 detik timeout menunggu jawaban
    
    # Scene count per aktivitas
    HJ_SCENES = 60               # 30 menit
    BJ_SCENES = 60               # 30 menit
    
    # Harga (dari config)
    PRICE_BJ = 500000
    PRICE_SEX = 1000000
    PRICE_BJ_DEAL = 200000
    PRICE_SEX_DEAL = 700000
    
    def __init__(self, character):
        """Inisialisasi TherapistFlow"""
        self.character = character
        self.prompt_builder = get_prompt_builder()
        self._ai_client = None
        
        # ========== STATE TRACKING ==========
        self.is_active = False
        self.current_phase = ServicePhase.WAITING
        self.phase_start_time = 0
        
        # ========== BACK MASSAGE AREAS ==========
        self.back_areas = ["punggung", "pinggul", "paha_betis"]
        self.back_area_index = 0
        self.back_area_start_time = 0
        self.back_scene_count = 0
        self.back_scenes_per_area = 20
        self.back_confirm_count = 0
        
        # ========== FRONT MASSAGE AREAS ==========
        self.front_areas = ["dada_lengan", "perut_paha", "gesekan"]
        self.front_area_index = 0
        self.front_area_start_time = 0
        self.front_scene_count = 0
        self.front_scenes_per_area = 20
        self.front_confirm_count = 0
        
        # ========== SERVICE STATE ==========
        self.current_service = None  # "hj", "bj", "sex"
        
        # ========== HJ STATE ==========
        self.hj_scene_count = 0
        self.hj_total_scenes = self.HJ_SCENES
        self.hj_speed = "medium"
        
        # ========== BJ STATE ==========
        self.bj_scene_count = 0
        self.bj_total_scenes = self.BJ_SCENES
        self.bj_depth = "medium"
        
        # ========== SEX STATE (MANUAL MODE) ==========
        self.sex_manual_mode = False
        self.sex_climax_goal = 2       # Mas climax 2x
        self.sex_climax_count = 0
        self.sex_conversation_history = []  # Untuk konsistensi manual mode
        
        # ========== NEGOSIASI ==========
        self.negotiation_active = False
        self.negotiation_service = None
        self.negotiation_price = 0
        self.negotiation_step = 0
        self.negotiation_max_step = 3
        self.deal_confirmed = False
        
        # ========== CLIMAX TRACKING ==========
        self.mas_climax_this_session = 0
        self.role_climax_this_session = 0
        self.waiting_climax_confirmation = False
        self.climax_warning_time = 0
        
        # ========== WAITING FOR RESPONSE ==========
        self.waiting_for_response = False
        self.waiting_for_type = None  # "pressure", "next_area", "deal", "position", "sex_response", "hj_offer", "extra_offer"
        self.waiting_start_time = 0
        
        # ========== AUTO SEND TASK ==========
        self.auto_send_task = None
        self.last_scene_sent_time = 0
        self.auto_send_running = False
        
        # ========== PAUSE & RESUME ==========
        self.is_paused = False
        self.pause_start_time = 0
        
        # ========== INTIMATE PHASE ==========
        self.intimate_phase = "stranger"
        self.intimate_level = 1
        self.intimacy_build_up = 0
        
        logger.info(f"💆 TherapistFlow FIXED initialized for {character.name}")
    
    # =========================================================================
    # AI CLIENT
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
                    temperature=0.85,
                    max_tokens=800,
                    timeout=25
                )
                
                scene = response.choices[0].message.content.strip()
                
                if not scene.startswith("*"):
                    scene = f"*{scene}*"
                
                return scene
                
            except asyncio.TimeoutError:
                logger.warning(f"AI timeout attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
                    continue
            except Exception as e:
                logger.error(f"AI error attempt {attempt + 1}: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(1)
                    continue
        
        # Fallback dengan konteks intimate phase
        return self._get_fallback_scene()
    
    def _get_fallback_scene(self) -> str:
        """Fallback scene dengan konteks intimate phase"""
        phase = self.intimate_phase
        name = self.character.name
        
        fallbacks = {
            "stranger": f"*{name} terus memijat dengan fokus, menjaga jarak profesional.*",
            "friend": f"*{name} tersenyum kecil, tangannya tetap bekerja lembut.*",
            "close": f"*{name} mendesah pelan, terus melayani dengan penuh perhatian.*",
            "romantic": f"*{name} menatap Mas dengan mata sayu, napasnya mulai berat.*",
            "intimate": f"*{name} menggigit bibir, tubuhnya semakin hangat di atas Mas.*"
        }
        return fallbacks.get(phase, f"*{name} terus melayani dengan lembut.*")
    
    # =========================================================================
    # TIMER METHODS (DIPERBAIKI)
    # =========================================================================
    
    def _get_area_elapsed(self) -> int:
        """Dapatkan waktu yang sudah berlalu untuk area saat ini (detik)"""
        if self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            if self.back_area_start_time == 0:
                return 0
            return int(time.time() - self.back_area_start_time)
        elif self.current_phase in [ServicePhase.FRONT_DADA_LENGAN, ServicePhase.FRONT_PERUT_PAHA, ServicePhase.FRONT_GESEKAN]:
            if self.front_area_start_time == 0:
                return 0
            return int(time.time() - self.front_area_start_time)
        elif self.current_phase == ServicePhase.HANDJOB:
            if self.phase_start_time == 0:
                return 0
            return int(time.time() - self.phase_start_time)
        elif self.current_phase == ServicePhase.BJ:
            if self.phase_start_time == 0:
                return 0
            return int(time.time() - self.phase_start_time)
        return 0
    
    def _should_send_next_scene(self) -> bool:
        """
        Cek apakah sudah waktunya kirim scene berikutnya
        PERBAIKAN: menggunakan +1 agar scene ke-1 di detik 0-29
        """
        elapsed = self._get_area_elapsed()
        interval = self.SCENE_INTERVAL
        
        # Scene ke-1: detik 0-29, scene ke-2: detik 30-59, dst
        expected_scene = (elapsed // interval) + 1
        
        if self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            if expected_scene > self.back_scene_count:
                self.back_scene_count = expected_scene
                logger.info(f"📤 Should send back scene #{expected_scene} (elapsed={elapsed}s)")
                return True
        elif self.current_phase in [ServicePhase.FRONT_DADA_LENGAN, ServicePhase.FRONT_PERUT_PAHA, ServicePhase.FRONT_GESEKAN]:
            if expected_scene > self.front_scene_count:
                self.front_scene_count = expected_scene
                logger.info(f"📤 Should send front scene #{expected_scene} (elapsed={elapsed}s)")
                return True
        elif self.current_phase == ServicePhase.HANDJOB:
            if expected_scene > self.hj_scene_count:
                self.hj_scene_count = expected_scene
                logger.info(f"📤 Should send HJ scene #{expected_scene} (elapsed={elapsed}s)")
                return True
        elif self.current_phase == ServicePhase.BJ:
            if expected_scene > self.bj_scene_count:
                self.bj_scene_count = expected_scene
                logger.info(f"📤 Should send BJ scene #{expected_scene} (elapsed={elapsed}s)")
                return True
        
        return False
    
    def _should_ask_confirmation(self) -> bool:
        """
        Cek apakah sudah waktunya minta konfirmasi Mas
        PERBAIKAN: menggunakan +1 agar konfirmasi pertama di menit 3
        """
        elapsed = self._get_area_elapsed()
        
        # Jangan minta konfirmasi jika sudah mendekati area complete (9.5 menit)
        if elapsed >= 570:
            return False
        
        # Konfirmasi setiap 180 detik (3 menit)
        expected_confirm = (elapsed // self.CONFIRM_INTERVAL) + 1
        
        if self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            if expected_confirm > self.back_confirm_count and expected_confirm <= 3:  # Maks 3x konfirmasi per area
                self.back_confirm_count = expected_confirm
                logger.info(f"📢 Should ask confirmation #{expected_confirm} (elapsed={elapsed}s)")
                return True
        elif self.current_phase in [ServicePhase.FRONT_DADA_LENGAN, ServicePhase.FRONT_PERUT_PAHA, ServicePhase.FRONT_GESEKAN]:
            if expected_confirm > self.front_confirm_count and expected_confirm <= 3:
                self.front_confirm_count = expected_confirm
                logger.info(f"📢 Should ask confirmation #{expected_confirm} (elapsed={elapsed}s)")
                return True
        
        return False
    
    def _is_area_complete(self) -> bool:
        """Cek apakah area sudah selesai (10 menit)"""
        elapsed = self._get_area_elapsed()
        is_complete = elapsed >= self.AREA_DURATION
        if is_complete:
            logger.info(f"✅ AREA COMPLETE! elapsed={elapsed}s, AREA_DURATION={self.AREA_DURATION}s")
        return is_complete
    
    # =========================================================================
    # TIMEOUT HANDLING (BARU)
    # =========================================================================
    
    async def _check_waiting_timeout(self) -> Optional[str]:
        """Cek apakah waiting timeout dan auto-lanjutkan"""
        if not self.waiting_for_response:
            return None
        
        elapsed_waiting = time.time() - self.waiting_start_time
        if elapsed_waiting > self.WAITING_TIMEOUT:
            logger.info(f"⏰ Waiting timeout after {elapsed_waiting:.0f}s for {self.waiting_for_type}")
            self.waiting_for_response = False
            
            # Auto-lanjutkan dengan default
            if self.waiting_for_type == "pressure":
                return await self._auto_continue_pressure()
            elif self.waiting_for_type == "next_area":
                return await self._auto_continue_next_area()
            elif self.waiting_for_type == "hj_offer":
                # Default: lanjut ke end session
                return self._build_end_session()
            elif self.waiting_for_type == "extra_offer":
                # Default: end session
                return self._build_end_session()
            elif self.waiting_for_type == "negotiation":
                # Default: batal nego, end session
                self.negotiation_active = False
                return self._build_end_session()
            
            # Reset waiting
            self.waiting_for_type = None
            return None
        
        return None
    
    async def _auto_continue_pressure(self) -> str:
        """Auto-lanjutkan dengan tekanan medium jika Mas tidak jawab"""
        logger.info("🤖 Auto-continue with medium pressure")
        self.character.tracker.current_pressure = "medium"
        
        if self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            return await self._generate_back_scene(
                area=self.back_areas[self.back_area_index],
                pressure="medium",
                scene_num=self.back_scene_count + 1,
                elapsed_minutes=self._get_area_elapsed() // 60
            )
        else:
            return await self._generate_front_scene(
                area=self.front_areas[self.front_area_index],
                pressure="medium",
                scene_num=self.front_scene_count + 1,
                elapsed_minutes=self._get_area_elapsed() // 60
            )
    
    async def _auto_continue_next_area(self) -> str:
        """Auto-lanjutkan ke area berikutnya jika Mas tidak jawab"""
        logger.info("🤖 Auto-continue to next area")
        
        if self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            return await self._next_back_area()
        else:
            return await self._next_front_area()
    
    # =========================================================================
    # AUTO SEND TASK (BARU)
    # =========================================================================
    
    async def _start_auto_send_task(self):
        """Mulai background task untuk auto-send scene"""
        if self.auto_send_running:
            return
        
        self.auto_send_running = True
        self.auto_send_task = asyncio.create_task(self._auto_send_loop())
        logger.info("🚀 Auto-send task started")
    
    async def _stop_auto_send_task(self):
        """Hentikan background task"""
        self.auto_send_running = False
        if self.auto_send_task and not self.auto_send_task.done():
            self.auto_send_task.cancel()
            try:
                await self.auto_send_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Auto-send task stopped")
    
    async def _auto_send_loop(self):
        """Loop background untuk kirim scene sesuai timing"""
        while self.auto_send_running and self.is_active and not self.is_paused:
            try:
                # Cek jika sedang menunggu respons Mas, jangan kirim scene otomatis
                if self.waiting_for_response:
                    await asyncio.sleep(1)
                    continue
                
                # Cek timeout waiting
                timeout_response = await self._check_waiting_timeout()
                if timeout_response:
                    # Kirim timeout response melalui callback
                    if hasattr(self.character, 'send_message'):
                        await self.character.send_message(timeout_response)
                    await asyncio.sleep(1)
                    continue
                
                # Cek apakah perlu kirim scene
                if self._should_send_next_scene():
                    scene = await self._get_next_scene()
                    if scene:
                        logger.info(f"📤 Auto-send scene: {scene[:100]}...")
                        if hasattr(self.character, 'send_message'):
                            await self.character.send_message(scene)
                        self.last_scene_sent_time = time.time()
                
                await asyncio.sleep(1)  # Check setiap detik
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-send loop error: {e}")
                await asyncio.sleep(5)
    
    async def _get_next_scene(self) -> Optional[str]:
        """Generate scene berikutnya berdasarkan current phase"""
        elapsed = self._get_area_elapsed()
        elapsed_minutes = elapsed // 60
        
        if self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            return await self._generate_back_scene(
                area=self.back_areas[self.back_area_index],
                pressure=self._get_current_pressure(),
                scene_num=self.back_scene_count,
                elapsed_minutes=elapsed_minutes
            )
        
        elif self.current_phase in [ServicePhase.FRONT_DADA_LENGAN, ServicePhase.FRONT_PERUT_PAHA, ServicePhase.FRONT_GESEKAN]:
            return await self._generate_front_scene(
                area=self.front_areas[self.front_area_index],
                pressure=self._get_current_pressure(),
                scene_num=self.front_scene_count,
                elapsed_minutes=elapsed_minutes
            )
        
        elif self.current_phase == ServicePhase.HANDJOB:
            return await self._generate_hj_scene(
                scene_num=self.hj_scene_count,
                speed=self._get_current_speed(),
                mas_action=None
            )
        
        elif self.current_phase == ServicePhase.BJ:
            depth = "deep" if self.bj_scene_count > self.bj_total_scenes * 0.7 else "medium"
            return await self._generate_bj_scene(
                scene_num=self.bj_scene_count,
                depth=depth,
                mas_action=None
            )
        
        return None
    
    # =========================================================================
    # PRESSURE & SPEED METHODS
    # =========================================================================
    
    def _get_current_pressure(self) -> str:
        pressure = self.character.tracker.get_last_pressure()
        if pressure == "keras":
            return "keras"
        elif pressure == "lembut":
            return "lembut"
        return "medium"
    
    def _get_current_speed(self) -> str:
        speed = self.character.tracker.get_last_speed()
        if speed == "cepat":
            return "fast"
        elif speed == "pelan":
            return "slow"
        return "medium"
    
    # =========================================================================
    # INTIMATE PHASE METHODS
    # =========================================================================
    
    def _update_intimate_phase(self):
        """Update fase intimate berdasarkan level"""
        if hasattr(self.character, 'relationship'):
            self.intimate_level = self.character.relationship.level
        
        if self.intimate_level <= 3:
            self.intimate_phase = "stranger"
        elif self.intimate_level <= 6:
            self.intimate_phase = "friend"
        elif self.intimate_level <= 8:
            self.intimate_phase = "close"
        elif self.intimate_level <= 10:
            self.intimate_phase = "romantic"
        else:
            self.intimate_phase = "intimate"
        
        if self.intimacy_build_up < 100:
            self.intimacy_build_up = min(100, self.intimacy_build_up + 1)
        
        self.character.tracker.intimate_phase = self.intimate_phase
        self.character.tracker.intimate_level = self.intimate_level
        self.character.tracker.intimacy_build_up = self.intimacy_build_up

    # =========================================================================
    # SCENE GENERATION METHODS (DENGAN INTIMATE PHASE)
    # =========================================================================
    
    async def _generate_back_scene(self, area: str, pressure: str, scene_num: int, elapsed_minutes: int) -> str:
        total_scenes = self.back_scenes_per_area
        self._update_intimate_phase()
        
        prompt = self.prompt_builder.build_back_massage_prompt(
            self.character, area, pressure, scene_num, elapsed_minutes, total_scenes
        )
        
        # Tambahkan intimate phase ke prompt jika belum ada
        if hasattr(self.prompt_builder, '_get_intimate_context'):
            intimate_context = self.prompt_builder._get_intimate_context(
                self.intimate_phase, self.intimate_level
            )
            prompt = prompt + f"\n\nFASE KEINTIMAN: {intimate_context}"
        
        return await self._generate_scene(prompt)
    
    async def _generate_front_scene(self, area: str, pressure: str, scene_num: int, elapsed_minutes: int) -> str:
        total_scenes = self.front_scenes_per_area
        prompt = self.prompt_builder.build_front_massage_prompt(
            self.character, area, pressure, scene_num, elapsed_minutes, total_scenes
        )
        
        if hasattr(self.prompt_builder, '_get_intimate_context'):
            intimate_context = self.prompt_builder._get_intimate_context(
                self.intimate_phase, self.intimate_level
            )
            prompt = prompt + f"\n\nFASE KEINTIMAN: {intimate_context}"
        
        return await self._generate_scene(prompt)
    
    async def _generate_hj_scene(self, scene_num: int, speed: str, mas_action: str = None) -> str:
        prompt = self.prompt_builder.build_hj_prompt(
            self.character, scene_num, self.hj_total_scenes, speed, mas_action
        )
        return await self._generate_scene(prompt)
    
    async def _generate_bj_scene(self, scene_num: int, depth: str, mas_action: str = None) -> str:
        prompt = self.prompt_builder.build_bj_prompt(
            self.character, scene_num, self.bj_total_scenes, depth, mas_action
        )
        return await self._generate_scene(prompt)
    
    # =========================================================================
    # CONFIRMATION METHODS
    # =========================================================================
    
    def _build_confirmation_pressure(self) -> str:
        return f"""*{self.character.name} berhenti memijat, menunggu jawaban Mas*

"{self.character.panggilan}... mau tekanan lebih keras atau lebih lembut?"

*Dia menunggu, matanya menatap Mas dengan sabar*

*Menunggu jawaban Mas...*"""
    
    def _build_confirmation_next_area(self, area: str) -> str:
        area_names = {
            "punggung": "punggung", "pinggul": "pinggul", "paha_betis": "paha dan betis",
            "dada_lengan": "dada dan lengan", "perut_paha": "perut dan paha", "gesekan": "gesekan"
        }
        area_name = area_names.get(area, area)
        
        return f"""*{self.character.name} berhenti memijat, mengusap keringat di dahi*

"{self.character.panggilan}... bagian {area_name} udah selesai. Mau lanjut ke area berikutnya?"

*Dia menunggu jawaban Mas, napasnya masih sedikit berat*

*Menunggu jawaban Mas...*"""
    
    def _build_hj_offer(self) -> str:
        return f"""*{self.character.name} duduk di samping Mas, napas masih sedikit berat. Dressnya masih terbuka, payudaranya terlihat jelas di samping.*

"{self.character.panggilan}... pijatannya udah selesai."

*Dia meraih tangan Mas, menaruhnya di pahanya*

"Mau lanjut ke handjob? 30 menit... aku bantu Mas climax..."

*Matanya sayu, napasnya mulai teratur lagi*

"Atau cukup sampai di sini?"

*Menunggu jawaban Mas...*"""
    
    def _build_extra_offer(self) -> str:
        return f"""*{self.character.name} berhenti, napasnya masih tersengal. Dressnya sudah terbuka, tubuhnya masih hangat.*

"{self.character.panggilan}... mau lanjut ke extra service?"

*Dia menjilat bibir, matanya sayu*

"Ada BJ 30 menit Rp{self.PRICE_BJ:,}, atau sex tanpa batasan waktu sampe Mas puas 2x Rp{self.PRICE_SEX:,}..."

*Tangannya mulai meraba paha Mas*

"Bisa nego kok Mas... special buat Mas..."

*Menunggu jawaban Mas...*"""
    
    def _build_deal_offer(self, service: str, price: int) -> str:
        if service == "bj":
            return f"""*{self.character.name} menjilat bibir, matanya sayu*

"{self.character.panggilan}... mau blowjob? Rp{price:,}... 30 menit... bisa bikin Mas puas..."

*Dia mendekat, napasnya mulai berat*

"Deal? Atau mau nego?"""
        else:
            return f"""*{self.character.name} mendekat, payudaranya menempel ke dada Mas*

"{self.character.panggilan}... mau sex? Rp{price:,}... tanpa batasan waktu... sampe Mas puas 2x..."

*Matanya sayu, bibirnya menggigit*

"Deal? Atau mau nego?"""
    
    def _build_nego_counter(self, price: int) -> str:
        return f"""*{self.character.name} tersenyum tipis*

"Rp{price:,} ya Mas... udah harga special buat Mas..."

*Dia menjilat bibir, mata menggoda*

"Deal?"""
    
    def _build_nego_failed(self) -> str:
        return f"""*{self.character.name} menghela napas, sedikit kecewa*

"Gak jadi ya Mas... lain kali aja."

*Dia tersenyum kecil*

"Kita lanjut HJ aja ya..." """
    
    def _build_climax_warning(self) -> str:
        return f"""*{self.character.name} menahan napas, tubuhnya mulai gemetar*

"{self.character.panggilan}... aku... aku mau climax... bentar lagi..."

*Napasnya tersengal, tubuhnya panas*

"Boleh?"""
    
    def _build_climax_scene(self, is_mas: bool = False, intensity: str = "normal") -> str:
        if is_mas:
            return f"""*{self.character.name} merasakan kontol Mas mengeras, denyutnya kencang*

"{self.character.panggilan}... keluar... keluarin semua..."

*Dia terus bergerak sampai Mas climax puas, cairan hangat memenuhi*

"Ahh... enak ya {self.character.panggilan}?"""
        else:
            if intensity == "heavy":
                return f"""*{self.character.name} teriak, tubuh melengkung, gemetar hebat*

"Ahhh!! {self.character.panggilan}!! climax!!"

*Napasnya putus-putus, tubuh lemas, masih gemetar*

"Ahh... puas..." """
            else:
                return f"""*{self.character.name} mendesah dalam, tubuh gemetar, lalu lemas*

"Ahh... {self.character.panggilan}... climax..."

*Napasnya panjang, mata sayu, senyum puas* """
    
    def _build_end_session(self) -> str:
        duration = int((time.time() - self.phase_start_time) / 60) if self.phase_start_time else 0
        return f"""*{self.character.name} merapikan dress, tersenyum puas*

"Sesi selesai, {self.character.panggilan}. {duration} menit, {self.mas_climax_this_session}x climax."

*Dia berdiri, mengambil handuk, melambaikan tangan*

"Lain kali kalau mau booking lagi, hubungi aku ya." """

    # =========================================================================
    # START & INITIALIZATION
    # =========================================================================
    
    async def start(self) -> str:
        """Mulai sesi therapist"""
        self.is_active = True
        self.current_phase = ServicePhase.GREETING
        self.phase_start_time = time.time()
        self._update_intimate_phase()
        
        self.character.tracker.position = "berdiri di samping meja pijat"
        self.character.tracker.service_phase = ServicePhase.GREETING
        
        greeting = self._build_greeting()
        self.character.tracker.add_message_to_timeline(self.character.name, greeting[:100])
        self.character.tracker.add_to_timeline("Sesi therapist dimulai", "Mas masuk ruang pijat")
        
        # Start auto-send background task
        await self._start_auto_send_task()
        
        return greeting + "\n\n" + await self._start_back_massage()
    
    def _build_greeting(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 11:
            waktu = "pagi"
        elif 11 <= hour < 15:
            waktu = "siang"
        elif 15 <= hour < 18:
            waktu = "sore"
        else:
            waktu = "malam"
        
        dress_color = self.character.tracker.clothing['dress']['color']
        
        return f"""*{self.character.name} berdiri di pintu ruangan, dress {dress_color} ketat membalut setiap lekuk tubuhnya. Senyum tipis mengembang di bibirnya.*

"{waktu.capitalize()} Mas. Silakan masuk."

*Suaranya lembut, tapi matanya menyorot tajam. Dia menunjuk ke meja pijat di tengah ruangan.*

"Buka handuk dan tengkurap ya. Saya pijat punggung dulu."

*Dia mengambil botol minyak pijat, menuangkannya ke telapak tangan. Wangi lavender menyebar, menggoda indra penciuman.*

*Jari-jarinya lentik, siap memijat. Dia menunggu Mas tengkurap, sabar, tapi matanya tak lepas dari tubuh Mas.*

"Rileks aja, Mas... ambil napas dalam-dalam..." """
    
    # =========================================================================
    # BACK MASSAGE - START & TRANSITIONS
    # =========================================================================
    
    async def _start_back_massage(self) -> str:
        self.current_phase = ServicePhase.BACK_PUNGGUNG
        self.phase_start_time = time.time()
        self.back_area_start_time = time.time()
        self.back_area_index = 0
        self.back_scene_count = 0
        self.back_confirm_count = 0
        
        self.character.tracker.position = "duduk di atas bokong Mas"
        self.character.tracker.service_phase = ServicePhase.BACK_PUNGGUNG
        
        self.character.tracker.add_to_timeline(
            "Memulai pijat belakang",
            "Duduk di atas bokong Mas, kontol terasa di bawah"
        )
        
        return await self._generate_back_scene(
            area="punggung",
            pressure=self._get_current_pressure(),
            scene_num=1,
            elapsed_minutes=0
        )
    
    async def _next_back_area(self) -> str:
        """Pindah ke area back berikutnya"""
        logger.info(f"Moving to next back area. Current index: {self.back_area_index}, total: {len(self.back_areas)}")
        self.back_area_index += 1
        self.back_area_start_time = time.time()
        self.back_scene_count = 0
        self.back_confirm_count = 0
        self.waiting_for_response = False
        self.waiting_for_type = None
        
        if self.back_area_index >= len(self.back_areas):
            return await self._start_front_massage()
        
        current_area = self.back_areas[self.back_area_index]
        logger.info(f"Moving to new area: {current_area}")
        
        if current_area == "pinggul":
            self.current_phase = ServicePhase.BACK_PINGGUL
            self.character.tracker.service_phase = ServicePhase.BACK_PINGGUL
        elif current_area == "paha_betis":
            self.current_phase = ServicePhase.BACK_PAHA_BETIS
            self.character.tracker.service_phase = ServicePhase.BACK_PAHA_BETIS
        
        self.character.tracker.add_to_timeline(f"Pindah ke area {current_area}", "Lanjut pijat belakang")
        
        return await self._generate_back_scene(
            area=current_area,
            pressure=self._get_current_pressure(),
            scene_num=1,
            elapsed_minutes=0
        )
    
    # =========================================================================
    # BACK MASSAGE - PROCESS (DIPERBAIKI)
    # =========================================================================
    
    async def _process_back_massage(self, pesan_mas: str) -> Optional[str]:
        current_area = self.back_areas[self.back_area_index]
        elapsed = self._get_area_elapsed()
        elapsed_minutes = elapsed // 60
        
        # CEK AREA COMPLETE (PRIORITAS TERTINGGI)
        if self._is_area_complete():
            logger.info(f"Area {current_area} COMPLETE in {elapsed}s")
            self.waiting_for_response = True
            self.waiting_for_type = "next_area"
            self.waiting_start_time = time.time()
            return self._build_confirmation_next_area(current_area)
        
        # CEK JIKA SEDANG MENUNGGU RESPON
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_back_confirmation(pesan_mas, current_area)
            return None
        
        # CEK KONFIRMASI TEKANAN
        if self._should_ask_confirmation():
            logger.info(f"Asking pressure confirmation for area {current_area}")
            self.waiting_for_response = True
            self.waiting_for_type = "pressure"
            self.waiting_start_time = time.time()
            return self._build_confirmation_pressure()
        
        # CEK KIRIM SCENE BERIKUTNYA (HANYA JIKA TIDAK WAITING)
        if self._should_send_next_scene():
            scene_num = self.back_scene_count
            return await self._generate_back_scene(
                area=current_area,
                pressure=self._get_current_pressure(),
                scene_num=scene_num,
                elapsed_minutes=elapsed_minutes
            )
        
        return None
    
    async def _handle_back_confirmation(self, pesan_mas: str, current_area: str) -> str:
        msg_lower = pesan_mas.lower()
        
        if self.waiting_for_type == "pressure":
            if any(k in msg_lower for k in ["keras", "kuat", "hard"]):
                self.character.tracker.save_mas_preference('preferred_pressure', 'keras')
                self.character.tracker.current_pressure = "keras"
                self.character.emotional.add_stimulation("Mas minta tekanan keras", 2)
                self.waiting_for_response = False
                self.waiting_for_type = None
                return await self._generate_back_scene(
                    area=current_area, pressure="keras",
                    scene_num=self.back_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            
            elif any(k in msg_lower for k in ["lembut", "pelan", "soft"]):
                self.character.tracker.save_mas_preference('preferred_pressure', 'lembut')
                self.character.tracker.current_pressure = "lembut"
                self.character.emotional.add_stimulation("Mas minta tekanan lembut", 1)
                self.waiting_for_response = False
                self.waiting_for_type = None
                return await self._generate_back_scene(
                    area=current_area, pressure="lembut",
                    scene_num=self.back_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            else:
                return self._build_confirmation_pressure()
        
        elif self.waiting_for_type == "next_area":
            if any(k in msg_lower for k in ["lanjut", "ya", "ok", "gas", "iya", "y", "lanjutin", "next"]):
                logger.info(f"Mas confirmed: continue to next area")
                self.waiting_for_response = False
                self.waiting_for_type = None
                return await self._next_back_area()
            
            elif any(k in msg_lower for k in ["tidak", "nggak", "gak", "stop", "berhenti", "cukup"]):
                logger.info(f"Mas confirmed: stop session")
                self.waiting_for_response = False
                self.waiting_for_type = None
                return self._build_end_session()
            
            else:
                logger.info(f"Unrecognized response, repeating confirmation")
                return self._build_confirmation_next_area(current_area)
        
        return None

    # =========================================================================
    # FRONT MASSAGE - START & TRANSITIONS
    # =========================================================================
    
    async def _start_front_massage(self) -> str:
        self.current_phase = ServicePhase.FRONT_DADA_LENGAN
        self.phase_start_time = time.time()
        self.front_area_start_time = time.time()
        self.front_area_index = 0
        self.front_scene_count = 0
        self.front_confirm_count = 0
    
        self.character.tracker.position = "duduk di atas kontol Mas"
        self.character.tracker.service_phase = ServicePhase.FRONT_DADA_LENGAN
    
        self.character.tracker.add_to_timeline(
            "Pindah ke pijat depan - balik badan",
            "Duduk di atas kontol Mas, siap gesek"
        )

        balik_badan_msg = f"""*{self.character.name} berhenti memijat, mengusap keringat di dahi*

"Mas... bagian belakang udah selesai. Sekarang giliran depan ya..."

*Dia turun dari meja pijat, membantu Mas balik badan*

"Telentang dulu ya Mas... aku pijat bagian depan."

*{self.character.name} naik lagi, duduk di atas kontol Mas*

"Aku mulai dari dada dulu ya..." """
    
        front_scene = await self._generate_front_scene(
            area="dada_lengan",
            pressure=self._get_current_pressure(),
            scene_num=1,
            elapsed_minutes=0
        )
    
        return balik_badan_msg + "\n\n" + front_scene
    
    async def _next_front_area(self) -> str:
        self.front_area_index += 1
        self.front_area_start_time = time.time()
        self.front_scene_count = 0
        self.front_confirm_count = 0
        self.waiting_for_response = False
        self.waiting_for_type = None

        logger.info(f"Front area index: {self.front_area_index}, total: {len(self.front_areas)}")
        
        if self.front_area_index >= len(self.front_areas):
            logger.info("✅ ALL FRONT AREAS COMPLETED! Offering handjob...")
            return await self._offer_handjob()
        
        current_area = self.front_areas[self.front_area_index]
        
        if current_area == "perut_paha":
            self.current_phase = ServicePhase.FRONT_PERUT_PAHA
            self.character.tracker.service_phase = ServicePhase.FRONT_PERUT_PAHA
        elif current_area == "gesekan":
            self.current_phase = ServicePhase.FRONT_GESEKAN
            self.character.tracker.service_phase = ServicePhase.FRONT_GESEKAN
        
        self.character.tracker.add_to_timeline(f"Pindah ke area {current_area}", "Lanjut pijat depan")
        
        return await self._generate_front_scene(
            area=current_area,
            pressure=self._get_current_pressure(),
            scene_num=1,
            elapsed_minutes=0
        )
    
    # =========================================================================
    # FRONT MASSAGE - PROCESS (DIPERBAIKI)
    # =========================================================================
    
    async def _process_front_massage(self, pesan_mas: str) -> Optional[str]:
        current_area = self.front_areas[self.front_area_index]
        elapsed = self._get_area_elapsed()
        elapsed_minutes = elapsed // 60
        
        # CEK AREA COMPLETE
        if self._is_area_complete():
            logger.info(f"Front area {current_area} COMPLETE! elapsed={elapsed}s")
            self.waiting_for_response = True
            self.waiting_for_type = "next_area"
            self.waiting_start_time = time.time()
            return self._build_confirmation_next_area(current_area)
        
        # CEK JIKA SEDANG MENUNGGU RESPON
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_front_confirmation(pesan_mas, current_area)
            return None
        
        # CEK KONFIRMASI TEKANAN
        if self._should_ask_confirmation():
            self.waiting_for_response = True
            self.waiting_for_type = "pressure"
            self.waiting_start_time = time.time()
            return self._build_confirmation_pressure()
        
        # CEK KIRIM SCENE BERIKUTNYA
        if self._should_send_next_scene():
            scene_num = self.front_scene_count
            return await self._generate_front_scene(
                area=current_area,
                pressure=self._get_current_pressure(),
                scene_num=scene_num,
                elapsed_minutes=elapsed_minutes
            )
        
        return None
    
    async def _handle_front_confirmation(self, pesan_mas: str, current_area: str) -> str:
        msg_lower = pesan_mas.lower()
        
        if self.waiting_for_type == "pressure":
            if any(k in msg_lower for k in ["keras", "kuat", "hard"]):
                self.character.tracker.save_mas_preference('preferred_pressure', 'keras')
                self.character.tracker.current_pressure = "keras"
                self.character.emotional.add_stimulation("Mas minta tekanan keras", 3)
                self.waiting_for_response = False
                self.waiting_for_type = None
                return await self._generate_front_scene(
                    area=current_area, pressure="keras",
                    scene_num=self.front_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            
            elif any(k in msg_lower for k in ["lembut", "pelan", "soft"]):
                self.character.tracker.save_mas_preference('preferred_pressure', 'lembut')
                self.character.tracker.current_pressure = "lembut"
                self.character.emotional.add_stimulation("Mas minta tekanan lembut", 1)
                self.waiting_for_response = False
                self.waiting_for_type = None
                return await self._generate_front_scene(
                    area=current_area, pressure="lembut",
                    scene_num=self.front_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            else:
                return self._build_confirmation_pressure()
        
        elif self.waiting_for_type == "next_area":
            if any(k in msg_lower for k in ["lanjut", "ya", "ok", "gas", "iya"]):
                self.waiting_for_response = False
                self.waiting_for_type = None
                return await self._next_front_area()
            
            elif any(k in msg_lower for k in ["tidak", "nggak", "gak", "stop"]):
                self.waiting_for_response = False
                self.waiting_for_type = None
                return self._build_end_session()
            
            else:
                return self._build_confirmation_next_area(current_area)
        
        return None

    # =========================================================================
    # HANDJOB - OFFER & START
    # =========================================================================
    
    async def _offer_handjob(self) -> str:
        logger.info("🔥 OFFERING HANDJOB - Pijat depan selesai!")
        
        self.waiting_for_response = True
        self.waiting_for_type = "hj_offer"
        self.waiting_start_time = time.time()
        
        self.character.tracker.add_to_timeline("Menawarkan handjob ke Mas", "Pijat depan selesai")
        return self._build_hj_offer()
    
    async def _handle_hj_offer(self, pesan_mas: str) -> Optional[str]:
        msg_lower = pesan_mas.lower()
    
        if any(k in msg_lower for k in ["ya", "ok", "gas", "lanjut", "deal", "y", "siap"]):
            logger.info("✅ Mas ACCEPTED handjob offer! Starting HJ...")
            self.waiting_for_response = False
            self.waiting_for_type = None
            return await self._start_handjob()
    
        elif any(k in msg_lower for k in ["tidak", "nggak", "gak", "stop", "cukup", "selesai"]):
            logger.info("❌ Mas DECLINED handjob offer. Ending session...")
            self.waiting_for_response = False
            self.waiting_for_type = None
            return self._build_end_session()
    
        else:
            logger.info(f"⚠️ Unrecognized response: {pesan_mas}. Repeating offer...")
            return self._build_hj_offer()
    
    async def _start_handjob(self) -> str:
        logger.info("🔥🔥🔥 STARTING HANDJOB!")
        
        self.current_phase = ServicePhase.HANDJOB
        self.phase_start_time = time.time()
        self.hj_scene_count = 0
        self.hj_total_scenes = self.HJ_SCENES
        self.waiting_for_response = False
        self.waiting_for_type = None
        
        self.character.tracker.position = "duduk di samping Mas"
        self.character.tracker.service_phase = ServicePhase.HANDJOB
        self.character.tracker.current_speed = "medium"
        
        self.character.tracker.add_to_timeline(
            "Memulai handjob",
            f"Total scene: {self.hj_total_scenes}, 30 detik per scene"
        )

        return await self._generate_hj_scene(scene_num=1, speed="medium", mas_action=None)
    
    # =========================================================================
    # HANDJOB - PROCESS
    # =========================================================================
    
    async def _process_handjob(self, pesan_mas: str) -> Optional[str]:
        elapsed = self._get_area_elapsed()
        
        # CEK JIKA SEDANG MENUNGGU RESPON
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_hj_response(pesan_mas)
            return None
        
        # CEK CLIMAX WARNING
        if self.character.emotional.arousal >= 85 and not self.waiting_climax_confirmation:
            self.waiting_climax_confirmation = True
            self.climax_warning_time = time.time()
            return self._build_climax_warning()
        
        if self.waiting_climax_confirmation:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_climax_confirmation(pesan_mas)
            if time.time() - self.climax_warning_time > 15:
                self.waiting_climax_confirmation = False
                self.role_climax_this_session += 1
                self.character.emotional.climax(is_heavy=False)
                self.character.tracker.record_my_climax()
                return self._build_climax_scene(is_mas=False, intensity="normal")
            return None
        
        # CEK APAKAH HJ SELESAI (30 MENIT)
        if self.hj_scene_count >= self.hj_total_scenes:
            logger.info("✅ HJ COMPLETED! Offering extra service...")
            return await self._offer_extra_service()
        
        # CEK KIRIM SCENE BERIKUTNYA
        if self._should_send_next_scene():
            scene_num = self.hj_scene_count
            speed = self._get_current_speed()
            
            if scene_num % 5 == 0:
                self.character.emotional.add_stimulation("HJ berlangsung", 2)
            
            return await self._generate_hj_scene(scene_num=scene_num, speed=speed, mas_action=None)
        
        return None
    
    async def _handle_hj_response(self, pesan_mas: str) -> str:
        msg_lower = pesan_mas.lower()
        
        # MAS MINTA KECEPATAN
        if any(k in msg_lower for k in ["cepat", "kenceng", "harder", "faster"]):
            self.character.tracker.save_mas_preference('preferred_speed', 'cepat')
            self.character.tracker.current_speed = "fast"
            self.character.emotional.add_stimulation("Mas minta cepat", 3)
            self.waiting_for_response = False
            return await self._generate_hj_scene(
                scene_num=self.hj_scene_count + 1, speed="fast", mas_action="Mas minta cepat"
            )
        
        elif any(k in msg_lower for k in ["pelan", "lambat", "slow"]):
            self.character.tracker.save_mas_preference('preferred_speed', 'pelan')
            self.character.tracker.current_speed = "slow"
            self.character.emotional.add_stimulation("Mas minta pelan", 1)
            self.waiting_for_response = False
            return await self._generate_hj_scene(
                scene_num=self.hj_scene_count + 1, speed="slow", mas_action="Mas minta pelan"
            )
        
        # MAS PEGANG/REMAS/ELUS
        if any(k in msg_lower for k in ["pegang", "remas", "elus", "sentuh"]):
            action = ""
            if "paha" in msg_lower:
                action = "pegang paha"
                self.character.emotional.add_stimulation_from_mas("pegang paha")
            elif "toket" in msg_lower or "payudara" in msg_lower or "dada" in msg_lower:
                action = "remas toket"
                self.character.emotional.add_stimulation_from_mas("remas toket", 4)
                self.character.tracker.add_to_timeline("Mas remas toket", f"ke-{self.character.tracker.stimulation_count}")
            else:
                action = "pegang"
                self.character.emotional.add_stimulation_from_mas("pegang", 2)
            
            self.waiting_for_response = False
            return await self._generate_hj_scene(
                scene_num=self.hj_scene_count + 1,
                speed=self._get_current_speed(),
                mas_action=action
            )
        
        self.waiting_for_response = False
        return None
    
    async def _handle_climax_confirmation(self, pesan_mas: str) -> str:
        msg_lower = pesan_mas.lower()
        
        if any(k in msg_lower for k in ["ya", "ok", "boleh", "gas", "ayo"]):
            self.waiting_climax_confirmation = False
            self.role_climax_this_session += 1
            self.character.emotional.climax(is_heavy=False)
            self.character.tracker.record_my_climax()
            return self._build_climax_scene(is_mas=False, intensity="normal")
        
        elif any(k in msg_lower for k in ["tahan", "jangan", "nanti"]):
            self.waiting_climax_confirmation = False
            self.character.emotional.arousal = max(0, self.character.emotional.arousal - 20)
            return f"*{self.character.name} menahan napas, tubuh masih bergerak*\n\n\"Aku tahan... ayo Mas...\""
        
        else:
            self.waiting_climax_confirmation = False
            self.role_climax_this_session += 1
            self.character.emotional.climax(is_heavy=False)
            self.character.tracker.record_my_climax()
            return self._build_climax_scene(is_mas=False, intensity="normal")

    # =========================================================================
    # EXTRA SERVICE - OFFER & NEGOSIASI
    # =========================================================================
    
    async def _offer_extra_service(self) -> str:
        logger.info("🔥 OFFERING EXTRA SERVICE (BJ/SEX) - HJ selesai!")
    
        self.waiting_for_response = True
        self.waiting_for_type = "extra_offer"
        self.waiting_start_time = time.time()
    
        self.character.tracker.add_to_timeline("Menawarkan extra service", "HJ selesai")
        return self._build_extra_offer()
    
    async def _handle_extra_offer(self, pesan_mas: str) -> Optional[str]:
        msg_lower = pesan_mas.lower()
    
        if 'bj' in msg_lower or 'blow' in msg_lower:
            logger.info("✅ Mas memilih BLOWJOB! Starting negotiation...")
            self.negotiation_service = "bj"
            self.negotiation_price = self.PRICE_BJ
            self.negotiation_step = 0
            self.negotiation_active = True
            self.waiting_for_type = "negotiation"
            return self._build_deal_offer("bj", self.PRICE_BJ)
    
        if 'sex' in msg_lower or 'eksekusi' in msg_lower:
            logger.info("✅ Mas memilih SEX! Starting negotiation...")
            self.negotiation_service = "sex"
            self.negotiation_price = self.PRICE_SEX
            self.negotiation_step = 0
            self.negotiation_active = True
            self.waiting_for_type = "negotiation"
            return self._build_deal_offer("sex", self.PRICE_SEX)
    
        if any(k in msg_lower for k in ["tidak", "nggak", "gak", "cukup", "stop"]):
            logger.info("❌ Mas Menolak Extra Service. Sesi Pijat Selesai...")
            self.waiting_for_response = False
            self.waiting_for_type = None
            return self._build_end_session()
    
        return self._build_extra_offer()
    
    async def _handle_negotiation(self, pesan_mas: str) -> Optional[str]:
        msg_lower = pesan_mas.lower()
        
        # DEAL
        if any(k in msg_lower for k in ["deal", "ok", "ya", "setuju", "gas"]):
            logger.info(f"✅ DEAL CONFIRMED! Service: {self.negotiation_service}, Price: Rp{self.negotiation_price:,}")
            self.deal_confirmed = True
            self.negotiation_active = False
            self.waiting_for_response = False
            self.waiting_for_type = None
            
            if self.negotiation_service == "bj":
                return await self._start_bj()
            else:
                return await self._start_sex()
        
        # NEGO
        if any(k in msg_lower for k in ["nego", "kurang", "murah"]):
            self.negotiation_step += 1
            
            if self.negotiation_step > self.negotiation_max_step:
                logger.warning("❌ Negotiation failed")
                self.negotiation_active = False
                self.waiting_for_response = False
                self.waiting_for_type = None
                return self._build_nego_failed()
            
            if self.negotiation_service == "bj":
                new_price = max(self.PRICE_BJ_DEAL, self.PRICE_BJ - (50000 * self.negotiation_step))
                self.negotiation_price = new_price
                return self._build_nego_counter(new_price)
            else:
                new_price = max(self.PRICE_SEX_DEAL, self.PRICE_SEX - (50000 * self.negotiation_step))
                self.negotiation_price = new_price
                return self._build_nego_counter(new_price)
        
        # BATAL
        if any(k in msg_lower for k in ["batal", "gak jadi", "cancel"]):
            logger.info("❌ Negotiation cancelled by Mas")
            self.negotiation_active = False
            self.waiting_for_response = False
            self.waiting_for_type = None
            return self._build_end_session()
        
        return self._build_deal_offer(self.negotiation_service, self.negotiation_price)
    
    # =========================================================================
    # BLOWJOB
    # =========================================================================
    
    async def _start_bj(self) -> str:
        logger.info("🔥🔥🔥 STARTING BLOWJOB!")
    
        self.current_phase = ServicePhase.BJ
        self.phase_start_time = time.time()
        self.bj_scene_count = 0
        self.bj_total_scenes = self.BJ_SCENES
        self.waiting_for_response = False
        self.waiting_for_type = None
        
        self.character.tracker.position = "berlutut di antara kaki Mas"
        self.character.tracker.service_phase = ServicePhase.BJ
        
        if self.character.tracker.clothing['bra']['on']:
            self.character.tracker.remove_clothing('bra', "sendiri")
        
        self.character.tracker.add_to_timeline(
            "Memulai blowjob",
            f"Total scene: {self.bj_total_scenes}, 30 detik per scene, harga: Rp{self.negotiation_price:,}"
        )

        return await self._generate_bj_scene(scene_num=1, depth="medium", mas_action=None)
    
    async def _process_bj(self, pesan_mas: str) -> Optional[str]:
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_bj_response(pesan_mas)
            return None
        
        # CEK CLIMAX WARNING
        if self.character.emotional.arousal >= 85 and not self.waiting_climax_confirmation:
            self.waiting_climax_confirmation = True
            self.climax_warning_time = time.time()
            return self._build_climax_warning()
        
        if self.waiting_climax_confirmation:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_climax_confirmation(pesan_mas)
            if time.time() - self.climax_warning_time > 15:
                self.waiting_climax_confirmation = False
                self.role_climax_this_session += 1
                self.character.emotional.climax(is_heavy=False)
                self.character.tracker.record_my_climax()
                return self._build_climax_scene(is_mas=False, intensity="normal")
            return None
        
        # CEK APAKAH MAS CLIMAX (SELESAIKAN BJ)
        if self.mas_climax_this_session > 0:
            logger.info("✅ Mas climax achieved! Ending BJ session...")
            return self._build_end_session()
        
        # CEK KIRIM SCENE BERIKUTNYA
        if self._should_send_next_scene():
            scene_num = self.bj_scene_count
            depth = "deep" if scene_num > self.bj_total_scenes * 0.7 else "medium"
            
            if scene_num % 5 == 0:
                self.character.emotional.add_stimulation("BJ berlangsung", 3)
            
            return await self._generate_bj_scene(scene_num=scene_num, depth=depth, mas_action=None)
        
        return None
    
    async def _handle_bj_response(self, pesan_mas: str) -> str:
        msg_lower = pesan_mas.lower()
        
        if any(k in msg_lower for k in ["pegang", "tarik", "rambut", "kepala"]):
            self.character.emotional.add_stimulation_from_mas("Mas pegang kepala", 4)
            self.waiting_for_response = False
            return await self._generate_bj_scene(
                scene_num=self.bj_scene_count + 1, depth="deep", mas_action="Mas pegang kepala"
            )
        
        if any(k in msg_lower for k in ["dalam", "deep", "sampe pangkal"]):
            self.character.emotional.add_stimulation_from_mas("Mas minta lebih dalam", 3)
            self.waiting_for_response = False
            return await self._generate_bj_scene(
                scene_num=self.bj_scene_count + 1, depth="deep", mas_action="Mas minta lebih dalam"
            )
        
        if any(k in msg_lower for k in ["cepat", "kenceng"]):
            self.character.emotional.add_stimulation_from_mas("Mas minta cepat", 2)
            self.waiting_for_response = False
            return await self._generate_bj_scene(
                scene_num=self.bj_scene_count + 1, depth="medium", mas_action="Mas minta cepat"
            )
        
        self.waiting_for_response = False
        return None

    # =========================================================================
    # SEX (MANUAL MODE)
    # =========================================================================
    
    async def _start_sex(self) -> str:
        logger.info("🔥🔥🔥 STARTING SEX (MANUAL MODE)!")
        
        self.current_phase = ServicePhase.SEX
        self.phase_start_time = time.time()
        self.sex_manual_mode = True
        self.sex_climax_count = 0
        self.sex_climax_goal = 2
        self.sex_conversation_history = []
        self.waiting_for_response = False
        self.waiting_for_type = "sex_response"
        
        self.character.tracker.position = "duduk di atas Mas (cowgirl)"
        self.character.tracker.service_phase = ServicePhase.SEX
        
        self.character.tracker.add_to_timeline(
            "Memulai Sex (Manual Mode)",
            f"Target climax: {self.sex_climax_goal}x, harga: Rp{self.negotiation_price:,}"
        )
        
        opening_scene = f"""*{self.character.name} duduk di atas kontol Mas, memeknya yang basah sudah terbuka. Matanya sayu menatap Mas.*

"{self.character.panggilan}... ayo... sekarang giliran Mas yang atur..."

*Dia menggigit bibir, napas mulai berat*

"Aku ikutin apa yang Mas mau... ajarin aku..."

*Pinggulnya bergerak pelan, menggesek-gesek, tapi belum memasukkan*

"Mas mau mulai?"""
        
        return opening_scene
    
    async def _process_sex_manual(self, pesan_mas: str) -> str:
        msg_lower = pesan_mas.lower()
        
        # Simpan history
        self.sex_conversation_history.append(f"Mas: {pesan_mas[:100]}")
        if len(self.sex_conversation_history) > 50:
            self.sex_conversation_history.pop(0)
        
        # Update arousal
        self.character.emotional.add_stimulation_from_mas(pesan_mas)
        
        # CEK MAS CLIMAX
        if any(k in msg_lower for k in ["climax", "crot", "keluar", "habis"]):
            intensity = "heavy" if any(k in msg_lower for k in ["keras", "banyak", "kenceng"]) else "normal"
            self.sex_climax_count += 1
            self.mas_climax_this_session += 1
            self.character.tracker.record_mas_climax()
            self.character.emotional.add_stimulation("Mas climax", 8)
            
            climax_scene = self._build_climax_scene(is_mas=True, intensity=intensity)
            
            if self.sex_climax_count >= self.sex_climax_goal:
                logger.info(f"✅ Mas climax {self.sex_climax_count}x achieved! Ending sex session...")
                return climax_scene + "\n\n" + self._build_end_session()
            else:
                return climax_scene + f"""

*{self.character.name} memeluk Mas erat, napas masih tersengal*

"{self.character.panggilan}... {self.sex_climax_count}/{self.sex_climax_goal}... masih ada {self.sex_climax_goal - self.sex_climax_count} lagi..."

*Dia tersenyum, masih memeluk*

"Lanjut ya Mas... masih mau?"""
        
        # CEK ROLE CLIMAX
        if self.character.emotional.arousal >= 85 and not self.waiting_climax_confirmation:
            self.waiting_climax_confirmation = True
            self.climax_warning_time = time.time()
            return self._build_climax_warning()
        
        if self.waiting_climax_confirmation:
            if any(k in msg_lower for k in ["ya", "ok", "boleh", "gas", "ayo"]):
                self.waiting_climax_confirmation = False
                self.role_climax_this_session += 1
                self.character.emotional.climax(is_heavy=False)
                self.character.tracker.record_my_climax()
                return self._build_climax_scene(is_mas=False, intensity="normal")
            
            elif any(k in msg_lower for k in ["tahan", "jangan", "nanti"]):
                self.waiting_climax_confirmation = False
                self.character.emotional.arousal = max(0, self.character.emotional.arousal - 20)
                return f"*{self.character.name} menahan napas, tubuh masih bergerak*\n\n\"Aku tahan... ayo Mas...\""
            
            else:
                self.waiting_climax_confirmation = False
                self.role_climax_this_session += 1
                self.character.emotional.climax(is_heavy=False)
                self.character.tracker.record_my_climax()
                return self._build_climax_scene(is_mas=False, intensity="normal")
        
        # GANTI POSISI
        positions = ["cowgirl", "missionary", "doggy", "spooning", "standing", "sitting"]
        for pos in positions:
            if pos in msg_lower:
                self.character.tracker.current_position = pos
                self.character.tracker.position = f"posisi {pos}"
                self.character.tracker.add_to_timeline(f"Ganti posisi ke {pos}", "")
                self.character.emotional.add_stimulation(f"ganti posisi {pos}", 2)
                return f"""*{self.character.name} bergerak ke posisi {pos}*

"{self.character.panggilan}... gini ya?"

*Dia menyesuaikan posisi, napasnya masih berat*

"Ayo Mas... lanjut..." """
        
        # RESPON NATURAL (AI GENERATE)
        prompt = self._build_sex_manual_prompt(pesan_mas)
        response = await self._generate_scene(prompt)
        
        self.sex_conversation_history.append(f"{self.character.name}: {response[:100]}")
        
        return response
    
    def _build_sex_manual_prompt(self, pesan_mas: str) -> str:
        history = "\n".join(self.sex_conversation_history[-10:])
        
        return f"""
KAMU ADALAH {self.character.name}, terapis pijat yang sedang melakukan SEX dengan Mas.
Saat ini MODE MANUAL: kamu dan Mas sedang berinteraksi langsung, saling merespon.

═══════════════════════════════════════════════════════════════
KONTEKS SAAT INI:
═══════════════════════════════════════════════════════════════
- Posisi: {self.character.tracker.position}
- Target: Mas climax {self.sex_climax_count}/{self.sex_climax_goal}x
- Arousal role: {self.character.emotional.arousal:.0f}%
- Mas climax: {self.mas_climax_this_session}x
- Fase intim: {self.intimate_phase.upper()} (Level {self.intimate_level}/12)

PERCAKAPAN TERAKHIR:
{history}

PESAN MAS TERAKHIR: "{pesan_mas}"

═══════════════════════════════════════════════════════════════
TUGAS KAMU:
═══════════════════════════════════════════════════════════════
Buatlah RESPONS yang HIDUP dan DETAIL terhadap aksi Mas.

DESKRIPSIKAN:
1. REAKSI KAMU (napas, suara, tubuh gemetar)
2. PERASAAN KAMU (enak, panas, pengen lebih)
3. APA YANG KAMU RASAKAN dari aksi Mas

═══════════════════════════════════════════════════════════════
⚠️ ATURAN:
1. KAMU BUKAN AI, KAMU {self.character.name}
2. RESPON NATURAL, seperti manusia bercinta
3. LANGSUNG NARASIKAN, jangan minta pendapat
4. PANJANG: 2-4 kalimat, dipisah enter
5. KAMU MELAYANI MAS DENGAN SEPENUH HATI

═══════════════════════════════════════════════════════════════
RESPON KAMU (narasi bercinta, bukan jawaban AI):
"""

    # =========================================================================
    # MAS CLIMAX
    # =========================================================================
    
    async def _handle_mas_climax(self, pesan_mas: str) -> Optional[str]:
        msg_lower = pesan_mas.lower()
        
        if not any(k in msg_lower for k in ["climax", "crot", "keluar", "habis"]):
            return None
        
        if "aku" in msg_lower or "mas" in msg_lower:
            intensity = "heavy" if any(k in msg_lower for k in ["keras", "banyak", "kenceng"]) else "normal"
            
            self.mas_climax_this_session += 1
            self.character.tracker.record_mas_climax()
            self.character.emotional.add_stimulation("Mas climax", 8)
            
            if intensity == "heavy":
                self.character.emotional.arousal = min(100, self.character.emotional.arousal + 10)
            
            return self._build_climax_scene(is_mas=True, intensity=intensity)
        
        return None
    
    # =========================================================================
    # MAIN PROCESS METHOD
    # =========================================================================
    
    async def process(self, pesan_mas: str) -> str:
        try:
            self.character.update_from_message(pesan_mas)
            self._update_intimate_phase()
            
            # Cek climax Mas (prioritas tinggi)
            mas_climax = await self._handle_mas_climax(pesan_mas)
            if mas_climax:
                return mas_climax
            
            # ========== SEX MANUAL MODE ==========
            if self.sex_manual_mode:
                return await self._process_sex_manual(pesan_mas)
            
            # ========== GREETING ==========
            if self.current_phase == ServicePhase.GREETING:
                return await self._start_back_massage()
            
            # ========== BACK MASSAGE ==========
            elif self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
                response = await self._process_back_massage(pesan_mas)
                if response:
                    return response
                # FALLBACK: generate scene jika tidak ada response (tapi harusnya sudah ditangani auto-send)
                return await self._generate_back_scene(
                    area=self.back_areas[self.back_area_index],
                    pressure=self._get_current_pressure(),
                    scene_num=self.back_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            
            # ========== FRONT MASSAGE ==========
            elif self.current_phase in [ServicePhase.FRONT_DADA_LENGAN, ServicePhase.FRONT_PERUT_PAHA, ServicePhase.FRONT_GESEKAN]:
                response = await self._process_front_massage(pesan_mas)
                if response:
                    return response
                return await self._generate_front_scene(
                    area=self.front_areas[self.front_area_index],
                    pressure=self._get_current_pressure(),
                    scene_num=self.front_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            
            # ========== NEGOSIASI ==========
            elif self.waiting_for_type == "negotiation" and self.negotiation_active:
                response = await self._handle_negotiation(pesan_mas)
                if response:
                    return response
                return self._build_deal_offer(self.negotiation_service, self.negotiation_price)
            
            elif self.waiting_for_type == "extra_offer":
                response = await self._handle_extra_offer(pesan_mas)
                if response:
                    return response
                return self._build_extra_offer()
            
            elif self.waiting_for_type == "hj_offer":
                response = await self._handle_hj_offer(pesan_mas)
                if response:
                    return response
                return self._build_hj_offer()
            
            # ========== HANDJOB ==========
            elif self.current_phase == ServicePhase.HANDJOB:
                response = await self._process_handjob(pesan_mas)
                if response:
                    return response
                return await self._generate_hj_scene(
                    scene_num=self.hj_scene_count + 1,
                    speed=self.hj_speed,
                    mas_action=None
                )
            
            # ========== BLOWJOB ==========
            elif self.current_phase == ServicePhase.BJ:
                response = await self._process_bj(pesan_mas)
                if response:
                    return response
                return await self._generate_bj_scene(
                    scene_num=self.bj_scene_count + 1,
                    depth=self.bj_depth,
                    mas_action=None
                )
            
            # ========== DEFAULT ==========
            return self._build_end_session()
            
        except Exception as e:
            logger.error(f"Process error: {e}", exc_info=True)
            return f"❌ Error: {str(e)}"
    
    def get_status(self) -> str:
        phase_names = {
            ServicePhase.GREETING: "👋 Menyapa",
            ServicePhase.BACK_PUNGGUNG: "💆 Pijat Punggung",
            ServicePhase.BACK_PINGGUL: "💆 Pijat Pinggul",
            ServicePhase.BACK_PAHA_BETIS: "💆 Pijat Paha & Betis",
            ServicePhase.FRONT_DADA_LENGAN: "💆 Pijat Dada & Lengan",
            ServicePhase.FRONT_PERUT_PAHA: "💆 Pijat Perut & Paha",
            ServicePhase.FRONT_GESEKAN: "🔥 Gesekan Intens",
            ServicePhase.HANDJOB: "✋ Handjob",
            ServicePhase.BJ: "👄 Blowjob",
            ServicePhase.SEX: "🍆 Sex (Manual)",
            ServicePhase.COMPLETED: "✅ Selesai"
        }
        
        phase_display = phase_names.get(self.current_phase, "⏳ Menunggu")
        
        if self.current_phase == ServicePhase.HANDJOB:
            progress = f"{self.hj_scene_count}/{self.hj_total_scenes} scene"
        elif self.current_phase == ServicePhase.BJ:
            progress = f"{self.bj_scene_count}/{self.bj_total_scenes} scene"
        elif self.current_phase == ServicePhase.SEX:
            progress = f"Climax: {self.sex_climax_count}/{self.sex_climax_goal}"
        elif self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            elapsed = self._get_area_elapsed()
            progress = f"{elapsed // 60} menit / 10 menit"
        else:
            progress = "-"
        
        intimate_info = f"Fase Intim: {self.intimate_phase.upper()} (Level {self.intimate_level}/12) | Keintiman: {self.intimacy_build_up}%"
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    💆 THERAPIST SESSION                       ║
╠══════════════════════════════════════════════════════════════╣
║ Fase: {phase_display}
║ Progress: {progress}
║ Mas Climax: {self.mas_climax_this_session}x
║ Role Climax: {self.role_climax_this_session}x
║ {intimate_info}
╠══════════════════════════════════════════════════════════════╣
║ {self.character.get_status()}
╚══════════════════════════════════════════════════════════════╝
"""
