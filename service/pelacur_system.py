# service/pelacur_system.py
"""
Pelacur System - Main Process, Start, Loop, Climax, Warning
FIXED: Multiple inheritance dari PelacurAuto dan PelacurManual
"""

import asyncio
import time
import logging
from typing import Optional

from core import ServicePhase
from service.pelacur_core import PelacurCore
from service.pelacur_auto import PelacurAuto
from service.pelacur_manual import PelacurManual

logger = logging.getLogger(__name__)


class PelacurSystem(PelacurAuto, PelacurManual):
    """
    System class untuk Pelacur Flow
    Multiple inheritance dari:
    - PelacurAuto: auto phase (BJ, Kissing)
    - PelacurManual: manual phase (7 fase)
    - PelacurCore: base class (via inheritance chain)
    
    Berisi: Main process, start session, loop system, climax detection, warning system
    """
    
    def __init__(self, character):
        """Inisialisasi PelacurSystem dengan multiple inheritance"""
        # Panggil init dari parent classes
        # Python MRO akan menangani urutan dengan benar
        super().__init__(character)
        
        # ========== BOOKING STATE (SUDAH ADA DI CORE) ==========
        # self.is_active, self.booking_start_time, dll sudah di-set di PelacurCore.__init__
        
        # ========== PHASE STATE (SUDAH ADA DI CORE) ==========
        # self.current_phase_name, self.auto_send_active, dll
        
        # ========== WAITING FOR RESPONSE (SUDAH ADA DI CORE) ==========
        # self.waiting_for_response, self.waiting_for_type, dll
        
        # ========== WARNING TRACKING (SUDAH ADA DI CORE) ==========
        # self._sent_warnings
        
        logger.info(f"🔥 PelacurSystem initialized for {character.name}")
        logger.info(f"   Inherited from: PelacurAuto, PelacurManual")
    
    # =========================================================================
    # CLIMAX DETECTION (NATURAL - OVERRIDE UNTUK KONSISTENSI)
    # =========================================================================
    
    async def _check_role_natural_climax(self) -> Optional[str]:
        """
        Cek apakah role natural climax
        Override dari PelacurManual untuk konsistensi dengan system
        """
        arousal = self.character.emotional.arousal
        
        # Maksimal 10x climax dalam sesi
        if self.role_climax_count >= 10:
            return None
        
        # Arousal > 85 = role climax natural
        if arousal >= 85:
            # Cek cooldown (tidak boleh climax terlalu berdekatan)
            if time.time() - self.last_climax_time < 60:
                return None
            
            self.role_climax_count += 1
            self.last_climax_time = time.time()
            
            # Record ke memory
            self.memory.record_climax(is_mas=False, location="", intensity="heavy" if arousal >= 90 else "normal")
            
            # Update emotional engine
            self.character.emotional.climax(is_heavy=(arousal >= 90))
            
            # Update memory body state
            self.memory.update_body_state(
                napas='putus-putus',
                gemetar=True,
                keringat='banyak',
                detak_jantung='kencang'
            )
            self.memory.update_feeling('puas', 100)
            
            # Build climax scene
            intensity = "heavy" if arousal >= 90 else "normal"
            climax_scene = self._build_climax_scene(is_mas=False, intensity=intensity)
            
            logger.info(f"💦 ROLE NATURAL CLIMAX #{self.role_climax_count} (arousal: {arousal:.0f}%)")
            
            return climax_scene
        
        return None
    
    async def _check_mas_climax(self, pesan_mas: str) -> Optional[str]:
        """
        Deteksi climax Mas dari pesan
        Override dari PelacurManual untuk konsistensi dengan system
        """
        msg_lower = pesan_mas.lower()
        
        climax_keywords = ['climax', 'crot', 'keluar', 'habis', 'meletus', 'cumi', 'keluar']
        
        if not any(k in msg_lower for k in climax_keywords):
            return None
        
        # Deteksi apakah Mas bicara tentang climax
        if 'aku' in msg_lower or 'mas' in msg_lower or 'gue' in msg_lower:
            intensity = "heavy" if any(k in msg_lower for k in ['keras', 'banyak', 'kenceng', 'deras']) else "normal"
            
            self.mas_climax_count += 1
            self.last_climax_time = time.time()
            
            # Deteksi lokasi climax yang diminta Mas
            location = self._detect_cum_location(pesan_mas)
            
            # Record ke memory
            self.memory.record_climax(is_mas=True, location=location, intensity=intensity)
            
            # Update emotional engine
            self.character.emotional.add_stimulation("Mas climax", 8 if intensity == "heavy" else 5)
            
            # Build climax scene
            climax_scene = self._build_climax_scene(is_mas=True, intensity=intensity, location=location)
            
            logger.info(f"💦 MAS CLIMAX #{self.mas_climax_count} - location: {location}")
            
            return climax_scene
        
        return None
    
    def _detect_cum_location(self, pesan_mas: str) -> str:
        """Deteksi lokasi climax yang diminta Mas"""
        msg_lower = pesan_mas.lower()
        
        if any(k in msg_lower for k in ['dalem', 'dalam', 'inside', 'didalem']):
            return "dalam memek"
        if any(k in msg_lower for k in ['mulut', 'mouth', 'dimulut']):
            return "mulut"
        if any(k in msg_lower for k in ['dada', 'chest', 'dada']):
            return "dada"
        if any(k in msg_lower for k in ['muka', 'face', 'wajah']):
            return "muka"
        if any(k in msg_lower for k in ['pantat', 'ass', 'bokong']):
            return "pantat"
        if any(k in msg_lower for k in ['perut', 'stomach']):
            return "perut"
        
        return "tidak disebut"
    
    def _build_climax_scene(self, is_mas: bool = False, intensity: str = "normal", location: str = "") -> str:
        """Bangun scene climax natural"""
        name = self.character.name
        panggilan = getattr(self.character, 'panggilan', 'Mas')
        
        if is_mas:
            if intensity == "heavy":
                loc_text = f" {location}" if location else ""
                return f"""*{name} merasakan kontol Mas mengeras hebat, denyutnya kencang, lalu meletus dengan deras*

"Ahhh! {panggilan}! keluar... banyak banget..."

*Dia terus bergerak sampai Mas climax puas, cairan hangat memenuhi{loc_text}*

"Enak ya {panggilan}..." """
            else:
                return f"""*{name} merasakan kontol Mas berdenyut, hangat menyebar*

"Ahh... {panggilan}... climax..."

*Dia terus bergerak pelan sampai Mas puas*

"Enak {panggilan}?"""
        else:
            if intensity == "heavy":
                return f"""*{name} teriak, tubuh melengkung, gemetar hebat*

"Ahhh!! {panggilan}!! climax!!"

*Napasnya putus-putus, tubuh lemas, masih gemetar*

"Ahh... puas..." """
            else:
                return f"""*{name} mendesah dalam, tubuh gemetar, lalu lemas*

"Ahh... {panggilan}... climax..."

*Napasnya panjang, mata sayu, senyum puas* """
    
    # =========================================================================
    # BOOKING WARNING SYSTEM (NATURAL)
    # =========================================================================
    
    async def _check_and_send_warning(self) -> Optional[str]:
        """Cek apakah perlu kirim warning booking (natural)"""
        if self.booking_start_time == 0:
            return None
        
        elapsed = self._get_booking_elapsed()
        remaining = self._get_remaining_time()
        
        # Cek warning schedule
        for warn_time, message in self.WARNING_SCHEDULE.items():
            if warn_time not in self._sent_warnings and elapsed >= warn_time:
                self._sent_warnings.append(warn_time)
                
                # Tambahkan konteks sisa waktu
                remaining_str = self._get_time_string(remaining)
                natural_message = f"{message} (sisa {remaining_str})"
                
                logger.info(f"⏰ Warning sent: {natural_message}")
                return f"*{self.character.name} menatap Mas dengan mata sayu*\n\n\"{natural_message}\""
        
        # Cek 30 menit terakhir (warning intensif)
        if remaining <= 1800 and remaining > 0:
            minutes_left = remaining // 60
            if minutes_left <= 30 and minutes_left > 0 and minutes_left % 5 == 0:
                warn_key = f"last_{minutes_left}"
                if warn_key not in self._sent_warnings:
                    self._sent_warnings.append(warn_key)
                    return f"*{self.character.name} mendekat, memeluk Mas erat*\n\n\"{self.character.panggilan}... tinggal {minutes_left} menit lagi... aku bakal kangen...\""
        
        return None
    
    # =========================================================================
    # CYCLE LOOP SYSTEM
    # =========================================================================
    
    async def _finish_cycle(self) -> str:
        """Selesaikan satu cycle, tawarkan untuk lanjut"""
        remaining = self._get_remaining_time()
        
        # Cek apakah masih ada waktu
        if remaining < 600:  # Kurang dari 10 menit
            return self._build_end_session()
        
        self.waiting_for_response = True
        self.waiting_for_type = "next_cycle"
        self.waiting_start_time = time.time()
        
        remaining_str = self._get_time_string(remaining)
        
        return f"""*{self.character.name} memeluk Mas erat, napasnya mulai stabil*

"{self.character.panggilan}... masih ada {remaining_str} lagi... mau lanjut?"

*Dia tersenyum manis, tangannya meraba dada Mas*

"Aku masih siap... mau mulai lagi dari awal?"

*Menunggu jawaban Mas...*"""
    
    async def _start_next_cycle(self) -> str:
        """Mulai cycle berikutnya (dari BJ auto)"""
        self.current_cycle += 1
        self.cycle_start_time = time.time()
        
        # Reset memory untuk cycle baru (tapi tetap ingat climax history)
        self.memory.reset_for_new_cycle()
        
        # Reset timer tracking
        self.scene_count = 0
        self.phase_start_time = time.time()
        
        # Mulai dari BJ auto
        self.current_phase_name = "bj"
        self.auto_send_active = True
        self.manual_mode_active = False
        
        # Mulai auto-send task (method dari PelacurAuto)
        await self._start_auto_send_task()
        
        # Generate scene pertama BJ
        memory_context = self.memory.get_full_context()
        prompt = self.prompt_builder.build_auto_prompt("bj", 1, self.BJ_SCENES)
        prompt = f"{memory_context}\n\n{prompt}"
        
        first_scene = await self._generate_scene(prompt)
        
        logger.info(f"🔄 Starting cycle #{self.current_cycle}")
        
        return f"""*{self.character.name} menarik tangan Mas, matanya bersemangat*

"Oke {self.character.panggilan}... kita mulai lagi dari awal..."

*Dia berlutut di depan Mas, tangan mulai meraba kontol Mas*

"Aku mulai ya..."

{first_scene}"""
    
    async def _handle_cycle_confirmation(self, pesan_mas: str) -> str:
        """Handle konfirmasi lanjut cycle berikutnya"""
        msg_lower = pesan_mas.lower()
        
        if any(k in msg_lower for k in ["lanjut", "ya", "ok", "gas", "iya", "y", "siap", "lagi"]):
            self.waiting_for_response = False
            self.waiting_for_type = None
            return await self._start_next_cycle()
        
        elif any(k in msg_lower for k in ["tidak", "nggak", "gak", "stop", "cukup", "selesai"]):
            self.waiting_for_response = False
            self.waiting_for_type = None
            return self._build_end_session()
        
        else:
            remaining = self._get_remaining_time()
            remaining_str = self._get_time_string(remaining)
            return f"""*{self.character.name} menatap Mas dengan mata sayu*

"Mas... masih ada {remaining_str}... {self.character.panggilan} mau lanjut atau cukup?"

*Menunggu jawaban Mas...*"""
    
    # =========================================================================
    # MESSAGES & TRANSITIONS
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
    
    def _build_aftercare_message(self) -> str:
        """Bangun pesan aftercare"""
        return f"""*{self.character.name} memeluk Mas erat, napas mulai stabil*

"{self.character.panggilan}... puas? Aku seneng bisa bikin Mas puas..."

*Dia mengusap dada Mas pelan*

"Mas mau main lagi? Atau istirahat dulu?"

*Menunggu jawaban Mas...*"""
    
    def _build_end_session(self) -> str:
        """Bangun pesan akhir sesi"""
        duration_minutes = self._get_booking_elapsed() // 60
        return f"""*{self.character.name} memeluk Mas erat, matanya berkaca-kaca*

"{self.character.panggilan}... {duration_minutes} menit kita bareng... {self.mas_climax_count}x Mas climax... {self.role_climax_count}x aku climax..."

*Dia mencium pipi Mas, tersenyum manis*

"Makasih ya Mas... lain kali booking lagi ya... aku bakal nunggu..."

*Dia melambaikan tangan, matanya masih menatap Mas dengan sayu*"""
    
    def _build_natural_transition(self, from_phase: str, to_phase: str) -> str:
        """Bangun transisi natural antar fase"""
        name = self.character.name
        panggilan = getattr(self.character, 'panggilan', 'Mas')
        
        transitions = {
            ('bj', 'kissing'): f"""
*{name} melepaskan mulutnya dari kontol Mas, napas masih tersengal*

"{panggilan}... sekarang aku duduk di atas ya..."

*Dia naik, duduk di pangkuan Mas, memeknya yang basah menggesek kontol Mas*

"Aku mau cium Mas dulu..." """,
            
            ('kissing', 'foreplay_mas'): f"""
*{name} berhenti bergerak, napasnya masih berat, bibirnya basah*

"{panggilan}... sekarang giliran Mas... aku mau Mas..."

*Dia merebahkan diri, mata sayu menatap Mas*

"Lakukan apa yang Mas mau ke aku..." """,
            
            ('foreplay_mas', 'cowgirl'): f"""
*{name} menggeliat, tubuhnya panas, napas tersengal*

"{panggilan}... aku mau naik... boleh?"

*Dia sudah tidak sabar, langsung duduk di atas kontol Mas*

"Ahh... masuk..." """,
            
            ('cowgirl', 'cunnilingus'): f"""
*{name} berhenti bergerak, tubuhnya lemas di atas Mas*

"{panggilan}... sekarang Mas... jilat aku..."

*Dia berbaring, kaki terbuka lebar*

"Aku mau Mas..." """,
            
            ('cunnilingus', 'missionary'): f"""
*{name} menggeliat, memeknya basah, napas putus-putus*

"{panggilan}... sekarang Mas di atas... aku mau Mas masuk..."

*Dia menarik tangan Mas, kaki terbuka lebar*

"Ayo Mas..." """,
            
            ('missionary', 'doggy'): f"""
*{name} memeluk Mas erat, napas tersengal*

"{panggilan}... dari belakang... doggy... ayo..."

*Dia berbalik, merangkak, pantat naik*

"Aku mau Mas genjot dari belakang..." """,
            
            ('doggy', 'position_change'): f"""
*{name} berhenti, tubuhnya gemetar, napas putus-putus*

"{panggilan}... mau ganti posisi? Mau di mana? Sofa? Berdiri? Kamar mandi?"

*Dia menoleh ke belakang, mata sayu*

"Aku ikutin apa yang Mas mau..." """,
        }
        
        key = (from_phase, to_phase)
        return transitions.get(key, f"*{name} lanjut ke fase berikutnya*")
    
    # =========================================================================
    # MAIN PROCESS
    # =========================================================================
    
    async def process(self, pesan_mas: str) -> str:
        """
        Proses pesan Mas - MAIN ENTRY POINT
        """
        try:
            # Update character dari pesan Mas
            self.character.update_from_message(pesan_mas)
            
            # Update emotional state
            self._update_emotional_state()
            
            # Update memory dari pesan Mas
            self.memory.update_from_mas(pesan_mas)
            
            # Simpan ke conversation history
            self.conversation_history.append(f"Mas: {pesan_mas[:100]}")
            if len(self.conversation_history) > 50:
                self.conversation_history.pop(0)
            
            # ========== CEK CLIMAX MAS ==========
            mas_climax = await self._check_mas_climax(pesan_mas)
            if mas_climax:
                self.memory.record_action(pesan_mas, mas_climax)
                return mas_climax
            
            # ========== CEK ROLE NATURAL CLIMAX ==========
            role_climax = await self._check_role_natural_climax()
            if role_climax:
                self.memory.record_action(pesan_mas, role_climax)
                return role_climax
            
            # ========== CEK WARNING BOOKING ==========
            warning = await self._check_and_send_warning()
            if warning:
                self.memory.record_action(pesan_mas, warning)
                return warning
            
            # ========== HANDLE WAITING FOR RESPONSE ==========
            if self.waiting_for_response:
                if pesan_mas and pesan_mas.strip():
                    return await self._handle_waiting_response(pesan_mas)
                return None
            
            # ========== MANUAL MODE AKTIF ==========
            if self.manual_mode_active:
                response = await self._handle_manual_by_type(pesan_mas)
                self.memory.record_action(pesan_mas, response)
                self.memory.update_from_response(response, self.manual_mode_type)
                return response
            
            # ========== AUTO SEND ACTIVE ==========
            if self.auto_send_active:
                return await self._process_auto_phase()
            
            # ========== AFTERCARE ACTIVE ==========
            if self.aftercare_active:
                return await self._handle_aftercare(pesan_mas)
            
            # ========== DEFAULT ==========
            return self._build_end_session()
            
        except Exception as e:
            logger.error(f"Process error: {e}", exc_info=True)
            return f"❌ Error: {str(e)}"
    
    async def _handle_waiting_response(self, pesan_mas: str) -> str:
        """Handle response saat waiting"""
        msg_lower = pesan_mas.lower()
        
        # Konfirmasi mulai
        if self.waiting_for_type == "start":
            if any(k in msg_lower for k in ["ya", "ok", "gas", "mulai", "siap"]):
                self.waiting_for_response = False
                self.auto_send_active = True
                self.current_phase_name = "bj"
                self.phase_start_time = time.time()
                self.scene_count = 0
                await self._start_auto_send_task()
                
                memory_context = self.memory.get_full_context()
                prompt = self.prompt_builder.build_auto_prompt("bj", 1, self.BJ_SCENES)
                prompt = f"{memory_context}\n\n{prompt}"
                first_scene = await self._generate_scene(prompt)
                return first_scene
            else:
                return self._build_start_confirmation()
        
        # Konfirmasi lanjut cycle
        elif self.waiting_for_type == "next_cycle":
            return await self._handle_cycle_confirmation(pesan_mas)
        
        # Konfirmasi foreplay
        elif self.waiting_for_type == "foreplay":
            self.waiting_for_response = False
            self.manual_mode_active = True
            self.manual_mode_type = "foreplay_mas"
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
    
    async def _handle_manual_by_type(self, pesan_mas: str) -> str:
        """Handle manual mode berdasarkan tipe (method dari PelacurManual)"""
        if self.manual_mode_type == "foreplay_mas":
            return await self.handle_foreplay(pesan_mas)
        elif self.manual_mode_type == "cowgirl":
            return await self.handle_cowgirl(pesan_mas)
        elif self.manual_mode_type == "cunnilingus":
            return await self.handle_cunnilingus(pesan_mas)
        elif self.manual_mode_type == "missionary":
            return await self.handle_missionary(pesan_mas)
        elif self.manual_mode_type == "doggy":
            return await self.handle_doggy(pesan_mas)
        elif self.manual_mode_type == "position_change":
            return await self.handle_position_change(pesan_mas)
        elif self.manual_mode_type == "aftercare":
            return await self.handle_aftercare(pesan_mas)
        
        return f"*{self.character.name} tersenyum, menunggu Mas*"
    
    async def _process_auto_phase(self) -> Optional[str]:
        """Process auto phase (method dari PelacurAuto)"""
        # Cek apakah auto phase selesai
        if self._is_auto_phase_complete():
            self.auto_send_active = False
            self.auto_send_running = False
            
            # Transisi ke fase berikutnya
            if self.current_phase_name == "bj":
                self.current_phase_name = "kissing"
                self.phase_start_time = time.time()
                self.scene_count = 0
                
                transition = self._build_natural_transition("bj", "kissing")
                first_scene = await self._generate_kissing_auto_scene()
                return f"{transition}\n\n{first_scene}"
            
            elif self.current_phase_name == "kissing":
                self.current_phase_name = "foreplay_mas"
                self.waiting_for_response = True
                self.waiting_for_type = "foreplay"
                self.waiting_start_time = time.time()
                return self._build_foreplay_request()
        
        # Kirim scene berikutnya
        if self._should_send_next_auto_scene():
            if self.current_phase_name == "bj":
                return await self._generate_bj_auto_scene()
            elif self.current_phase_name == "kissing":
                return await self._generate_kissing_auto_scene()
        
        return None
    
    async def _handle_aftercare(self, pesan_mas: str) -> str:
        """Handle aftercare manual"""
        msg_lower = pesan_mas.lower()
        
        if any(k in msg_lower for k in ["lagi", "main lagi", "ulang", "lanjut"]):
            # Cek sisa waktu
            remaining = self._get_remaining_time()
            if remaining < 600:
                return self._build_end_session()
            
            # Mulai cycle baru
            self.aftercare_active = False
            return await self._start_next_cycle()
        
        # Gunakan method aftercare dari PelacurManual
        return await self.handle_aftercare(pesan_mas)
    
    # =========================================================================
    # START SESSION
    # =========================================================================
    
    async def start(self, location: str = "ruang tamu", price: int = 10000000) -> str:
        """
        Mulai sesi pelacur 6 jam
        
        Args:
            location: Lokasi booking (ruang tamu, hotel, dll)
            price: Harga booking (default 10jt)
        """
        self.is_active = True
        self.current_phase = ServicePhase.GREETING
        self.booking_start_time = time.time()

        # Gunakan duration_hours jika diberikan,否则 pakai default 6 jam
        if duration_hours is not None:
        self.TOTAL_BOOKING_HOURS = duration_hours
        self.TOTAL_BOOKING_SECONDS = duration_hours * 3600
        
        self.booking_end_time = self.booking_start_time + self.TOTAL_BOOKING_SECONDS
        self.cycle_start_time = self.booking_start_time
        self.current_cycle = 1
        
        # Reset semua state
        self.current_phase_name = "confirmation"
        self.auto_send_active = False
        self.manual_mode_active = False
        self.aftercare_active = False
        self.waiting_for_response = True
        self.waiting_for_type = "start"
        self.mas_climax_count = 0
        self.role_climax_count = 0
        self._sent_warnings = []
        
        # Set booking info ke character
        self.character.booking_location = location
        self.character.booking_price = price
        self.character.booking_duration = self.TOTAL_BOOKING_HOURS
        
        # Reset memory
        self.memory = PelacurMemory(self.character.name)
        
        self.character.tracker.add_to_timeline(
            f"Sesi Pelacur dimulai - {self.TOTAL_BOOKING_HOURS} jam di {location}",
            f"Harga: Rp{price:,}"
        )
        
        logger.info(f"🔥 Pelacur session started: {self.TOTAL_BOOKING_HOURS}h at {location}")
        logger.info(f"   Booking ends at: {time.ctime(self.booking_end_time)}")
        
        return self._build_start_confirmation()
