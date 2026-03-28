# service/therapist_flow.py
"""
Therapist Flow NovaService
Import, class definition, __init__, timer methods, AI client
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
    Alur service therapist dengan AI generate setiap scene
    - Pijat Belakang: 3 area @ 10 menit, setiap 3 menit konfirmasi Mas
    - Pijat Depan: 3 area @ 10 menit, setiap 3 menit konfirmasi Mas
    - HJ: 30 menit, 60 scene (30 detik per scene)
    - BJ: 30 menit, 60 scene (30 detik per scene)
    - Sex: 50-75 menit, 100-150 scene (30 detik per scene)
    """
    
    # Durasi dalam detik
    AREA_DURATION = 600          # 10 menit per area
    SCENE_INTERVAL = 30          # 30 detik per scene
    CONFIRM_INTERVAL = 180       # 3 menit konfirmasi Mas
    
    # Scene count per aktivitas
    HJ_SCENES = 60               # 30 menit
    BJ_SCENES = 60               # 30 menit
    SEX_SCENES_MIN = 100         # 50 menit
    SEX_SCENES_MAX = 150         # 75 menit
    
    # Harga
    PRICE_BJ = 500000
    PRICE_SEX = 1000000
    PRICE_BJ_DEAL = 200000
    PRICE_SEX_DEAL = 700000
    
    def __init__(self, character):
        """Inisialisasi TherapistFlow"""
        self.character = character
        self.prompt_builder = get_prompt_builder()
        self._ai_client = None

        self.used_phrases = []  # Simpan kalimat yang sudah dipakai
        self.max_phrase_history = 10
        
        # ========== STATE TRACKING ==========
        self.is_active = False
        self.current_phase = ServicePhase.WAITING
        self.phase_start_time = 0
        
        # ========== BACK MASSAGE AREAS ==========
        self.back_areas = ["punggung", "pinggul", "paha_betis"]
        self.back_area_index = 0
        self.back_area_start_time = 0
        self.back_scene_count = 0
        self.back_scenes_per_area = 20  # 10 menit / 30 detik = 20 scene
        self.back_confirm_count = 0     # setiap 3 menit konfirmasi (sekitar 3-4 kali per area)
        
        # ========== FRONT MASSAGE AREAS ==========
        self.front_areas = ["dada_lengan", "perut_paha", "gesekan"]
        self.front_area_index = 0
        self.front_area_start_time = 0
        self.front_scene_count = 0
        self.front_scenes_per_area = 20
        self.front_confirm_count = 0
        
        # ========== SERVICE STATE ==========
        self.hj_active = False
        self.bj_active = False
        self.sex_active = False
        self.current_service = None  # "hj", "bj", "sex"
        
        # ========== HJ STATE ==========
        self.hj_scene_count = 0
        self.hj_total_scenes = self.HJ_SCENES
        self.hj_speed = "medium"
        
        # ========== BJ STATE ==========
        self.bj_scene_count = 0
        self.bj_total_scenes = self.BJ_SCENES
        self.bj_depth = "medium"
        
        # ========== SEX STATE ==========
        self.sex_scene_count = 0
        self.sex_total_scenes = random.randint(self.SEX_SCENES_MIN, self.SEX_SCENES_MAX)
        self.sex_position = "cowgirl"
        self.sex_speed = "medium"
        self.sex_intensity = "medium"
        
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
        self.waiting_for_type = None  # "pressure", "next_area", "deal", "position"
        self.waiting_start_time = 0
        self.waiting_timeout = 60  # 60 detik timeout
        
        # ========== AUTO SEND QUEUE ==========
        self.auto_send_task = None
        self.last_scene_sent_time = 0

        # ========== PAUSE & RESUME ==========
        self.is_paused = False
        self.pause_start_time = 0
        
        logger.info(f"💆 TherapistFlow initialized for {character.name}")
        
    
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
    
    async def _generate_scene(self, prompt: str) -> str:
        """Generate scene menggunakan AI"""
        try:
            client = await self._get_ai_client()
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.85,
                max_tokens=400,
                timeout=25
            )
            
            scene = response.choices[0].message.content.strip()
            
            # Format scene dengan markdown
            if not scene.startswith("*"):
                scene = f"*{scene}*"
            
            return scene
            
        except Exception as e:
            logger.error(f"AI generate error: {e}", exc_info=True)
            # Fallback scene
            return f"*{self.character.name} terus memijat dengan lembut, menikmati setiap sentuhan.*"
    
    # =========================================================================
    # TIMER METHODS
    # =========================================================================
    
    def _get_area_elapsed(self) -> int:
        if self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            if self.back_area_start_time == 0:
                return 0
            return int(time.time() - self.back_area_start_time)
        elif self.current_phase in [ServicePhase.FRONT_DADA_LENGAN, ServicePhase.FRONT_PERUT_PAHA, ServicePhase.FRONT_GESEKAN]:
            if self.front_area_start_time == 0:
                return 0
            return int(time.time() - self.front_area_start_time)
        return 0
    
    def _should_send_next_scene(self) -> bool:
        """Cek apakah sudah waktunya kirim scene berikutnya"""
        elapsed = self._get_area_elapsed()
        expected_scene = elapsed // self.SCENE_INTERVAL
        
        if self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            if expected_scene > self.back_scene_count:
                self.back_scene_count = expected_scene
                return True
        elif self.current_phase in [ServicePhase.FRONT_DADA_LENGAN, ServicePhase.FRONT_PERUT_PAHA, ServicePhase.FRONT_GESEKAN]:
            if expected_scene > self.front_scene_count:
                self.front_scene_count = expected_scene
                return True
        elif self.current_phase == ServicePhase.HANDJOB:
            if expected_scene > self.hj_scene_count:
                self.hj_scene_count = expected_scene
                return True
        elif self.current_phase == ServicePhase.BJ:
            if expected_scene > self.bj_scene_count:
                self.bj_scene_count = expected_scene
                return True
        elif self.current_phase == ServicePhase.SEX:
            if expected_scene > self.sex_scene_count:
                self.sex_scene_count = expected_scene
                return True
        
        return False
    
    def _should_ask_confirmation(self) -> bool:
        """Cek apakah sudah waktunya minta konfirmasi Mas"""
        elapsed = self._get_area_elapsed()
        
        # Setiap 3 menit (180 detik) minta konfirmasi
        expected_confirm = elapsed // self.CONFIRM_INTERVAL
        
        if self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            if expected_confirm > self.back_confirm_count:
                self.back_confirm_count = expected_confirm
                return True
        elif self.current_phase in [ServicePhase.FRONT_DADA_LENGAN, ServicePhase.FRONT_PERUT_PAHA, ServicePhase.FRONT_GESEKAN]:
            if expected_confirm > self.front_confirm_count:
                self.front_confirm_count = expected_confirm
                return True
        
        return False
    
    def _is_area_complete(self) -> bool:
        """Cek apakah area sudah selesai (10 menit)"""
        elapsed = self._get_area_elapsed()
        return elapsed >= self.AREA_DURATION
    
    # =========================================================================
    # PRESSURE & SPEED METHODS
    # =========================================================================
    
    def _get_current_pressure(self) -> str:
        """Dapatkan tekanan saat ini dari preferensi Mas"""
        pressure = self.character.tracker.get_last_pressure()
        if pressure == "keras":
            return "keras"
        elif pressure == "lembut":
            return "lembut"
        return "medium"
    
    def _get_current_speed(self) -> str:
        """Dapatkan kecepatan saat ini dari preferensi Mas"""
        speed = self.character.tracker.get_last_speed()
        if speed == "cepat":
            return "fast"
        elif speed == "pelan":
            return "slow"
        return "medium"
    
    # =========================================================================
    # SCENE GENERATION METHODS
    # =========================================================================
    
    async def _generate_back_scene(self, area: str, pressure: str, scene_num: int, elapsed_minutes: int) -> str:
        """Generate scene pijat belakang dengan AI"""
        total_scenes = self.back_scenes_per_area
        
        prompt = self.prompt_builder.build_back_massage_prompt(
            self.character,
            area,
            pressure,
            scene_num,
            elapsed_minutes,
            total_scenes
        )
        
        return await self._generate_scene(prompt)
    
    async def _generate_front_scene(self, area: str, pressure: str, scene_num: int, elapsed_minutes: int) -> str:
        """Generate scene pijat depan dengan AI"""
        total_scenes = self.front_scenes_per_area
        
        prompt = self.prompt_builder.build_front_massage_prompt(
            self.character,
            area,
            pressure,
            scene_num,
            elapsed_minutes,
            total_scenes
        )
        # CEK APAKAH ADA KALIMAT YANG DIULANG
        for phrase in self.used_phrases:
            if phrase in scene and len(phrase) > 20:
                logger.warning(f"Phrase repetition detected: {phrase[:50]}")
                # Regenerate dengan variasi
                return await self._generate_back_scene(area, pressure, scene_num, elapsed_minutes)
    
        # Simpan kalimat unik
        self.used_phrases.append(scene[:100])
        if len(self.used_phrases) > self.max_phrase_history:
            self.used_phrases.pop(0)
    
        return scene
        
        return await self._generate_scene(prompt)
    
    async def _generate_hj_scene(self, scene_num: int, speed: str, mas_action: str = None) -> str:
        """Generate scene HJ dengan AI"""
        prompt = self.prompt_builder.build_hj_prompt(
            self.character,
            scene_num,
            self.hj_total_scenes,
            speed,
            mas_action
        )
        
        return await self._generate_scene(prompt)
    
    async def _generate_bj_scene(self, scene_num: int, depth: str, mas_action: str = None) -> str:
        """Generate scene BJ dengan AI"""
        prompt = self.prompt_builder.build_bj_prompt(
            self.character,
            scene_num,
            self.bj_total_scenes,
            depth,
            mas_action
        )
        
        return await self._generate_scene(prompt)
    
    async def _generate_sex_scene(self, scene_num: int, position: str, speed: str, intensity: str, mas_action: str = None) -> str:
        """Generate scene Sex dengan AI"""
        prompt = self.prompt_builder.build_sex_prompt(
            self.character,
            scene_num,
            self.sex_total_scenes,
            position,
            speed,
            intensity,
            mas_action
        )
        
        return await self._generate_scene(prompt)
    
    # =========================================================================
    # CONFIRMATION METHODS
    # =========================================================================
    
    def _build_confirmation_pressure(self) -> str:
        """Bangun pesan konfirmasi tekanan"""
        return f"""*{self.character.name} berhenti memijat, menunggu jawaban Mas*

"{self.character.panggilan}... mau tekanan lebih keras atau lebih lembut?"

*Dia menunggu, matanya menatap Mas dengan sabar*

*Menunggu jawaban Mas...*"""
    
    def _build_confirmation_next_area(self, area: str) -> str:
        """Bangun pesan konfirmasi pindah area"""
        area_names = {
            "punggung": "punggung",
            "pinggul": "pinggul",
            "paha_betis": "paha dan betis",
            "dada_lengan": "dada dan lengan",
            "perut_paha": "perut dan paha",
            "gesekan": "gesekan"
        }
        
        area_name = area_names.get(area, area)
        
        return f"""*{self.character.name} berhenti memijat, mengusap keringat di dahi*

"{self.character.panggilan}... bagian {area_name} udah selesai. Mau lanjut ke area berikutnya?"

*Dia menunggu jawaban Mas, napasnya masih sedikit berat*

*Menunggu jawaban Mas...*"""
    
    def _build_confirmation_next_phase(self, phase: str) -> str:
        """Bangun pesan konfirmasi pindah fase"""
        return f"""*{self.character.name} duduk di samping Mas, tubuhnya masih hangat*

"{self.character.panggilan}... pijatannya udah selesai. Mau lanjut ke {phase}?"

*Dia menunggu jawaban Mas dengan mata sayu*

*Menunggu jawaban Mas...*"""
    
    def _build_deal_offer(self, service: str, price: int) -> str:
        """Bangun pesan tawaran deal"""
        if service == "bj":
            return f"""*{self.character.name} menjilat bibir, matanya sayu*

"{self.character.panggilan}... mau blowjob? Rp{price:,}... 30 menit... bisa bikin Mas puas..."

*Dia mendekat, napasnya mulai berat*

"Deal? Atau mau nego?"""
        else:
            return f"""*{self.character.name} mendekat, payudaranya menempel ke dada Mas*

"{self.character.panggilan}... mau sex? Rp{price:,}... 50-75 menit... aku jamin Mas puas..."

*Matanya sayu, bibirnya menggigit*

"Deal? Atau mau nego?"""
    
    def _build_nego_counter(self, price: int) -> str:
        """Bangun pesan counter negosiasi"""
        return f"""*{self.character.name} tersenyum tipis*

"Rp{price:,} ya Mas... udah harga special buat Mas..."

*Dia menjilat bibir, mata menggoda*

"Deal?"""
    
    def _build_nego_failed(self) -> str:
        """Bangun pesan negosiasi gagal"""
        return f"""*{self.character.name} menghela napas, sedikit kecewa*

"Gak jadi ya Mas... lain kali aja."

*Dia tersenyum kecil*

"Kita lanjut HJ aja ya..." """
    
    def _build_climax_warning(self) -> str:
        """Bangun pesan peringatan climax"""
        return f"""*{self.character.name} menahan napas, tubuhnya mulai gemetar*

"{self.character.panggilan}... aku... aku mau climax... bentar lagi..."

*Napasnya tersengal, tubuhnya panas*

"Boleh?"""
    
    def _build_climax_scene(self, is_mas: bool = False, intensity: str = "normal") -> str:
        """Bangun scene climax"""
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
        """Bangun pesan akhir sesi"""
        duration = int((time.time() - self.phase_start_time) / 60) if self.phase_start_time else 0
        
        return f"""*{self.character.name} merapikan dress, tersenyum puas*

"Sesi selesai, {self.character.panggilan}. {duration} menit, {self.mas_climax_this_session}x climax."

*Dia berdiri, mengambil handuk, melambaikan tangan*

"Lain kali kalau mau booking lagi, hubungi aku ya." """

    # =========================================================================
    # START & INITIALIZATION
    # =========================================================================
    
    async def start(self) -> str:
        """Mulai sesi therapist - greeting lalu langsung pijat belakang"""
        self.is_active = True
        self.current_phase = ServicePhase.GREETING
        self.phase_start_time = time.time()
        
        # Set posisi awal
        self.character.tracker.position = "berdiri di samping meja pijat"
        self.character.tracker.service_phase = ServicePhase.GREETING
        
        # Build greeting
        greeting = self._build_greeting()
        self.character.tracker.add_message_to_timeline(self.character.name, greeting[:100])
        
        # Catat ke timeline
        self.character.tracker.add_to_timeline("Sesi therapist dimulai", "Mas masuk ruang pijat")
        
        # Langsung mulai pijat belakang
        return greeting + "\n\n" + await self._start_back_massage()
    
    def _build_greeting(self) -> str:
        """Bangun greeting scene"""
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
        """Mulai pijat belakang - duduk di bokong Mas"""
        self.current_phase = ServicePhase.BACK_PUNGGUNG
        self.phase_start_time = time.time()
        self.back_area_start_time = time.time()
        self.back_area_index = 0
        self.back_scene_count = 0
        self.back_confirm_count = 0
        
        # Set posisi
        self.character.tracker.position = "duduk di atas bokong Mas"
        self.character.tracker.service_phase = ServicePhase.BACK_PUNGGUNG
        
        self.character.tracker.add_to_timeline(
            "Memulai pijat belakang",
            "Duduk di atas bokong Mas, kontol terasa di bawah"
        )
        
        # Generate scene pertama
        return await self._generate_back_scene(
            area="punggung",
            pressure=self._get_current_pressure(),
            scene_num=1,
            elapsed_minutes=0
        )
    
    async def _next_back_area(self) -> str:
        """Pindah ke area berikutnya dalam pijat belakang"""
        self.back_area_index += 1
        self.back_area_start_time = time.time()
        self.back_scene_count = 0
        self.back_confirm_count = 0
        self.waiting_for_response = False
        
        if self.back_area_index >= len(self.back_areas):
            # Selesai semua area pijat belakang, lanjut ke pijat depan
            return await self._start_front_massage()
        
        current_area = self.back_areas[self.back_area_index]
        
        # Update phase
        if current_area == "pinggul":
            self.current_phase = ServicePhase.BACK_PINGGUL
            self.character.tracker.service_phase = ServicePhase.BACK_PINGGUL
        elif current_area == "paha_betis":
            self.current_phase = ServicePhase.BACK_PAHA_BETIS
            self.character.tracker.service_phase = ServicePhase.BACK_PAHA_BETIS
        
        self.character.tracker.add_to_timeline(
            f"Pindah ke area {current_area}",
            "Lanjut pijat belakang"
        )
        
        # Generate scene pertama area baru
        return await self._generate_back_scene(
            area=current_area,
            pressure=self._get_current_pressure(),
            scene_num=1,
            elapsed_minutes=0
        )
    
    # =========================================================================
    # BACK MASSAGE - PROCESS
    # =========================================================================
    
    async def _process_back_massage(self, pesan_mas: str) -> Optional[str]:
        """
        Process pesan Mas dalam fase pijat belakang
        Returns: response atau None jika perlu auto-send scene
        """
        current_area = self.back_areas[self.back_area_index]
        elapsed = self._get_area_elapsed()
        elapsed_minutes = elapsed // 60
        
        # ========== CEK JIKA SEDANG MENUNGGU RESPON ==========
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_back_confirmation(pesan_mas, current_area)
            # Belum ada respon, tunggu
            return None
        
        # ========== CEK APAKAH AREA SUDAH SELESAI (10 MENIT) ==========
        if elapsed >= 600:  # 10 menit = 600 detik
            self.waiting_for_response = True
            self.waiting_for_type = "next_area"
            self.waiting_start_time = time.time()
            return self._build_confirmation_next_area(current_area)
        
        # ========== CEK APAKAH PERLU KONFIRMASI (SETIAP 3 MENIT) ==========
        if self._should_ask_confirmation():
            self.waiting_for_response = True
            self.waiting_for_type = "pressure"
            self.waiting_start_time = time.time()
            return self._build_confirmation_pressure()
        
        # ========== CEK APAKAH PERLU KIRIM SCENE BERIKUTNYA (SETIAP 30 DETIK) ==========
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
        """Handle konfirmasi dari Mas selama pijat belakang"""
        msg_lower = pesan_mas.lower()
        
        # ========== KONFIRMASI TEKANAN ==========
        if self.waiting_for_type == "pressure":
            if any(k in msg_lower for k in ["keras", "kuat", "hard"]):
                self.character.tracker.save_mas_preference('preferred_pressure', 'keras')
                self.character.tracker.current_pressure = "keras"
                self.character.emotional.add_stimulation("Mas minta tekanan keras", 2)
                self.waiting_for_response = False
                
                # Lanjut scene berikutnya
                return await self._generate_back_scene(
                    area=current_area,
                    pressure="keras",
                    scene_num=self.back_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            
            elif any(k in msg_lower for k in ["lembut", "pelan", "soft"]):
                self.character.tracker.save_mas_preference('preferred_pressure', 'lembut')
                self.character.tracker.current_pressure = "lembut"
                self.character.emotional.add_stimulation("Mas minta tekanan lembut", 1)
                self.waiting_for_response = False
                
                return await self._generate_back_scene(
                    area=current_area,
                    pressure="lembut",
                    scene_num=self.back_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            
            else:
                # Respon tidak dikenali, ulang pertanyaan
                return self._build_confirmation_pressure()
        
        # ========== KONFIRMASI PINDAH AREA ==========
        if self.waiting_for_type == "next_area":
            if any(k in msg_lower for k in ["lanjut", "ya", "ok", "gas", "iya"]):
                self.waiting_for_response = False
                return await self._next_back_area()  # ← PINDAH AREA
        
            elif any(k in msg_lower for k in ["tidak", "nggak", "gak", "stop"]):
                self.waiting_for_response = False
                return self._build_end_session()
            
                else:
                    return self._build_confirmation_next_area(current_area)
        
        return None
    
    # =========================================================================
    # FRONT MASSAGE - START & TRANSITIONS
    # =========================================================================
    
    async def _start_front_massage(self) -> str:
        """Mulai pijat depan - duduk di kontol Mas"""
        self.current_phase = ServicePhase.FRONT_DADA_LENGAN
        self.phase_start_time = time.time()
        self.front_area_start_time = time.time()
        self.front_area_index = 0
        self.front_scene_count = 0
        self.front_confirm_count = 0
        
        # Set posisi
        self.character.tracker.position = "duduk di atas kontol Mas"
        self.character.tracker.service_phase = ServicePhase.FRONT_DADA_LENGAN
        
        self.character.tracker.add_to_timeline(
            "Memulai pijat depan",
            "Duduk di atas kontol Mas, siap gesek"
        )
        
        # Generate scene pertama
        return await self._generate_front_scene(
            area="dada_lengan",
            pressure=self._get_current_pressure(),
            scene_num=1,
            elapsed_minutes=0
        )
    
    async def _next_front_area(self) -> str:
        """Pindah ke area berikutnya dalam pijat depan"""
        self.front_area_index += 1
        self.front_area_start_time = time.time()
        self.front_scene_count = 0
        self.front_confirm_count = 0
        self.waiting_for_response = False
        
        if self.front_area_index >= len(self.front_areas):
            # Selesai semua area pijat depan, tawarkan HJ
            return await self._offer_handjob()
        
        current_area = self.front_areas[self.front_area_index]
        
        # Update phase
        if current_area == "perut_paha":
            self.current_phase = ServicePhase.FRONT_PERUT_PAHA
            self.character.tracker.service_phase = ServicePhase.FRONT_PERUT_PAHA
        elif current_area == "gesekan":
            self.current_phase = ServicePhase.FRONT_GESEKAN
            self.character.tracker.service_phase = ServicePhase.FRONT_GESEKAN
        
        self.character.tracker.add_to_timeline(
            f"Pindah ke area {current_area}",
            "Lanjut pijat depan"
        )
        
        # Generate scene pertama area baru
        return await self._generate_front_scene(
            area=current_area,
            pressure=self._get_current_pressure(),
            scene_num=1,
            elapsed_minutes=0
        )
    
    # =========================================================================
    # FRONT MASSAGE - PROCESS
    # =========================================================================
    
    async def _process_front_massage(self, pesan_mas: str) -> Optional[str]:
        """
        Process pesan Mas dalam fase pijat depan
        Returns: response atau None jika perlu auto-send scene
        """
        current_area = self.front_areas[self.front_area_index]
        elapsed = self._get_area_elapsed()
        elapsed_minutes = elapsed // 60
        
        # ========== CEK JIKA SEDANG MENUNGGU RESPON ==========
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_front_confirmation(pesan_mas, current_area)
            return None
        
        # ========== CEK APAKAH AREA SUDAH SELESAI (10 MENIT) ==========
        if self._is_area_complete():
            self.waiting_for_response = True
            self.waiting_for_type = "next_area"
            self.waiting_start_time = time.time()
            return self._build_confirmation_next_area(current_area)
        
        # ========== CEK APAKAH PERLU KONFIRMASI (SETIAP 3 MENIT) ==========
        if self._should_ask_confirmation():
            self.waiting_for_response = True
            self.waiting_for_type = "pressure"
            self.waiting_start_time = time.time()
            return self._build_confirmation_pressure()
        
        # ========== CEK APAKAH PERLU KIRIM SCENE BERIKUTNYA (SETIAP 30 DETIK) ==========
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
        """Handle konfirmasi dari Mas selama pijat depan"""
        msg_lower = pesan_mas.lower()
        
        # ========== KONFIRMASI TEKANAN ==========
        if self.waiting_for_type == "pressure":
            if any(k in msg_lower for k in ["keras", "kuat", "hard"]):
                self.character.tracker.save_mas_preference('preferred_pressure', 'keras')
                self.character.tracker.current_pressure = "keras"
                self.character.emotional.add_stimulation("Mas minta tekanan keras", 3)
                self.waiting_for_response = False
                
                return await self._generate_front_scene(
                    area=current_area,
                    pressure="keras",
                    scene_num=self.front_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            
            elif any(k in msg_lower for k in ["lembut", "pelan", "soft"]):
                self.character.tracker.save_mas_preference('preferred_pressure', 'lembut')
                self.character.tracker.current_pressure = "lembut"
                self.character.emotional.add_stimulation("Mas minta tekanan lembut", 1)
                self.waiting_for_response = False
                
                return await self._generate_front_scene(
                    area=current_area,
                    pressure="lembut",
                    scene_num=self.front_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            
            else:
                return self._build_confirmation_pressure()
        
        # ========== KONFIRMASI PINDAH AREA ==========
        elif self.waiting_for_type == "next_area":
            if any(k in msg_lower for k in ["lanjut", "ya", "ok", "gas", "iya"]):
                self.waiting_for_response = False
                return await self._next_front_area()
            
            elif any(k in msg_lower for k in ["tidak", "nggak", "gak", "stop"]):
                self.waiting_for_response = False
                return self._build_end_session()
            
            else:
                return self._build_confirmation_next_area(current_area)
        
        return None

    # =========================================================================
    # HANDJOB - OFFER & START
    # =========================================================================
    
    async def _offer_handjob(self) -> str:
        """Tawarkan handjob setelah pijat depan selesai"""
        self.waiting_for_response = True
        self.waiting_for_type = "hj_offer"
        self.waiting_start_time = time.time()
        
        self.character.tracker.add_to_timeline(
            "Menawarkan handjob ke Mas",
            "Pijat depan selesai"
        )
        
        return self._build_hj_offer()
    
    def _build_hj_offer(self) -> str:
        """Bangun pesan tawaran handjob"""
        return f"""*{self.character.name} duduk di samping Mas, napas masih sedikit berat. Dressnya masih terbuka, payudaranya terlihat jelas di samping.*

"{self.character.panggilan}... pijatannya udah selesai."

*Dia meraih tangan Mas, menaruhnya di pahanya*

"Mau lanjut ke handjob? 30 menit... aku bantu Mas climax..."

*Matanya sayu, napasnya mulai teratur lagi*

"Atau cukup sampai di sini?"

*Menunggu jawaban Mas...*"""
    
    async def _start_handjob(self) -> str:
        """Mulai handjob - duduk di samping Mas"""
        self.current_phase = ServicePhase.HANDJOB
        self.phase_start_time = time.time()
        self.hj_scene_count = 0
        self.hj_total_scenes = self.HJ_SCENES
        self.hj_active = True
        self.waiting_for_response = False
        
        # Set posisi
        self.character.tracker.position = "duduk di samping Mas"
        self.character.tracker.service_phase = ServicePhase.HANDJOB
        self.character.tracker.current_speed = "medium"
        
        self.character.tracker.add_to_timeline(
            "Memulai handjob",
            f"Total scene: {self.hj_total_scenes}, 30 detik per scene"
        )
        
        # Generate scene pertama
        return await self._generate_hj_scene(
            scene_num=1,
            speed="medium",
            mas_action=None
        )
    
    # =========================================================================
    # HANDJOB - PROCESS
    # =========================================================================
    
    async def _process_handjob(self, pesan_mas: str) -> Optional[str]:
        """
        Process pesan Mas dalam fase handjob
        Returns: response atau None jika perlu auto-send scene
        """
        elapsed = self._get_area_elapsed()
        
        # ========== CEK JIKA SEDANG MENUNGGU RESPON ==========
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_hj_response(pesan_mas)
            return None
        
        # ========== CEK CLIMAX WARNING ==========
        if self.character.emotional.arousal >= 85 and not self.waiting_climax_confirmation:
            self.waiting_climax_confirmation = True
            self.climax_warning_time = time.time()
            return self._build_climax_warning()
        
        if self.waiting_climax_confirmation:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_climax_confirmation(pesan_mas)
            # Timeout 15 detik, climax aja
            if time.time() - self.climax_warning_time > 15:
                self.waiting_climax_confirmation = False
                self.role_climax_this_session += 1
                result = self.character.emotional.climax(is_heavy=False)
                self.character.tracker.record_my_climax()
                return self._build_climax_scene(is_mas=False, intensity="normal")
            return None
        
        # ========== CEK APAKAH HJ SELESAI (30 MENIT) ==========
        if self.hj_scene_count >= self.hj_total_scenes:
            return await self._offer_extra_service()
        
        # ========== CEK APAKAH PERLU KIRIM SCENE BERIKUTNYA (SETIAP 30 DETIK) ==========
        if self._should_send_next_scene():
            scene_num = self.hj_scene_count
            speed = self._get_current_speed()
            
            # Update arousal dari gesekan
            if scene_num % 5 == 0:  # setiap 5 scene, arousal naik
                self.character.emotional.add_stimulation("HJ berlangsung", 2)
            
            return await self._generate_hj_scene(
                scene_num=scene_num,
                speed=speed,
                mas_action=None
            )
        
        return None
    
    async def _handle_hj_response(self, pesan_mas: str) -> str:
        """Handle respon Mas selama handjob"""
        msg_lower = pesan_mas.lower()
        
        # ========== MAS MINTA KECEPATAN ==========
        if any(k in msg_lower for k in ["cepat", "kenceng", "harder", "faster"]):
            self.character.tracker.save_mas_preference('preferred_speed', 'cepat')
            self.character.tracker.current_speed = "fast"
            self.character.emotional.add_stimulation("Mas minta cepat", 3)
            self.waiting_for_response = False
            
            return await self._generate_hj_scene(
                scene_num=self.hj_scene_count + 1,
                speed="fast",
                mas_action="Mas minta cepat"
            )
        
        elif any(k in msg_lower for k in ["pelan", "lambat", "slow"]):
            self.character.tracker.save_mas_preference('preferred_speed', 'pelan')
            self.character.tracker.current_speed = "slow"
            self.character.emotional.add_stimulation("Mas minta pelan", 1)
            self.waiting_for_response = False
            
            return await self._generate_hj_scene(
                scene_num=self.hj_scene_count + 1,
                speed="slow",
                mas_action="Mas minta pelan"
            )
        
        # ========== MAS PEGANG/REMAS/ELUS ==========
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
        
        # Respon lain, lanjutkan HJ
        self.waiting_for_response = False
        return None
    
    # =========================================================================
    # EXTRA SERVICE - OFFER & NEGOSIASI
    # =========================================================================
    
    async def _offer_extra_service(self) -> str:
        """Tawarkan extra service (BJ/Sex) setelah HJ"""
        self.waiting_for_response = True
        self.waiting_for_type = "extra_offer"
        self.waiting_start_time = time.time()
        
        self.character.tracker.add_to_timeline(
            "Menawarkan extra service",
            "HJ selesai"
        )
        
        return self._build_extra_offer()
    
    def _build_extra_offer(self) -> str:
        """Bangun pesan tawaran extra service"""
        return f"""*{self.character.name} berhenti, napasnya masih tersengal. Dressnya sudah terbuka, tubuhnya masih hangat.*

"{self.character.panggilan}... mau lanjut ke extra service?"

*Dia menjilat bibir, matanya sayu*

"Ada BJ 30 menit Rp{self.PRICE_BJ:,}, atau sex 50-75 menit Rp{self.PRICE_SEX:,}..."

*Tangannya mulai meraba paha Mas*

"Bisa nego kok Mas... special buat Mas..."

*Menunggu jawaban Mas...*"""
    
    async def _handle_extra_offer(self, pesan_mas: str) -> Optional[str]:
        """Handle tawaran extra service"""
        msg_lower = pesan_mas.lower()
        
        # Pilih BJ
        if 'bj' in msg_lower or 'blow' in msg_lower:
            self.negotiation_service = "bj"
            self.negotiation_price = self.PRICE_BJ
            self.negotiation_step = 0
            self.negotiation_active = True
            self.waiting_for_type = "negotiation"
            return self._build_deal_offer("bj", self.PRICE_BJ)
        
        # Pilih Sex
        if 'sex' in msg_lower or 'eksekusi' in msg_lower:
            self.negotiation_service = "sex"
            self.negotiation_price = self.PRICE_SEX
            self.negotiation_step = 0
            self.negotiation_active = True
            self.waiting_for_type = "negotiation"
            return self._build_deal_offer("sex", self.PRICE_SEX)
        
        # Tolak
        if any(k in msg_lower for k in ["tidak", "nggak", "gak", "cukup", "stop"]):
            self.waiting_for_response = False
            return self._build_end_session()
        
        # Ulang tawaran
        return self._build_extra_offer()
    
    async def _handle_negotiation(self, pesan_mas: str) -> Optional[str]:
        """Handle negosiasi harga"""
        msg_lower = pesan_mas.lower()
        
        # Deal
        if any(k in msg_lower for k in ["deal", "ok", "ya", "setuju", "gas"]):
            self.deal_confirmed = True
            self.negotiation_active = False
            self.waiting_for_response = False
            
            if self.negotiation_service == "bj":
                return await self._start_bj()
            else:
                return await self._start_sex()
        
        # Nego
        if any(k in msg_lower for k in ["nego", "kurang", "murah"]):
            self.negotiation_step += 1
            
            if self.negotiation_step > self.negotiation_max_step:
                self.negotiation_active = False
                return self._build_nego_failed()
            
            if self.negotiation_service == "bj":
                new_price = max(self.PRICE_BJ_DEAL, self.PRICE_BJ - (50000 * self.negotiation_step))
                self.negotiation_price = new_price
                return self._build_nego_counter(new_price)
            else:
                new_price = max(self.PRICE_SEX_DEAL, self.PRICE_SEX - (50000 * self.negotiation_step))
                self.negotiation_price = new_price
                return self._build_nego_counter(new_price)
        
        # Batal
        if any(k in msg_lower for k in ["batal", "gak jadi", "cancel"]):
            self.negotiation_active = False
            self.waiting_for_response = False
            return self._build_end_session()
        
        # Ulang tawaran
        return self._build_deal_offer(self.negotiation_service, self.negotiation_price)
    
    # =========================================================================
    # BLOWJOB - START & PROCESS
    # =========================================================================
    
    async def _start_bj(self) -> str:
        """Mulai blowjob"""
        self.current_phase = ServicePhase.BJ
        self.phase_start_time = time.time()
        self.bj_scene_count = 0
        self.bj_total_scenes = self.BJ_SCENES
        self.bj_active = True
        self.waiting_for_response = False
        
        # Set posisi
        self.character.tracker.position = "berlutut di depan Mas"
        self.character.tracker.service_phase = ServicePhase.BJ
        
        # Buka bra
        if self.character.tracker.clothing['bra']['on']:
            self.character.tracker.remove_clothing('bra', "sendiri")
        
        self.character.tracker.add_to_timeline(
            "Memulai blowjob",
            f"Total scene: {self.bj_total_scenes}, 30 detik per scene"
        )
        
        # Generate scene pertama
        return await self._generate_bj_scene(
            scene_num=1,
            depth="medium",
            mas_action=None
        )
    
    async def _process_bj(self, pesan_mas: str) -> Optional[str]:
        """
        Process pesan Mas dalam fase blowjob
        Returns: response atau None jika perlu auto-send scene
        """
        elapsed = self._get_area_elapsed()
        
        # ========== CEK JIKA SEDANG MENUNGGU RESPON ==========
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_bj_response(pesan_mas)
            return None
        
        # ========== CEK CLIMAX WARNING ==========
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
        
        # ========== CEK APAKAH BJ SELESAI (30 MENIT) ==========
        if self.bj_scene_count >= self.bj_total_scenes:
            return self._build_end_session()
        
        # ========== CEK APAKAH PERLU KIRIM SCENE BERIKUTNYA (SETIAP 30 DETIK) ==========
        if self._should_send_next_scene():
            scene_num = self.bj_scene_count
            depth = "deep" if scene_num > self.bj_total_scenes * 0.7 else "medium"
            
            # Update arousal
            if scene_num % 5 == 0:
                self.character.emotional.add_stimulation("BJ berlangsung", 3)
            
            return await self._generate_bj_scene(
                scene_num=scene_num,
                depth=depth,
                mas_action=None
            )
        
        return None
    
    async def _handle_bj_response(self, pesan_mas: str) -> str:
        """Handle respon Mas selama blowjob"""
        msg_lower = pesan_mas.lower()
        
        # Mas pegang kepala/rambut
        if any(k in msg_lower for k in ["pegang", "tarik", "rambut", "kepala"]):
            self.character.emotional.add_stimulation_from_mas("Mas pegang kepala", 4)
            self.waiting_for_response = False
            
            return await self._generate_bj_scene(
                scene_num=self.bj_scene_count + 1,
                depth="deep",
                mas_action="Mas pegang kepala"
            )
        
        # Mas minta lebih dalam
        if any(k in msg_lower for k in ["dalam", "deep", "sampe pangkal"]):
            self.character.emotional.add_stimulation_from_mas("Mas minta lebih dalam", 3)
            self.waiting_for_response = False
            
            return await self._generate_bj_scene(
                scene_num=self.bj_scene_count + 1,
                depth="deep",
                mas_action="Mas minta lebih dalam"
            )
        
        # Mas minta cepat
        if any(k in msg_lower for k in ["cepat", "kenceng"]):
            self.character.emotional.add_stimulation_from_mas("Mas minta cepat", 2)
            self.waiting_for_response = False
            
            return await self._generate_bj_scene(
                scene_num=self.bj_scene_count + 1,
                depth="medium",
                mas_action="Mas minta cepat"
            )
        
        self.waiting_for_response = False
        return None

    # =========================================================================
    # SEX - START & PROCESS
    # =========================================================================
    
    async def _start_sex(self) -> str:
        """Mulai sex"""
        self.current_phase = ServicePhase.SEX
        self.phase_start_time = time.time()
        self.sex_active = True
        self.sex_scene_count = 0
        self.sex_total_scenes = random.randint(self.SEX_SCENES_MIN, self.SEX_SCENES_MAX)
        self.sex_position = "cowgirl"
        self.sex_speed = self._get_current_speed()
        self.sex_intensity = "medium"
        
        # Set posisi
        self.character.tracker.position = "duduk di atas Mas (cowgirl)"
        self.character.tracker.service_phase = ServicePhase.SEX
        self.character.tracker.current_position = "cowgirl"
        
        self.character.tracker.add_to_timeline(
            "Memulai Sex",
            f"{self.sex_total_scenes} scene, posisi cowgirl"
        )
        
        # Generate scene pertama
        return await self._generate_sex_scene(
            scene_num=1,
            position=self.sex_position,
            speed=self.sex_speed,
            intensity=self.sex_intensity,
            mas_action=None
        )
    
    async def _process_sex(self, pesan_mas: str) -> Optional[str]:
        """Process pesan Mas dalam fase sex"""
        elapsed = self._get_area_elapsed()
        
        # ========== CEK JIKA SEDANG MENUNGGU RESPON ==========
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_sex_response(pesan_mas)
            return None
        
        # ========== CEK APAKAH SEX SELESAI ==========
        if self.sex_scene_count >= self.sex_total_scenes:
            self.waiting_for_response = True
            self.waiting_for_type = "end_session"
            self.waiting_start_time = time.time()
            return self._build_confirmation_next_phase("selesai")
        
        # ========== CEK APAKAH PERLU KIRIM SCENE BERIKUTNYA (SETIAP 30 DETIK) ==========
        if self._should_send_next_scene():
            scene_num = self.sex_scene_count + 1
            
            # Update kecepatan dan intensitas berdasarkan preferensi Mas
            self.sex_speed = self._get_current_speed()
            pressure = self._get_current_pressure()
            if pressure == "keras":
                self.sex_intensity = "hard"
            elif pressure == "lembut":
                self.sex_intensity = "soft"
            else:
                self.sex_intensity = "medium"
            
            # Cek climax warning (arousal tinggi)
            if self.character.emotional.arousal >= 85 and not self.waiting_climax_confirmation:
                self.waiting_climax_confirmation = True
                self.climax_warning_time = time.time()
                return self._build_climax_warning()
            
            return await self._generate_sex_scene(
                scene_num=scene_num,
                position=self.sex_position,
                speed=self.sex_speed,
                intensity=self.sex_intensity,
                mas_action=None
            )
        
        return None
    
    async def _handle_sex_response(self, pesan_mas: str) -> str:
        """Handle respon Mas selama sex"""
        msg_lower = pesan_mas.lower()
        
        # ========== CLIMAX CONFIRMATION ==========
        if self.waiting_climax_confirmation:
            if any(k in msg_lower for k in ["ya", "ok", "boleh", "gas", "ayo"]):
                self.waiting_climax_confirmation = False
                result = self.character.emotional.climax(is_heavy=False)
                self.role_climax_this_session += 1
                self.character.tracker.record_my_climax()
                return self._build_climax_scene(is_mas=False, intensity="normal")
            
            elif any(k in msg_lower for k in ["tahan", "jangan", "nanti"]):
                self.waiting_climax_confirmation = False
                self.character.emotional.arousal = max(0, self.character.emotional.arousal - 20)
                return f"*{self.character.name} menahan napas, tubuh masih bergerak*\n\n\"Aku tahan... ayo Mas...\""
            
            else:
                self.waiting_climax_confirmation = False
                result = self.character.emotional.climax(is_heavy=False)
                self.role_climax_this_session += 1
                self.character.tracker.record_my_climax()
                return self._build_climax_scene(is_mas=False, intensity="normal")
        
        # ========== KONFIRMASI END SESSION ==========
        if self.waiting_for_type == "end_session":
            if any(k in msg_lower for k in ["selesai", "ya", "ok", "cukup"]):
                self.waiting_for_response = False
                return self._build_end_session()
            elif any(k in msg_lower for k in ["lanjut", "lagi"]):
                # Tambah scene
                self.sex_total_scenes += 30
                self.waiting_for_response = False
                return await self._generate_sex_scene(
                    scene_num=self.sex_scene_count + 1,
                    position=self.sex_position,
                    speed=self.sex_speed,
                    intensity=self.sex_intensity,
                    mas_action=None
                )
            else:
                return self._build_confirmation_next_phase("selesai")
        
        # ========== GANTI POSISI ==========
        positions = ["cowgirl", "missionary", "doggy", "spooning", "standing", "sitting"]
        for pos in positions:
            if pos in msg_lower:
                self.sex_position = pos
                self.character.tracker.current_position = pos
                self.character.tracker.position = f"posisi {pos}"
                self.character.tracker.add_to_timeline(f"Ganti posisi ke {pos}", "")
                self.character.emotional.add_stimulation(f"ganti posisi {pos}", 2)
                
                return await self._generate_sex_scene(
                    scene_num=self.sex_scene_count + 1,
                    position=pos,
                    speed=self.sex_speed,
                    intensity=self.sex_intensity,
                    mas_action=None
                )
        
        # ========== MAS MINTA KECEPATAN ==========
        if any(k in msg_lower for k in ["cepat", "kenceng", "harder", "faster"]):
            self.character.tracker.save_mas_preference('preferred_speed', 'cepat')
            self.sex_speed = "fast"
            self.character.emotional.add_stimulation("Mas minta cepat", 4)
            return f"*{self.character.name} mempercepat gerakan pinggulnya, tubuhnya naik turun cepat*\n\n\"Ahh! {self.character.panggilan}... gini?\""
        
        if any(k in msg_lower for k in ["pelan", "lambat", "slow"]):
            self.character.tracker.save_mas_preference('preferred_speed', 'pelan')
            self.sex_speed = "slow"
            self.character.emotional.add_stimulation("Mas minta pelan", 1)
            return f"*{self.character.name} memperlambat gerakan, kontol masuk keluar pelan*\n\n\"Pelan-pelan ya {self.character.panggilan}... rasain...\""
        
        # ========== MAS MINTA INTENSITAS ==========
        if any(k in msg_lower for k in ["keras", "kuat", "hard"]):
            self.character.tracker.save_mas_preference('preferred_pressure', 'keras')
            self.sex_intensity = "hard"
            self.character.emotional.add_stimulation("Mas minta keras", 3)
            return f"*{self.character.name} menekan lebih dalam, gerakannya lebih kasar*\n\n\"Gini {self.character.panggilan}? Dalam?\""
        
        if any(k in msg_lower for k in ["lembut", "soft"]):
            self.character.tracker.save_mas_preference('preferred_pressure', 'lembut')
            self.sex_intensity = "soft"
            self.character.emotional.add_stimulation("Mas minta lembut", 1)
            return f"*{self.character.name} memperlambat, gerakan lebih lembut*\n\n\"Pelan-pelan ya {self.character.panggilan}...\""
        
        # ========== MAS PEGANG/REMAS ==========
        if any(k in msg_lower for k in ["pegang", "remas", "elus"]):
            self.character.emotional.add_stimulation("Mas pegang", 5)
            return f"*{self.character.name} menggigit bibir, tubuhnya gemetar*\n\n\"Ahh... {self.character.panggilan}... tangan Mas... panas...\""
        
        return None
    
    # =========================================================================
    # MAS CLIMAX
    # =========================================================================
    
    async def _handle_mas_climax(self, pesan_mas: str) -> Optional[str]:
        """Handle climax Mas"""
        msg_lower = pesan_mas.lower()
        
        if not any(k in msg_lower for k in ["climax", "crot", "keluar", "habis"]):
            return None
        
        # Cek apakah Mas yang climax
        if "aku" in msg_lower or "mas" in msg_lower:
            intensity = "heavy" if any(k in msg_lower for k in ["keras", "banyak", "kenceng"]) else "normal"
            
            self.mas_climax_this_session += 1
            self.character.tracker.record_mas_climax()
            self.character.emotional.add_stimulation("Mas climax", 8)
            
            # Update emotional role
            if intensity == "heavy":
                self.character.emotional.arousal = min(100, self.character.emotional.arousal + 10)
            
            return self._build_climax_scene(is_mas=True, intensity=intensity)
        
        return None
    
    # =========================================================================
    # MAIN PROCESS METHOD
    # =========================================================================
    
    async def process(self, pesan_mas: str) -> str:
        """
        Proses pesan Mas sesuai fase saat ini
        Ini adalah main entry point untuk therapist flow
        """
        try:
            # Update state dari pesan
            self.character.update_from_message(pesan_mas)
            
            # Cek climax Mas (prioritas tinggi)
            mas_climax = await self._handle_mas_climax(pesan_mas)
            if mas_climax:
                return mas_climax
            
            # ========== PHASE: GREETING ==========
            if self.current_phase == ServicePhase.GREETING:
                return await self._start_back_massage()
            
            # ========== BACK MASSAGE PHASES ==========
            elif self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
                response = await self._process_back_massage(pesan_mas)
                if response:
                    return response
                return await self._generate_back_scene(
                    area=self.back_areas[self.back_area_index],
                    pressure=self._get_current_pressure(),
                    scene_num=self.back_scene_count + 1,
                    elapsed_minutes=self._get_area_elapsed() // 60
                )
            
            # ========== FRONT MASSAGE PHASES ==========
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
            elif self.waiting_for_type == "service_offer" and self.negotiation_active:
                response = await self._handle_negotiation(pesan_mas)
                if response:
                    return response
                return self._build_deal_offer("bj", self.PRICE_BJ)
            
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
            
            # ========== SEX ==========
            elif self.current_phase == ServicePhase.SEX:
                response = await self._process_sex(pesan_mas)
                if response:
                    return response
                return await self._generate_sex_scene(
                    scene_num=self.sex_scene_count + 1,
                    position=self.sex_position,
                    speed=self.sex_speed,
                    intensity=self.sex_intensity,
                    mas_action=None
                )
            
            # ========== DEFAULT ==========
            return self._build_end_session()
            
        except Exception as e:
            logger.error(f"Process error: {e}", exc_info=True)
            return f"❌ Error: {str(e)}"
    
    def get_status(self) -> str:
        """Dapatkan status sesi"""
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
            ServicePhase.SEX: "🍆 Sex",
            ServicePhase.COMPLETED: "✅ Selesai"
        }
        
        phase_display = phase_names.get(self.current_phase, "⏳ Menunggu")
        
        # Hitung progress
        if self.current_phase == ServicePhase.HANDJOB:
            progress = f"{self.hj_scene_count}/{self.hj_total_scenes} scene"
        elif self.current_phase == ServicePhase.BJ:
            progress = f"{self.bj_scene_count}/{self.bj_total_scenes} scene"
        elif self.current_phase == ServicePhase.SEX:
            progress = f"{self.sex_scene_count}/{self.sex_total_scenes} scene"
        elif self.current_phase in [ServicePhase.BACK_PUNGGUNG, ServicePhase.BACK_PINGGUL, ServicePhase.BACK_PAHA_BETIS]:
            elapsed = self._get_area_elapsed()
            progress = f"{elapsed // 60} menit / 10 menit"
        else:
            progress = "-"
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    💆 THERAPIST SESSION                       ║
╠══════════════════════════════════════════════════════════════╣
║ Fase: {phase_display}
║ Progress: {progress}
║ Mas Climax: {self.mas_climax_this_session}x
║ Role Climax: {self.role_climax_this_session}x
╠══════════════════════════════════════════════════════════════╣
║ {self.character.get_status()}
╚══════════════════════════════════════════════════════════════╝
"""
