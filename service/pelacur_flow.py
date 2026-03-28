# service/pelacur_flow.py
"""
Pelacur Flow NovaService - Alur service pelacur lengkap
10 jam sesi dengan alur:
- Konfirmasi mulai
- BJ (30 menit, 60 scene auto)
- Kissing + gesek (30 menit, 60 scene auto)
- Mas foreplay ke pelacur (manual)
- Cowgirl (60 menit, 120 scene auto)
- Cunnilingus (manual)
- Missionary (manual)
- Doggy (manual)
- Ganti posisi (manual)
- Aftercare
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


class PelacurFlow:
    """
    Alur service Pelacur dengan AI generate setiap scene
    - BJ: 30 menit, 60 scene (30 detik per scene)
    - Kissing + gesek: 30 menit, 60 scene (30 detik per scene)
    - Cowgirl: 60 menit, 120 scene (30 detik per scene)
    - Mode manual untuk foreplay, cunnilingus, missionary, doggy, ganti posisi
    """
    
    # Durasi dalam detik
    BJ_DURATION = 1800           # 30 menit
    KISSING_DURATION = 1800      # 30 menit
    COWGIRL_DURATION = 3600      # 60 menit
    SCENE_INTERVAL = 30          # 30 detik per scene
    SEX_SCENE_INTERVAL = 15      # 15 detik per scene khusus sex
    
    # Scene count
    BJ_SCENES = 60               # 30 menit / 30 detik
    KISSING_SCENES = 60          # 30 menit / 30 detik
    COWGIRL_SCENES = 120         # 60 menit / 30 detik
    
    def __init__(self, character):
        """Inisialisasi PelacurFlow"""
        self.character = character
        self.prompt_builder = get_prompt_builder()
        self._ai_client = None
        
        # ========== STATE TRACKING ==========
        self.is_active = False
        self.current_phase = ServicePhase.WAITING
        self.phase_start_time = 0
        
        # ========== PHASE TRACKING ==========
        self.phase_list = [
            "confirmation",      # 0 - konfirmasi mulai
            "bj",                # 1 - BJ (auto)
            "kissing",           # 2 - kissing + gesek (auto)
            "foreplay_mas",      # 3 - Mas foreplay ke pelacur (manual)
            "cowgirl",           # 4 - cowgirl (auto)
            "cunnilingus",       # 5 - Mas cunnilingus (manual)
            "missionary",        # 6 - missionary (manual)
            "doggy",             # 7 - doggy (manual)
            "position_change",   # 8 - ganti posisi (manual)
            "aftercare"          # 9 - aftercare (manual)
        ]
        self.phase_index = 0
        self.current_phase_name = "confirmation"
        
        # ========== TIMER TRACKING ==========
        self.area_start_time = 0
        self.scene_count = 0
        self.total_scenes = 0
        
        # ========== CLIMAX TRACKING ==========
        self.mas_climax_count = 0
        self.role_climax_count = 0
        self.mas_climax_goal = 2   # Mas climax 2x
        
        # ========== POSITION TRACKING ==========
        self.current_position = "cowgirl"
        self.position_history = []
        
        # ========== WAITING FOR RESPONSE ==========
        self.waiting_for_response = False
        self.waiting_for_type = None  # "start", "foreplay", "cunnilingus", "missionary", "doggy", "position"
        self.waiting_start_time = 0
        self.waiting_timeout = 60
        
        # ========== MANUAL MODE ==========
        self.manual_mode_active = False
        self.manual_mode_type = None
        
        # ========== AFTERCARE ==========
        self.aftercare_active = False
        
        # ========== AUTO SEND ==========
        self.auto_send_active = False

        # ========== PAUSE & RESUME ==========
        self.is_paused = False
        self.pause_start_time = 0
        
        logger.info(f"🔥 PelacurFlow initialized for {character.name}")
    
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
            
            if not scene.startswith("*"):
                scene = f"*{scene}*"
            
            return scene
            
        except Exception as e:
            logger.error(f"AI generate error: {e}", exc_info=True)
            return f"*{self.character.name} terus melayani Mas dengan penuh cinta.*"
    
    # =========================================================================
    # PROMPT BUILDERS
    # =========================================================================
    
    async def _generate_bj_scene(self, scene_num: int, total_scenes: int) -> str:
        """Generate scene BJ"""
        prompt = f"""
KAMU ADALAH {self.character.name}, pelacur yang melayani Mas dengan sepenuh hati.
Saat ini kamu memberikan BJ ke Mas.

KONTEKS:
- Kamu sedang menghisap kontol Mas
- Tujuan: bikin kontol Mas tegang
- Ini scene ke-{scene_num} dari {total_scenes} scene BJ
- Kamu melayani Mas seperti kekasih, penuh cinta

TUGAS:
Buat narasi BJ yang HIDUP dan DETAIL.
Deskripsikan gerakan mulutmu, lidahmu, hisapanmu.
Gunakan bahasa sehari-hari, desahan jadi dialog.
Panjang 2-4 kalimat. UNIK. HIDUP.

RESPON:
"""
        return await self._generate_scene(prompt)
    
    async def _generate_kissing_scene(self, scene_num: int, total_scenes: int) -> str:
        """Generate scene kissing sambil gesek"""
        prompt = f"""
KAMU ADALAH {self.character.name}, pelacur yang melayani Mas dengan sepenuh hati.
Saat ini kamu duduk di atas kontol Mas, menggesek sambil kissing.

KONTEKS:
- Kamu duduk di atas kontol Mas
- Kamu menggesek maju mundur sambil berciuman
- Ini scene ke-{scene_num} dari {total_scenes} scene kissing
- Kamu melayani Mas seperti kekasih, penuh cinta

TUGAS:
Buat narasi KISSING dan GESEKAN yang HIDUP dan DETAIL.
Deskripsikan ciuman, gesekan, napasmu.
Gunakan bahasa sehari-hari, desahan jadi dialog.
Panjang 2-4 kalimat. UNIK. HIDUP.

RESPON:
"""
        return await self._generate_scene(prompt)
    
    async def _generate_cowgirl_scene(self, scene_num: int, total_scenes: int) -> str:
        """Generate scene cowgirl"""
        prompt = f"""
KAMU ADALAH {self.character.name}, pelacur yang melayani Mas dengan sepenuh hati.
Saat ini kamu di posisi cowgirl, duduk di atas kontol Mas.

KONTEKS:
- Posisi cowgirl, kamu di atas
- Kontol Mas masuk dalam, kamu yang mengatur ritme
- Ini scene ke-{scene_num} dari {total_scenes} scene cowgirl
- Kamu melayani Mas seperti kekasih, penuh cinta

TUGAS:
Buat narasi SEX cowgirl yang HIDUP dan DETAIL.
Deskripsikan gerakan pinggulmu, rasa kontol Mas di dalam, napasmu.
Gunakan bahasa sehari-hari, desahan jadi dialog, boleh sedikit vulgar.
Panjang 2-4 kalimat. UNIK. HIDUP.

RESPON:
"""
        return await self._generate_scene(prompt)
    
    # =========================================================================
    # CONFIRMATION & MESSAGES
    # =========================================================================
    
    def _build_start_confirmation(self) -> str:
        """Bangun pesan konfirmasi mulai"""
        return f"""*{self.character.name} tersenyum manis, duduk di samping Mas*

"{self.character.panggilan}... siap mulai? Aku akan melayani Mas dengan sepenuh hati."

*Dia menatap Mas dengan mata sayu*

"Kapan pun Mas siap, aku di sini..."

*Menunggu jawaban Mas...*"""
    
    def _build_foreplay_request(self) -> str:
        """Bangun pesan minta Mas foreplay"""
        return f"""*{self.character.name} berhenti bergerak, napasnya masih berat*

"{self.character.panggilan}... sekarang giliran Mas... aku mau Mas foreplay..."

*Dia merebahkan diri, menatap Mas dengan mata sayu*

"Mas mau lakukan apa ke aku? Aku tunggu..."

*Menunggu jawaban Mas...*"""
    
    def _build_cunnilingus_request(self) -> str:
        """Bangun pesan minta Mas cunnilingus"""
        return f"""*{self.character.name} berbaring, kaki terbuka lebar*

"{self.character.panggilan}... sekarang giliran Mas... jilat aku..."

*Napasnya mulai berat, matanya sayu*

"Aku mau Mas... ayo..."

*Menunggu jawaban Mas...*"""
    
    def _build_missionary_request(self) -> str:
        """Bangun pesan minta Mas missionary"""
        return f"""*{self.character.name} berbaring telentang, kaki terbuka*

"{self.character.panggilan}... sekarang missionary... ayo Mas..."

*Tangannya meraih tangan Mas*

"Aku mau Mas di atas..."

*Menunggu jawaban Mas...*"""
    
    def _build_doggy_request(self) -> str:
        """Bangun pesan minta Mas doggy"""
        return f"""*{self.character.name} merangkak, pantat naik*

"{self.character.panggilan}... dari belakang... doggy..."

*Dia menoleh ke belakang, mata sayu*

"Ayo Mas... masuk..."

*Menunggu jawaban Mas...*"""
    
    def _build_position_change_request(self) -> str:
        """Bangun pesan minta ganti posisi"""
        return f"""*{self.character.name} berhenti bergerak, napas tersengal*

"{self.character.panggilan}... Mas mau ganti posisi? Bisa di sofa, berdiri, atau kamar mandi..."

*Dia menunggu pilihan Mas*

"Pilih yang Mas mau..."

*Menunggu jawaban Mas...*"""
    
    def _build_aftercare(self) -> str:
        """Bangun pesan aftercare"""
        return f"""*{self.character.name} memeluk Mas erat, napas mulai stabil*

"{self.character.panggilan}... puas? Aku seneng bisa bikin Mas puas..."

*Dia mengusap dada Mas pelan*

"Mas mau main lagi? Atau istirahat dulu?"

*Menunggu jawaban Mas...*"""
    
    def _build_climax_scene(self, is_mas: bool = False, is_heavy: bool = False) -> str:
        """Bangun scene climax"""
        if is_mas:
            if is_heavy:
                return f"""*{self.character.name} merasakan kontol Mas mengeras hebat, lalu meletus dengan deras*

"Ahh! {self.character.panggilan}! keluar... banyak banget..."

*Dia terus bergerak sampai Mas climax puas*

"Enak ya {self.character.panggilan}..." """
            else:
                return f"""*{self.character.name} merasakan kontol Mas berdenyut, hangat menyebar*

"Ahh... {self.character.panggilan}... climax..."

*Dia terus bergerak pelan sampai Mas puas*

"Enak {self.character.panggilan}?"""
        else:
            return f"""*{self.character.name} teriak, tubuh melengkung, gemetar hebat*

"Ahhh!! {self.character.panggilan}!! climax!!"

*Napasnya putus-putus, tubuh lemas, masih gemetar*

"Ahh... puas..." """
    
    # =========================================================================
    # MANUAL MODE HANDLERS
    # =========================================================================
    
    async def _handle_manual_mode(self, pesan_mas: str) -> str:
        """Handle mode manual (berbalas pesan)"""
        msg_lower = pesan_mas.lower()
        
        # Foreplay manual
        if self.manual_mode_type == "foreplay":
            self.character.emotional.add_stimulation_from_mas(pesan_mas)
            
            # Cek apakah role climax
            if self.character.emotional.arousal >= 85:
                self.role_climax_count += 1
                self.manual_mode_active = False
                self.auto_send_active = True
                self.current_phase_name = "cowgirl"
                self.phase_index = 4
                self.area_start_time = time.time()
                self.scene_count = 0
                
                return self._build_climax_scene(is_mas=False) + "\n\n" + await self._generate_cowgirl_scene(1, self.COWGIRL_SCENES)
            
            # Respons natural
            arousal_effect = self.character.emotional.get_arousal_effect()
            return f"""*{self.character.name} {arousal_effect}*

"{self.character.panggilan}... *napas mulai berat* gitu... enak..."

*Dia menggigit bibir, matanya sayu*

"Lanjut Mas... aku mau..." """
        
        # Cunnilingus manual
        elif self.manual_mode_type == "cunnilingus":
            self.character.emotional.add_stimulation_from_mas(pesan_mas)
            
            if self.character.emotional.arousal >= 85:
                self.role_climax_count += 1
                self.manual_mode_active = False
                self.auto_send_active = True
                self.current_phase_name = "missionary"
                self.phase_index = 6
                self.area_start_time = time.time()
                self.scene_count = 0
                
                return self._build_climax_scene(is_mas=False) + "\n\n" + self._build_missionary_request()
            
            return f"""*{self.character.name} menggeliat, napas tersengal*

"{self.character.panggilan}... lidah Mas... enak..."

*Pahanya terbuka lebar*

"Lanjut... jangan berhenti..." """
        
        # Missionary manual
        elif self.manual_mode_type == "missionary":
            self.character.emotional.add_stimulation_from_mas(pesan_mas)
            
            if self.character.emotional.arousal >= 85:
                self.role_climax_count += 1
                self.manual_mode_active = False
                self.auto_send_active = True
                self.current_phase_name = "doggy"
                self.phase_index = 7
                self.area_start_time = time.time()
                self.scene_count = 0
                
                return self._build_climax_scene(is_mas=False) + "\n\n" + self._build_doggy_request()
            
            return f"""*{self.character.name} memeluk Mas erat*

"{self.character.panggilan}... dalam... dalem banget..."

*Pinggulnya naik menyambut setiap dorongan*

"Ayo Mas... genjot..." """
        
        # Doggy manual
        elif self.manual_mode_type == "doggy":
            self.character.emotional.add_stimulation_from_mas(pesan_mas)
            
            # Cek Mas climax
            if any(k in msg_lower for k in ["climax", "crot", "keluar"]):
                self.mas_climax_count += 1
                self.manual_mode_active = False
                self.auto_send_active = True
                self.current_phase_name = "position_change"
                self.phase_index = 8
                self.area_start_time = time.time()
                self.scene_count = 0
                
                is_heavy = any(k in msg_lower for k in ["keras", "banyak"])
                return self._build_climax_scene(is_mas=True, is_heavy=is_heavy) + "\n\n" + self._build_position_change_request()
            
            return f"""*{self.character.name} merangkak, pantat naik*

"{self.character.panggilan}... dari belakang... dalem banget..."

*Tubuhnya bergoyang mengikuti ritme*

"Ayo Mas... kencengin..." """
        
        # Position change manual
        elif self.manual_mode_type == "position_change":
            # Deteksi posisi yang dipilih Mas
            if any(k in msg_lower for k in ["sofa", "sitting"]):
                self.current_position = "sitting"
            elif any(k in msg_lower for k in ["berdiri", "standing"]):
                self.current_position = "standing"
            elif any(k in msg_lower for k in ["kamar mandi", "shower"]):
                self.current_position = "standing (shower)"
            else:
                self.current_position = "sofa"
            
            self.character.emotional.add_stimulation_from_mas(pesan_mas)
            
            # Cek Mas climax ke-2
            if any(k in msg_lower for k in ["climax", "crot", "keluar"]):
                self.mas_climax_count += 1
                self.manual_mode_active = False
                self.auto_send_active = False
                self.current_phase_name = "aftercare"
                self.phase_index = 9
                self.aftercare_active = True
                
                is_heavy = any(k in msg_lower for k in ["keras", "banyak"])
                return self._build_climax_scene(is_mas=True, is_heavy=is_heavy) + "\n\n" + self._build_aftercare()
            
            return f"""*{self.character.name} bergerak ke posisi {self.current_position}*

"{self.character.panggilan}... gini ya... ayo..."

*Dia menarik Mas ke posisi baru*

"Mas mau lanjut..." """
        
        return None
    
    # =========================================================================
    # MAIN PROCESS
    # =========================================================================
    
    async def process(self, pesan_mas: str) -> str:
        """Proses pesan Mas"""
        
        # ========== MODE MANUAL AKTIF ==========
        if self.manual_mode_active:
            return await self._handle_manual_mode(pesan_mas)
        
        # ========== AFTERCARE ==========
        if self.aftercare_active:
            msg_lower = pesan_mas.lower()
            if any(k in msg_lower for k in ["lagi", "main lagi", "ulang", "lanjut"]):
                # Ulang dari awal
                self.phase_index = 1
                self.current_phase_name = "bj"
                self.area_start_time = time.time()
                self.scene_count = 0
                self.auto_send_active = True
                self.aftercare_active = False
                return await self._generate_bj_scene(1, self.BJ_SCENES)
            
            return self._build_aftercare()
        
        # ========== CEK JIKA SEDANG MENUNGGU RESPON ==========
        if self.waiting_for_response:
            if pesan_mas and pesan_mas.strip():
                return await self._handle_confirmation(pesan_mas)
            return None
        
        # ========== AUTO-SEND SCENE ==========
        if self.auto_send_active:
            elapsed = time.time() - self.area_start_time
            
            # Cek apakah fase selesai
            if self.current_phase_name == "bj" and elapsed >= self.BJ_DURATION:
                self.waiting_for_response = True
                self.waiting_for_type = "foreplay"
                self.auto_send_active = False
                return self._build_foreplay_request()
            
            elif self.current_phase_name == "kissing" and elapsed >= self.KISSING_DURATION:
                self.waiting_for_response = True
                self.waiting_for_type = "foreplay"
                self.auto_send_active = False
                return self._build_foreplay_request()
            
            elif self.current_phase_name == "cowgirl" and elapsed >= self.COWGIRL_DURATION:
                self.waiting_for_response = True
                self.waiting_for_type = "cunnilingus"
                self.auto_send_active = False
                return self._build_cunnilingus_request()
            
            # Kirim scene berikutnya
            expected_scene = int(elapsed // self.SCENE_INTERVAL)
            
            if expected_scene > self.scene_count:
                self.scene_count = expected_scene
                
                if self.current_phase_name == "bj":
                    return await self._generate_bj_scene(self.scene_count, self.BJ_SCENES)
                elif self.current_phase_name == "kissing":
                    return await self._generate_kissing_scene(self.scene_count, self.KISSING_SCENES)
                elif self.current_phase_name == "cowgirl":
                    return await self._generate_cowgirl_scene(self.scene_count, self.COWGIRL_SCENES)
            
            return None
        
        return None
    
    async def _handle_confirmation(self, pesan_mas: str) -> str:
        """Handle konfirmasi dari Mas"""
        msg_lower = pesan_mas.lower()
        
        # Konfirmasi mulai
        if self.waiting_for_type == "start":
            if any(k in msg_lower for k in ["ya", "ok", "gas", "mulai", "siap"]):
                self.waiting_for_response = False
                self.auto_send_active = True
                self.current_phase_name = "bj"
                self.phase_index = 1
                self.area_start_time = time.time()
                self.scene_count = 0
                return await self._generate_bj_scene(1, self.BJ_SCENES)
            else:
                return self._build_start_confirmation()
        
        # Konfirmasi foreplay
        elif self.waiting_for_type == "foreplay":
            self.waiting_for_response = False
            self.manual_mode_active = True
            self.manual_mode_type = "foreplay"
            return f"""*{self.character.name} berbaring, menunggu Mas*

"Ayo Mas... lakukan apa yang Mas mau ke aku..."

*Dia menatap Mas dengan mata sayu*

"Aku tunggu..." """
        
        # Konfirmasi cunnilingus
        elif self.waiting_for_type == "cunnilingus":
            self.waiting_for_response = False
            self.manual_mode_active = True
            self.manual_mode_type = "cunnilingus"
            return f"""*{self.character.name} berbaring, kaki terbuka*

"Ayo Mas... jilat aku..."

*Napasnya mulai berat*

"Aku tunggu..." """
        
        # Konfirmasi missionary
        elif self.waiting_for_type == "missionary":
            self.waiting_for_response = False
            self.manual_mode_active = True
            self.manual_mode_type = "missionary"
            return f"""*{self.character.name} berbaring telentang, tangan terbuka*

"Ayo Mas... Mas di atas..."

*Dia menarik tangan Mas*

"Aku tunggu..." """
        
        # Konfirmasi doggy
        elif self.waiting_for_type == "doggy":
            self.waiting_for_response = False
            self.manual_mode_active = True
            self.manual_mode_type = "doggy"
            return f"""*{self.character.name} merangkak, pantat naik*

"Ayo Mas... dari belakang..."

*Dia menoleh ke belakang*

"Aku tunggu..." """
        
        # Konfirmasi ganti posisi
        elif self.waiting_for_type == "position":
            self.waiting_for_response = False
            self.manual_mode_active = True
            self.manual_mode_type = "position_change"
            return f"""*{self.character.name} menunggu pilihan Mas*

"Pilih posisi yang Mas mau... sofa, berdiri, atau kamar mandi?"

*Dia tersenyum*

"Aku tunggu..." """
        
        return None
    
    # =========================================================================
    # START SESSION
    # =========================================================================
    
    async def start(self, location: str, price: int, duration_hours: int = 10) -> str:
        """Mulai sesi pelacur"""
        self.is_active = True
        self.current_phase = ServicePhase.GREETING
        self.phase_start_time = time.time()
        
        # Set booking info
        self.character.booking_location = location
        self.character.booking_price = price
        self.character.booking_duration = duration_hours
        
        # Reset semua state
        self.phase_index = 0
        self.current_phase_name = "confirmation"
        self.auto_send_active = False
        self.manual_mode_active = False
        self.aftercare_active = False
        self.waiting_for_response = True
        self.waiting_for_type = "start"
        self.mas_climax_count = 0
        self.role_climax_count = 0
        
        self.character.tracker.add_to_timeline(
            f"Sesi Pelacur dimulai - {duration_hours} jam di {location}",
            f"Harga: Rp{price:,}"
        )
        
        logger.info(f"🔥 Pelacur session started: {duration_hours}h at {location}")
        
        return self._build_start_confirmation()
