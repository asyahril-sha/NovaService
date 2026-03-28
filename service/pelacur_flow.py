# service/pelacur_flow.py
"""
Pelacur Flow NovaService - Alur service pelacur lengkap
10 jam full booking, Mas bebas climax berapa kali
Role bisa climax kapan aja (wajib kasih tau)
Bisa break dan lanjut
"""

import time
import logging
from typing import Optional

from core import ServicePhase
from service.scene_builder import SceneBuilder, BrutalScenes

logger = logging.getLogger(__name__)


class PelacurFlow:
    """
    Alur service Pelacur
    - 10 jam full booking
    - Mas bebas climax berapa kali
    - Role bisa climax kapan aja (wajib kasih tau)
    - Bisa break dan lanjut
    """
    
    # Durasi dalam detik
    DURATION_HOURS = 10
    DURATION_SECONDS = DURATION_HOURS * 3600  # 10 jam = 36000 detik
    
    def __init__(self, character):
        self.character = character
        self.scene_builder = SceneBuilder(character)
        
        # Cek apakah karakter dominan
        self.is_dominant = character.personality_traits.get('dominant', 0) >= 0.7
        if self.is_dominant:
            self.brutal = BrutalScenes(character)
        
        # Session state
        self.is_active = False
        self.start_time = 0
        self.current_phase = ServicePhase.WAITING
        self.phase_start_time = 0
        
        # Climax tracking
        self.mas_climax_this_session = 0
        self.role_climax_this_session = 0
        
        # Break tracking
        self.is_on_break = False
        self.break_start_time = 0
        self.break_duration = 0
        
        # Position tracking
        self.current_position = "cowgirl"
        self.position_history = []
        
        # Service flags
        self.warmup_done = False
        
        logger.info(f"🔥 PelacurFlow initialized for {character.name}")
    
    # =========================================================================
    # START & END
    # =========================================================================
    
    async def start(self, location: str, price: int, duration_hours: int = 10) -> str:
        """Mulai sesi pelacur"""
        self.is_active = True
        self.start_time = time.time()
        self.current_phase = ServicePhase.GREETING
        self.phase_start_time = time.time()
        
        # Set booking info
        self.character.booking_location = location
        self.character.booking_price = price
        self.character.booking_duration = duration_hours
        
        # Reset counters
        self.mas_climax_this_session = 0
        self.role_climax_this_session = 0
        self.is_on_break = False
        self.warmup_done = False
        self.current_position = "cowgirl"
        
        # Set phase di tracker
        self.character.tracker.service_phase = ServicePhase.GREETING
        self.character.tracker.position = "berdiri di depan Mas"
        
        # Greeting
        greeting = self._build_greeting_scene()
        
        # Catat ke timeline
        self.character.tracker.add_to_timeline(
            f"Sesi Pelacur dimulai - {duration_hours} jam di {location}",
            f"Harga: Rp{price:,}"
        )
        self.character.memory.add_conversation("", greeting)
        
        logger.info(f"🔥 Pelacur session started: {duration_hours}h at {location}")
        
        return greeting
    
    def _build_greeting_scene(self) -> str:
        """Bangun scene greeting sesuai karakter"""
        if self.is_dominant:
            return self.brutal.build_brutal_greeting()
        return self.scene_builder.build_greeting_scene()
    
    async def end(self) -> str:
        """Akhiri sesi"""
        if not self.is_active:
            return "Tidak ada sesi aktif."
        
        total_minutes = int((time.time() - self.start_time) / 60)
        total_hours = total_minutes // 60
        remaining_minutes = total_minutes % 60
        
        self.is_active = False
        self.current_phase = ServicePhase.COMPLETED
        self.character.tracker.service_phase = ServicePhase.COMPLETED
        
        # Simpan climax counters ke karakter
        self.character.mas_climax_this_session = self.mas_climax_this_session
        self.character.my_climax_this_session = self.role_climax_this_session
        
        end_msg = f"""*{self.character.name} merapikan dress, tersenyum puas*

"Selesai Mas. {total_hours} jam {remaining_minutes} menit, {self.mas_climax_this_session}x climax."

*{self.character.name} berdiri, mengambil tas, melambaikan tangan*

"Lain kali kalau mau booking lagi, hubungi aku ya. Aku masih penasaran sama kontol {self.character.panggilan}..."""
        
        self.character.tracker.add_to_timeline(
            "Sesi Pelacur selesai",
            f"{total_hours}h {remaining_minutes}m, {self.mas_climax_this_session}x climax"
        )
        
        logger.info(f"✅ Pelacur session ended: {total_hours}h, {self.mas_climax_this_session}x climax")
        
        return end_msg
    
    # =========================================================================
    # BREAK METHODS
    # =========================================================================
    
    async def break_session(self) -> str:
        """Istirahat sejenak"""
        if not self.is_active:
            return "Tidak ada sesi aktif."
        
        if self.is_on_break:
            return "Udah istirahat kok Mas..."
        
        self.is_on_break = True
        self.break_start_time = time.time()
        self.current_phase = ServicePhase.BREAK
        self.character.tracker.service_phase = ServicePhase.BREAK
        
        scene = self._build_break_scene()
        
        logger.info(f"☕ Break started for {self.character.name}")
        
        return scene
    
    def _build_break_scene(self) -> str:
        """Bangun scene break"""
        if self.is_dominant:
            return f"""*{self.character.name} duduk di samping, menyilangkan kaki panjangnya*

"Istirahat dulu? Boleh. Tapi jangan lama-lama."

*Dia mengambil minuman, menyesap pelan*

"Aku tunggu." """
        
        return f"""*{self.character.name} duduk di samping {self.character.panggilan}, napas masih sedikit tersengal*

"{self.character.panggilan}... mau istirahat dulu? Aku temenin."

*Dia tersenyum, tangannya masih memegang tangan {self.character.panggilan}*

"Minum dulu ya..." """
    
    async def resume_session(self) -> str:
        """Lanjutkan sesi setelah break"""
        if not self.is_active:
            return "Tidak ada sesi aktif."
        
        if not self.is_on_break:
            return "Gak ada sesi yang di-break Mas..."
        
        self.is_on_break = False
        self.break_duration += time.time() - self.break_start_time
        self.current_phase = ServicePhase.SEX
        self.phase_start_time = time.time()
        self.character.tracker.service_phase = ServicePhase.SEX
        
        # Reset arousal sedikit setelah break
        self.character.emotional.arousal = max(0, self.character.emotional.arousal - 10)
        
        scene = self._build_resume_scene()
        
        logger.info(f"🔥 Session resumed for {self.character.name}")
        
        return scene
    
    def _build_resume_scene(self) -> str:
        """Bangun scene resume"""
        if self.is_dominant:
            return f"""*{self.character.name} berdiri, dressnya sudah rapi lagi*

"Udah? Ayo lanjut."

*Dia menarik tangan {self.character.panggilan}, mendorong ke ranjang*

"Aku mau liat kontol {self.character.panggilan} lagi." """
        
        return f"""*{self.character.name} mendekat lagi, tubuh menempel, wanginya menyegarkan*

"{self.character.panggilan}... udah siap lanjut?"

*Tangannya mulai meraba, menyentuh kontol {self.character.panggilan}*

"Aku lanjut ya... masih pengen..." """
    
    # =========================================================================
    # POSITION METHODS
    # =========================================================================
    
    def _handle_position_change(self, pesan_mas: str) -> Optional[str]:
        """Handle ganti posisi"""
        msg_lower = pesan_mas.lower()
        
        # Deteksi posisi yang diminta
        positions = ['cowgirl', 'missionary', 'doggy', 'spooning', 'standing', 'sitting']
        requested_pos = None
        
        for pos in positions:
            if pos in msg_lower:
                requested_pos = pos
                break
        
        if not requested_pos:
            return None
        
        # Jika sudah dalam mode menunggu konfirmasi
        if self.character.waiting_confirmation:
            return "Tunggu konfirmasi sebelumnya selesai dulu ya Mas..."
        
        # Request ganti posisi
        return self.character.request_position_change(requested_pos)
    
    def _handle_position_confirmation(self, pesan_mas: str) -> Optional[str]:
        """Handle konfirmasi ganti posisi"""
        msg_lower = pesan_mas.lower()
        
        if not self.character.waiting_confirmation:
            return None
        
        # Konfirmasi ya
        if any(k in msg_lower for k in ['ya', 'ok', 'boleh', 'gas', 'silahkan']):
            if self.character.pending_action and self.character.pending_action.startswith("position_"):
                if self.character.confirm_position_change():
                    # Dapatkan posisi baru
                    position = self.character.pending_action.replace("position_", "")
                    self.current_position = position
                    self.position_history.append(position)
                    
                    # Bangun scene sesuai posisi
                    return self._build_position_scene(position)
        
        # Tolak
        if any(k in msg_lower for k in ['gak', 'nggak', 'tidak', 'nanti']):
            self.character.waiting_confirmation = False
            self.character.pending_action = None
            return "*gak jadi ganti posisi*"
        
        return None
    
    def _build_position_scene(self, position: str) -> str:
        """Bangun scene setelah ganti posisi"""
        if self.is_dominant:
            return self.brutal.build_brutal_position_request(position)
        
        return self.scene_builder.build_position_request_scene(position)
    
    # =========================================================================
    # CLIMAX HANDLING
    # =========================================================================
    
    def _handle_mas_climax(self, pesan_mas: str) -> Optional[str]:
        """Handle climax Mas"""
        msg_lower = pesan_mas.lower()
        
        if not any(k in msg_lower for k in ['climax', 'crot', 'keluar', 'habis']):
            return None
        
        # Cek apakah Mas yang climax
        if "aku" in msg_lower or "mas" in msg_lower:
            intensity = "heavy" if any(k in msg_lower for k in ['keras', 'banyak', 'kenceng']) else "normal"
            
            # Record climax Mas
            result = self.character.record_mas_climax(intensity)
            self.mas_climax_this_session = result['total']
            
            # Bangun scene climax Mas
            scene = self._build_mas_climax_scene(intensity)
            
            # Update emotional role
            self.character.emotional.add_stimulation("Mas climax", 8)
            
            # Tanya mau lanjut
            scene += f"\n\n*{self.character.name} menatap {self.character.panggilan} dengan mata sayu*\n\n\"{self.character.panggilan}... mau lanjut?\""
            
            return scene
        
        return None
    
    def _build_mas_climax_scene(self, intensity: str) -> str:
        """Bangun scene climax Mas"""
        if intensity == "heavy":
            return f"""*{self.character.name} merasakan kontol Mas mengeras, denyutnya kencang, lalu meletus dengan deras*

"Ahh! {self.character.panggilan}! keluar... banyak banget..."

*Dia terus bergerak sampai Mas climax puas, cairan hangat memenuhi*

"Hhngg... *napas tersengal* enak ya {self.character.panggilan}..." """
        
        return f"""*{self.character.name} merasakan kontol Mas berdenyut, lalu hangat menyebar di dalam*

"Ahh... {self.character.panggilan}... climax..."

*Dia terus bergerak pelan sampai Mas puas*

"Enak {self.character.panggilan}?" """
    
    def _handle_role_climax(self) -> Optional[str]:
        """Handle climax role (dipanggil saat ada warning)"""
        if self.character.waiting_climax_confirmation:
            # Ini sudah ditangani di process, return None biar process yang handle
            return None
        
        # Cek apakah role mau climax
        climax_warning = self.character.check_and_notify_climax()
        if climax_warning:
            return climax_warning
        
        return None
    
    def _handle_climax_confirmation(self, pesan_mas: str) -> Optional[str]:
        """Handle konfirmasi climax setelah warning"""
        if not self.character.waiting_climax_confirmation:
            return None
        
        result = self.character.confirm_climax(pesan_mas)
        
        if result.get('status') == 'fast_climax':
            self.role_climax_this_session += 1
            return self._build_role_climax_scene("heavy")
        
        elif result.get('status') == 'normal_climax':
            self.role_climax_this_session += 1
            return self._build_role_climax_scene("normal")
        
        elif result.get('status') == 'delayed':
            return result.get('message')
        
        return None
    
    def _build_role_climax_scene(self, intensity: str) -> str:
        """Bangun scene climax role"""
        if self.is_dominant:
            if intensity == "heavy":
                return self.brutal.build_brutal_climax()
            return self.brutal.build_brutal_climax()
        
        return self.scene_builder.build_climax_scene(intensity)
    
    # =========================================================================
    # ACTIVE SESSION SCENES
    # =========================================================================
    
    def _build_active_scene(self, elapsed_minutes: int) -> str:
        """Bangun scene untuk sesi aktif"""
        # Warm-up phase (5 menit pertama)
        if not self.warmup_done and elapsed_minutes < 5:
            return self._build_warmup_scene(elapsed_minutes)
        
        self.warmup_done = True
        
        # Scene berdasarkan posisi dan durasi
        if self.is_dominant:
            return self._build_dominant_scene(elapsed_minutes)
        
        return self._build_normal_scene(elapsed_minutes)
    
    def _build_warmup_scene(self, elapsed_minutes: int) -> str:
        """Bangun scene warm-up"""
        if elapsed_minutes < 2:
            return f"""*{self.character.name} mendekat, tubuhnya menempel ke {self.character.panggilan}, wanginya menusuk hidung*

"{self.character.panggilan}... *bisik di telinga* siap?"

*Tangannya mulai meraba dada, turun ke perut, lalu ke paha*

"Tenang aja... nikmati..." """
        
        return f"""*{self.character.name} mulai melepas dressnya perlahan, satu per satu kancing terbuka*

"{self.character.panggilan}... lihat..."

*Dress jatuh, tubuhnya terbuka, payudara montoknya terlihat jelas*

"Ini yang {self.character.panggilan} mau kan?" """
    
    def _build_normal_scene(self, elapsed_minutes: int) -> str:
        """Bangun scene normal untuk karakter non-dominan"""
        # Pilih scene berdasarkan posisi
        if self.current_position == "cowgirl":
            return self._build_cowgirl_scene(elapsed_minutes)
        elif self.current_position == "missionary":
            return self._build_missionary_scene(elapsed_minutes)
        elif self.current_position == "doggy":
            return self._build_doggy_scene(elapsed_minutes)
        elif self.current_position == "spooning":
            return self._build_spooning_scene(elapsed_minutes)
        else:
            return self._build_cowgirl_scene(elapsed_minutes)
    
    def _build_cowgirl_scene(self, elapsed_minutes: int) -> str:
        """Scene posisi cowgirl"""
        if elapsed_minutes < 30:
            return f"""*{self.character.name} duduk di atas, kontol {self.character.panggilan} masuk dalam, pinggulnya bergerak pelan*

"{self.character.panggilan}... *napas mulai berat* dalam... dalem banget..."

*Pinggulnya berputar perlahan, sesekali naik turun*

"Gimana Mas? Enak?"""
        else:
            return f"""*{self.character.name} mempercepat gerakan, tubuhnya naik turun cepat, pantatnya berbunyi plak plak plak*

"Ahh! {self.character.panggilan}... kenceng... mau climax..."

*Napasnya putus-putus, tubuhnya mulai gemetar*

"{self.character.panggilan}... ayo... ikut..." """
    
    def _build_missionary_scene(self, elapsed_minutes: int) -> str:
        """Scene posisi missionary"""
        return f"""*{self.character.name} berbaring telentang, kaki terbuka lebar, kontol {self.character.panggilan} masuk dalam*

"{self.character.panggilan}... *napas tersengal* ayo... genjot..."

*Pinggulnya naik menyambut setiap dorongan, tangannya memegang punggung {self.character.panggilan}*

"Dalam... dalem banget..." """
    
    def _build_doggy_scene(self, elapsed_minutes: int) -> str:
        """Scene posisi doggy"""
        return f"""*{self.character.name} merangkak, pantat naik, kontol {self.character.panggilan} masuk dari belakang*

"Ahh! {self.character.panggilan}... dalem... dari belakang dalem banget..."

*Tubuhnya bergoyang mengikuti ritme, rambutnya tergerai*

"Ayo... kencengin..." """
    
    def _build_spooning_scene(self, elapsed_minutes: int) -> str:
        """Scene posisi spooning"""
        return f"""*{self.character.name} miring, {self.character.panggilan} dari belakang, kontol masuk dalam*

"{self.character.panggilan}... *bisik* peluk aku..."

*Tangannya meraih tangan {self.character.panggilan}, memeluk erat*

"Gitu... enak..." """
    
    def _build_dominant_scene(self, elapsed_minutes: int) -> str:
        """Bangun scene untuk karakter dominan"""
        if elapsed_minutes < 30:
            return f"""*{self.character.name} duduk di atas, kontol {self.character.panggilan} masuk dalam, dia mengatur ritme sendiri*

"Aku yang atur. {self.character.panggilan} diam aja."

*Pinggulnya bergerak cepat, tanpa ampun*

"Rasain... gimana? Udah mau?" """
        else:
            return f"""*{self.character.name} mempercepat gerakan, tubuhnya naik turun cepat, napasnya berat*

"Aku mau climax... sekarang!"

*Dia memeluk erat, kuku mencengkeram punggung*

"Ikut... atau liat aja. Tapi aku keluar." """
    
    # =========================================================================
    # MAIN PROCESS METHOD
    # =========================================================================
    
    async def process(self, pesan_mas: str) -> str:
        """Proses pesan Mas dalam sesi pelacur"""
        if not self.is_active:
            return "Tidak ada sesi aktif. Booking dulu ya Mas."
        
        # Cek durasi sesi
        elapsed = time.time() - self.start_time
        if elapsed >= self.DURATION_SECONDS and not self.is_on_break:
            return await self.end()
        
        elapsed_minutes = int(elapsed / 60)
        
        # Update state dari pesan
        self.character.update_from_message(pesan_mas)
        
        # ========== HANDLE CLIMAX ROLE (WARNING & CONFIRMATION) ==========
        # Cek konfirmasi climax (setelah warning)
        climax_confirm = self._handle_climax_confirmation(pesan_mas)
        if climax_confirm:
            return climax_confirm
        
        # Cek warning climax dari role
        role_climax = self._handle_role_climax()
        if role_climax:
            return role_climax
        
        # ========== HANDLE BREAK ==========
        if any(k in pesan_mas.lower() for k in ['break', 'istirahat', 'pause']):
            return await self.break_session()
        
        if any(k in pesan_mas.lower() for k in ['lanjut', 'resume', 'lagi']) and self.is_on_break:
            return await self.resume_session()
        
        # ========== HANDLE POSITION CHANGE ==========
        pos_change = self._handle_position_change(pesan_mas)
        if pos_change:
            return pos_change
        
        pos_confirm = self._handle_position_confirmation(pesan_mas)
        if pos_confirm:
            return pos_confirm
        
        # ========== HANDLE MAS CLIMAX ==========
        mas_climax = self._handle_mas_climax(pesan_mas)
        if mas_climax:
            return mas_climax
        
        # ========== UPDATE AROUSAL DARI PESAN ==========
        self._update_arousal_from_message(pesan_mas)
        
        # ========== BUILD ACTIVE SCENE ==========
        return self._build_active_scene(elapsed_minutes)
    
    def _update_arousal_from_message(self, pesan_mas: str):
        """Update arousal dari pesan Mas"""
        msg_lower = pesan_mas.lower()
        
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus', 'hebat']):
            self.character.emotional.add_stimulation("pujian Mas", 2)
        
        if any(k in msg_lower for k in ['cepat', 'kenceng', 'harder', 'faster']):
            self.character.emotional.add_stimulation("Mas minta kenceng", 3)
        
        if any(k in msg_lower for k in ['pegang', 'remas', 'sentuh']):
            self.character.emotional.add_stimulation("Mas pegang", 4)
        
        if any(k in msg_lower for k in ['sange', 'horny', 'panas']):
            self.character.emotional.add_stimulation("Mas juga sange", 5)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_status(self) -> str:
        """Dapatkan status sesi"""
        if not self.is_active:
            return "Tidak ada sesi aktif"
        
        elapsed = time.time() - self.start_time
        remaining = max(0, self.DURATION_SECONDS - elapsed)
        remaining_hours = remaining / 3600
        remaining_minutes = (remaining % 3600) / 60
        
        elapsed_hours = elapsed / 3600
        
        if self.is_on_break:
            break_elapsed = time.time() - self.break_start_time
            break_minutes = int(break_elapsed // 60)
            break_status = f"\n☕ Break: {break_minutes} menit"
        else:
            break_status = ""
        
        phase_names = {
            ServicePhase.GREETING: "👋 Menyapa",
            ServicePhase.SEX: "🔥 Sesi Aktif",
            ServicePhase.BREAK: "☕ Break",
            ServicePhase.COMPLETED: "✅ Selesai"
        }
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    🔥 PELACUR SESSION                         ║
╠══════════════════════════════════════════════════════════════╣
║ Durasi: {elapsed_hours:.1f} / {self.DURATION_HOURS} jam
║ Sisa: {remaining_hours:.0f} jam {remaining_minutes:.0f} menit
║ Fase: {phase_names.get(self.current_phase, 'Unknown')}
║ Posisi: {self.current_position}
╠══════════════════════════════════════════════════════════════╣
║ 💦 Mas Climax: {self.mas_climax_this_session}x
║ 💦 Role Climax: {self.role_climax_this_session}x
╠══════════════════════════════════════════════════════════════╣
║ {self.character.get_status()}
╚══════════════════════════════════════════════════════════════╝
"""
