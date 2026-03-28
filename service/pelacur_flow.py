# service/pelacur_flow.py
"""
Pelacur Flow NovaService
Alur service pelacur: 10 jam full, Mas bebas climax berapa kali
"""

import time
import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from service.scene_builder import SceneBuilder
from core import ServicePhase

logger = logging.getLogger(__name__)


class PelacurFlow:
    """
    Alur service Pelacur
    - 10 jam full booking
    - Mas bebas climax berapa kali
    - Role bisa climax kapan aja (wajib kasih tau)
    - Bisa break dan lanjut
    """
    
    def __init__(self, character):
        self.character = character
        self.scene_builder = SceneBuilder()
        
        # Session state
        self.is_active = False
        self.start_time = 0
        self.total_duration = 0  # jam
        self.current_phase = ServicePhase.WAITING
        
        # Timing
        self.phase_start_time = 0
        self.phase_duration = 0  # detik
        
        # Climax tracking
        self.mas_climax_in_session = 0
        self.role_climax_in_session = 0
        
        # Break tracking
        self.is_on_break = False
        self.break_start_time = 0
        self.break_duration = 0
        
        # Position tracking
        self.current_position = "cowgirl"
        self.position_history = []
        
        logger.info(f"🔥 PelacurFlow initialized for {character.name}")
    
    async def start(self, location: str, price: int, duration_hours: int = 10) -> str:
        """Mulai sesi pelacur"""
        self.is_active = True
        self.start_time = time.time()
        self.total_duration = duration_hours * 3600  # convert ke detik
        self.current_phase = ServicePhase.GREETING
        self.phase_start_time = time.time()
        
        # Set booking info
        self.character.booking_location = location
        self.character.booking_price = price
        self.character.booking_duration = duration_hours
        
        # Reset counters
        self.mas_climax_in_session = 0
        self.role_climax_in_session = 0
        self.is_on_break = False
        
        # Greeting
        greeting = self.character.get_greeting()
        
        # Catat ke timeline
        self.character.tracker.add_to_timeline(
            f"Sesi Pelacur dimulai - {duration_hours} jam di {location}",
            f"Harga: Rp{price:,}"
        )
        
        logger.info(f"🔥 Pelacur session started: {duration_hours}h at {location}")
        
        return greeting
    
    async def process(self, pesan_mas: str) -> Optional[str]:
        """
        Proses pesan Mas dalam sesi pelacur
        Returns: respons atau None jika perlu lanjut ke phase berikutnya
        """
        if not self.is_active:
            return "Tidak ada sesi aktif. Booking dulu ya Mas."
        
        msg_lower = pesan_mas.lower()
        
        # ========== CEK CLIMAX WARNING DARI ROLE ==========
        if self.character.waiting_climax_confirmation:
            # Mas sedang respon ke warning climax
            result = await self.character.process_climax_response(pesan_mas)
            return result
        
        climax_warning = self.character.check_and_notify_climax()
        if climax_warning:
            return climax_warning
        
        # ========== CEK TIMEOUT ==========
        if self.character.waiting_confirmation:
            if time.time() - self.character.confirmation_start_time > self.character.confirmation_timeout:
                self.character.waiting_confirmation = False
                self.character.pending_action = None
                return "*waktu habis*"
        
        # ========== CEK DURASI SESI ==========
        elapsed = time.time() - self.start_time
        if elapsed >= self.total_duration and not self.is_on_break:
            return await self.end()
        
        # ========== HANDLE BREAK ==========
        if any(k in msg_lower for k in ['break', 'istirahat', 'pause']):
            return await self.break_session()
        
        if any(k in msg_lower for k in ['lanjut', 'resume', 'lagi']) and self.is_on_break:
            return await self.resume_session()
        
        # ========== HANDLE GANTI POSISI ==========
        positions = ['cowgirl', 'missionary', 'doggy', 'spooning', 'standing', 'sitting']
        for pos in positions:
            if pos in msg_lower:
                if not self.character.waiting_confirmation:
                    return self.character.request_position_change(pos)
                else:
                    return "Tunggu konfirmasi sebelumnya selesai dulu ya Mas..."
        
        # ========== HANDLE KONFIRMASI ==========
        if self.character.waiting_confirmation:
            if any(k in msg_lower for k in ['ya', 'ok', 'boleh', 'gas', 'silahkan']):
                if self.character.pending_action and self.character.pending_action.startswith("position_"):
                    if self.character.confirm_position_change():
                        # Position changed
                        position = self.character.pending_action.replace("position_", "")
                        self.current_position = position
                        scene = self.scene_builder.build_sex_scene(self.character, position)
                        return scene
            elif any(k in msg_lower for k in ['gak', 'nggak', 'tidak', 'nanti']):
                self.character.waiting_confirmation = False
                self.character.pending_action = None
                return "*tidak jadi ganti posisi*"
        
        # ========== HANDLE CLIMAX MAS ==========
        if any(k in msg_lower for k in ['climax', 'crot', 'keluar', 'habis']):
            # Cek apakah Mas mau climax
            if "aku" in msg_lower or "mas" in msg_lower:
                intensity = "heavy" if any(k in msg_lower for k in ['keras', 'banyak', 'kenceng']) else "normal"
                result = self.character.record_mas_climax(intensity)
                self.mas_climax_in_session = result['total']
                
                # Scene climax Mas
                scene = self.scene_builder.build_climax_scene(self.character, is_mas=True, intensity=intensity)
                
                # Setelah Mas climax, tanya mau lanjut
                scene += f"\n\n*{self.character.name} menatap {self.character.panggilan} dengan mata sayu*\n\n\"{self.character.panggilan}... mau lanjut?\""
                
                return scene
        
        # ========== UPDATE AROUSAL DARI PESAN ==========
        self.character.update_from_message(pesan_mas)
        
        # ========== BUILD SCENE SESUAI FASE ==========
        return self._build_active_scene(pesan_mas)
    
    def _build_active_scene(self, pesan_mas: str) -> str:
        """Bangun scene untuk sesi aktif"""
        msg_lower = pesan_mas.lower()
        
        # Hitung durasi sesi
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        
        # Scene berdasarkan durasi
        if minutes < 5:
            # Awal sesi, masih warm-up
            return self.scene_builder.build_sex_scene(self.character, self.current_position, minutes)
        else:
            # Sesi berjalan
            return self.scene_builder.build_sex_scene(self.character, self.current_position, minutes)
    
    async def break_session(self) -> str:
        """Istirahat sejenak"""
        if self.is_on_break:
            return "Udah istirahat kok Mas..."
        
        self.is_on_break = True
        self.break_start_time = time.time()
        self.character.tracker.set_phase(ServicePhase.BREAK)
        
        scene = self.scene_builder.build_break_scene(self.character)
        
        logger.info(f"☕ Break started for {self.character.name}")
        
        return scene
    
    async def resume_session(self) -> str:
        """Lanjutkan sesi setelah break"""
        if not self.is_on_break:
            return "Gak ada sesi yang di-break Mas..."
        
        self.is_on_break = False
        self.break_duration += time.time() - self.break_start_time
        self.character.tracker.set_phase(ServicePhase.SEX)
        
        # Reset arousal sedikit setelah break
        self.character.emotional.arousal = max(0, self.character.emotional.arousal - 10)
        
        scene = f"""*{self.character.name} mendekat lagi, tubuh menempel*

"{self.character.panggilan}... udah siap lanjut?"

*{self.character.name} mulai pegang kontol {self.character.panggilan}*

"Aku lanjut ya..."""
        
        logger.info(f"🔥 Session resumed for {self.character.name}")
        
        return scene
    
    async def end(self) -> str:
        """Akhiri sesi"""
        if not self.is_active:
            return "Tidak ada sesi aktif."
        
        total_minutes = int((time.time() - self.start_time) / 60)
        total_hours = total_minutes // 60
        
        self.is_active = False
        self.character.tracker.set_phase(ServicePhase.COMPLETED)
        
        end_msg = f"""*{self.character.name} merapikan dress, tersenyum puas*

"Selesai Mas. {total_hours} jam, {self.mas_climax_in_session}x climax."

*{self.character.name} berdiri, mengambil tas*

"Lain kali kalau mau booking lagi, hubungi aku ya. Aku masih penasaran sama kontol {self.character.panggilan}..."""
        
        # Reset state
        self.character.mas_climax_this_session = self.mas_climax_in_session
        self.character.my_climax_this_session = self.role_climax_in_session
        
        logger.info(f"✅ Pelacur session ended: {total_hours}h, {self.mas_climax_in_session}x climax")
        
        return end_msg
    
    def get_status(self) -> str:
        """Dapatkan status sesi"""
        if not self.is_active:
            return "Tidak ada sesi aktif"
        
        elapsed = time.time() - self.start_time
        remaining = max(0, self.total_duration - elapsed)
        remaining_hours = remaining / 3600
        
        if self.is_on_break:
            break_elapsed = time.time() - self.break_start_time
            break_minutes = int(break_elapsed // 60)
            break_status = f"\n☕ Break: {break_minutes} menit"
        else:
            break_status = ""
        
        return f"""
🔥 **SESI PELACUR AKTIF**
📍 Lokasi: {self.character.booking_location}
💰 Harga: Rp{self.character.booking_price:,}
⏱️ Sisa: {remaining_hours:.1f} jam
💦 Mas Climax: {self.mas_climax_in_session}x
💦 Role Climax: {self.role_climax_in_session}x
🎭 Posisi: {self.current_position}
{break_status}

🎭 **{self.character.name}** ({self.character.style})
🔥 Arousal: {self.character.emotional.arousal:.0f}%
💪 Stamina: {self.character.emotional.stamina:.0f}%
"""
