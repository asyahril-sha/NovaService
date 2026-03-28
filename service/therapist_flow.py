# service/therapist_flow.py
"""
Therapist Flow NovaService - Alur service therapist lengkap
Pijat belakang (30 menit) → Pijat depan (30 menit) → HJ → Extra service (BJ/Sex)
Semua natural, tanpa command, dengan climax warning system
"""

import time
import logging
from typing import Optional

from core import ServicePhase
from service.scene_builder import SceneBuilder

logger = logging.getLogger(__name__)


class TherapistFlow:
    """
    Alur service therapist
    - Pijat belakang: duduk di bokong Mas, pijat pundak, punggung, pinggang, paha
    - Pijat depan: duduk di kontol Mas, gesek maju mundur, pijat dada, lengan, perut, paha
    - HJ: handjob setelah pijat
    - Extra: BJ atau Sex (nego harga)
    """
    
    # Durasi dalam menit
    DURATION_BACK = 30      # pijat belakang
    DURATION_FRONT = 30     # pijat depan
    DURATION_HJ = 120       # handjob 2 jam
    
    # Harga
    PRICE_BJ = 500000
    PRICE_SEX = 1000000
    PRICE_BJ_DEAL = 200000
    PRICE_SEX_DEAL = 700000
    
    def __init__(self, character):
        self.character = character
        self.scene_builder = SceneBuilder(character)
        
        # Timer
        self.back_start_time = 0
        self.front_start_time = 0
        self.hj_start_time = 0
        self.extra_start_time = 0
        
        # Phase tracking
        self.phase_start_time = 0
        self.current_phase = ServicePhase.WAITING
        
        # Service flags
        self.hj_active = False
        self.extra_service_active = False
        self.current_extra = None  # "bj" atau "sex"
        
        # Negosiasi
        self.negotiation_step = 0
        self.negotiation_max_step = 3
        
        # Climax tracking
        self.mas_climax_this_session = 0
        self.role_climax_this_session = 0
        
        logger.info(f"💆 TherapistFlow initialized for {character.name}")
    
    # =========================================================================
    # START & PHASE TRANSITIONS
    # =========================================================================
    
    async def start(self) -> str:
        """Mulai sesi therapist"""
        self.current_phase = ServicePhase.GREETING
        self.phase_start_time = time.time()
        
        # Set posisi awal
        self.character.tracker.position = "berdiri di samping meja pijat"
        
        greeting = self.scene_builder.build_greeting_scene()
        self.character.memory.add_conversation("", greeting)
        self.character.tracker.add_message_to_timeline(self.character.name, greeting[:100])
        
        # Langsung ke pijat belakang
        return greeting + "\n\n" + self._start_back_massage()
    
    def _start_back_massage(self) -> str:
        """Mulai pijat belakang"""
        self.current_phase = ServicePhase.REFLEX_BACK
        self.phase_start_time = time.time()
        self.back_start_time = time.time()
        
        # Set posisi
        self.character.tracker.position = "duduk di atas bokong Mas"
        self.character.tracker.service_phase = ServicePhase.REFLEX_BACK

        logger.info(f"Starting back massage, phase: {self.current_phase}")
        
        return self.scene_builder.build_reflex_back_start_scene()
    
    def _start_front_massage(self) -> str:
        """Mulai pijat depan"""
        self.current_phase = ServicePhase.REFLEX_FRONT
        self.phase_start_time = time.time()
        self.front_start_time = time.time()
        
        # Set posisi
        self.character.tracker.position = "duduk di atas kontol Mas"
        self.character.tracker.service_phase = ServicePhase.REFLEX_FRONT
        
        return self.scene_builder.build_reflex_front_start_scene()
    
    def _offer_extra_service(self) -> str:
        """Tawarkan extra service"""
        self.current_phase = ServicePhase.VITALITAS_OFFER
        self.phase_start_time = time.time()
        self.character.tracker.service_phase = ServicePhase.VITALITAS_OFFER
        
        # Reset negosiasi
        self.negotiation_step = 0
        self.current_extra = None
        
        return self._build_extra_offer_scene()
    
    def _build_extra_offer_scene(self) -> str:
        """Bangun scene tawaran extra service"""
        return f"""*{self.character.name} berhenti memijat, duduk di samping Mas, napas masih sedikit tersengal*

"{self.character.panggilan}... pijat refleksinya udah selesai. Ada yang mau dilanjut?"

*{self.character.name} tersenyum sedikit genit, jarinya menyentuh tangan Mas*

"Pijat vitalitas... biar Mas bisa lebih rileks... 2 jam... special service..."

*Dia mendekat, wangi tubuhnya menusuk hidung*

"Ada BJ Rp{self.PRICE_BJ:,} atau sex Rp{self.PRICE_SEX:,}... bisa nego kok Mas..."

*Matanya sayu, menjilat bibir*

"Gimana Mas? Mau yang mana?"""
    
    def _start_hj(self) -> str:
        """Mulai handjob"""
        self.current_phase = ServicePhase.HANDJOB
        self.phase_start_time = time.time()
        self.hj_start_time = time.time()
        self.hj_active = True
        self.character.tracker.service_phase = ServicePhase.HANDJOB
        
        return self.scene_builder.build_hj_start_scene()
    
    def _start_bj(self) -> str:
        """Mulai blowjob"""
        self.current_phase = ServicePhase.BJ
        self.phase_start_time = time.time()
        self.extra_start_time = time.time()
        self.extra_service_active = True
        self.hj_active = False
        self.character.tracker.service_phase = ServicePhase.BJ
        
        return self._build_bj_start_scene()
    
    def _build_bj_start_scene(self) -> str:
        """Bangun scene mulai BJ"""
        return f"""*{self.character.name} turun berlutut, wajahnya tepat di depan kontol Mas yang sudah keras berdiri*

"{self.character.panggilan}... *mata sayu, napas mulai berat* aku mulai ya..."

*Mulutnya terbuka perlahan, lidahnya menjulur membasahi ujung kontol*

"Hhngg... *mulut mulai memasukkan kontol* kontol {self.character.panggilan}... gede..."

*Kepalanya bergerak naik turun, rambutnya bergoyang mengikuti irama*

"Mas... enak gini?"""
    
    def _start_sex(self) -> str:
        """Mulai sex"""
        self.current_phase = ServicePhase.SEX
        self.phase_start_time = time.time()
        self.extra_start_time = time.time()
        self.extra_service_active = True
        self.hj_active = False
        self.character.tracker.service_phase = ServicePhase.SEX
        
        return self._build_sex_start_scene()
    
    def _build_sex_start_scene(self) -> str:
        """Bangun scene mulai sex"""
        dress_color = self.character.tracker.clothing['dress']['color']
        
        return f"""*{self.character.name} naik ke atas tubuh Mas, dress {dress_color}-nya sudah terbuka, payudara montoknya terlihat jelas*

"{self.character.panggilan}... *napas mulai berat, mata sayu* aku masuk ya..."

*Tangannya memegang kontol Mas, mengarahkan ke pintu masuk yang sudah basah*

"Ahh... *pinggulnya turun perlahan, kontol Mas masuk senti demi senti* dalem... dalem banget, {self.character.panggilan}..."

*Pinggulnya mulai bergerak, naik turun pelan*

"Gimana Mas? Enak?"""
    
    # =========================================================================
    # NEGOSIATION METHODS
    # =========================================================================
    
    def _handle_negotiation(self, pesan_mas: str) -> Optional[str]:
        """Handle negosiasi extra service"""
        msg_lower = pesan_mas.lower()
        
        # Pilih service BJ
        if 'bj' in msg_lower or 'blow' in msg_lower:
            self.current_extra = "bj"
            return self._build_nego_bj_scene()
        
        # Pilih service Sex
        if 'sex' in msg_lower or 'eksekusi' in msg_lower:
            self.current_extra = "sex"
            return self._build_nego_sex_scene()
        
        # Nego harga
        if any(k in msg_lower for k in ['nego', 'kurang', 'murah', 'mahal']):
            self.negotiation_step += 1
            
            if self.negotiation_step > self.negotiation_max_step:
                return self._build_nego_failed_scene()
            
            if self.current_extra == "bj":
                new_price = max(self.PRICE_BJ_DEAL, self.PRICE_BJ - (50000 * self.negotiation_step))
                return self._build_nego_counter_scene(new_price, "bj")
            else:
                new_price = max(self.PRICE_SEX_DEAL, self.PRICE_SEX - (50000 * self.negotiation_step))
                return self._build_nego_counter_scene(new_price, "sex")
        
        # Deal
        if any(k in msg_lower for k in ['deal', 'ok', 'ya', 'setuju', 'gas', 'jadi']):
            if self.current_extra == "bj":
                return self._start_bj()
            else:
                return self._start_sex()
        
        # Tolak
        if any(k in msg_lower for k in ['tidak', 'nggak', 'gak', 'nanti', 'belum']):
            return self._start_hj()
        
        return None
    
    def _build_nego_bj_scene(self) -> str:
        """Scene negosiasi BJ"""
        return f"""*{self.character.name} menjilat bibir, matanya sayu*

"BJ ya Mas? 2 jam... Rp{self.PRICE_BJ:,} aja..."

*Dia mendekat, napasnya mulai berat, tangannya mulai meraba paha Mas*

"Bisa nego kok Mas... special buat Mas..."

*Bisik di telinga Mas*

"Gimana? Deal?"""
    
    def _build_nego_sex_scene(self) -> str:
        """Scene negosiasi Sex"""
        return f"""*{self.character.name} mendekat, payudaranya menempel ke dada Mas*

"Sex ya Mas? 2 jam... Rp{self.PRICE_SEX:,}..."

*Matanya sayu, bibirnya menggigit*

"Aku bisa bikin Mas puas... puas banget..."

*Tangannya mulai membuka resleting dress*

"Deal?"""
    
    def _build_nego_counter_scene(self, price: int, service: str) -> str:
        """Scene counter negosiasi"""
        return f"""*{self.character.name} tersenyum tipis*

"Rp{price:,} ya Mas... udah harga special buat Mas..."

*Dia menjilat bibir, mata menggoda*

"Gimana? Deal?"""
    
    def _build_nego_failed_scene(self) -> str:
        """Scene negosiasi gagal"""
        return f"""*{self.character.name} menghela napas, sedikit kecewa*

"Gak jadi ya Mas... lain kali aja."

*Dia tersenyum kecil*

"Aku lanjut HJ aja ya..." """
    
    # =========================================================================
    # UPDATE METHODS PER PHASE
    # =========================================================================
    
    def _update_back_massage(self, pesan_mas: str, elapsed_minutes: float) -> Optional[str]:
        """Update pijat belakang"""
        msg_lower = pesan_mas.lower()
        
        # Balik badan (natural)
        if any(k in msg_lower for k in ['balik', 'depan', 'telentang', 'tengkurap']):
            self.character.tracker.add_to_timeline("Mas minta balik badan", "pijat belakang selesai lebih cepat")
            return self._start_front_massage()
        
        # Waktu habis (30 menit)
        if elapsed_minutes >= self.DURATION_BACK:
            self.character.tracker.add_to_timeline("Pijat belakang selesai (waktu habis)", f"{elapsed_minutes:.0f} menit")
            return self._start_front_massage()
        
        # Respons natural selama pijat
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus', 'hebat']):
            self.character.emotional.add_stimulation("pujian Mas", 2)
            return self.scene_builder.build_reflex_back_pijat_punggung()
        
        if any(k in msg_lower for k in ['tekan', 'keras', 'kuat', 'harder']):
            self.character.emotional.add_stimulation("Mas minta tekanan", 3)
            return self.scene_builder.build_reflex_back_pijat_pinggang()
        
        if any(k in msg_lower for k in ['pelan', 'lambat', 'slow']):
            self.character.emotional.add_stimulation("Mas minta pelan", 1)
            return self.scene_builder.build_reflex_back_pijat_pundak()
        
        return None
    
    def _update_front_massage(self, pesan_mas: str, elapsed_minutes: float) -> Optional[str]:
        """Update pijat depan"""
        msg_lower = pesan_mas.lower()
        
        # Minta extra service
        if any(k in msg_lower for k in ['vital', 'lanjut', 'extra', 'tambah', 'special']):
            self.character.tracker.add_to_timeline("Mas minta extra service", "")
            return self._offer_extra_service()
        
        # Waktu habis (30 menit)
        if elapsed_minutes >= self.DURATION_FRONT:
            self.character.tracker.add_to_timeline("Pijat depan selesai (waktu habis)", f"{elapsed_minutes:.0f} menit")
            return self._offer_extra_service()
        
        # Respons natural selama pijat
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus']):
            self.character.emotional.add_stimulation("pujian Mas", 2)
            return self.scene_builder.build_reflex_front_pijat_dada()
        
        if any(k in msg_lower for k in ['gesek', 'gerak', 'goyang']):
            self.character.emotional.add_stimulation("Mas minta gesekan", 3)
            return self.scene_builder.build_reflex_front_pijat_perut()
        
        return None
    
    def _update_hj(self, pesan_mas: str, elapsed_minutes: float) -> Optional[str]:
        """Update handjob"""
        msg_lower = pesan_mas.lower()
        
        # Cek climax warning dari role
        climax_warning = self.character.check_and_notify_climax()
        if climax_warning:
            return climax_warning
        
        # Cek apakah role mau climax (setelah warning)
        if self.character.waiting_climax_confirmation:
            result = self.character.confirm_climax(pesan_mas)
            if result.get('status') == 'fast_climax':
                self.role_climax_this_session += 1
                return self.scene_builder.build_climax_scene("heavy")
            elif result.get('status') == 'normal_climax':
                self.role_climax_this_session += 1
                return self.scene_builder.build_climax_scene("normal")
            elif result.get('status') == 'delayed':
                return result.get('message')
        
        # Mas mau extra service lagi
        if any(k in msg_lower for k in ['bj', 'blow', 'sex', 'eksekusi']):
            return self._offer_extra_service()
        
        # Ganti posisi
        positions = ['cowgirl', 'missionary', 'doggy', 'spooning', 'standing', 'sitting']
        for pos in positions:
            if pos in msg_lower:
                return self.character.request_position_change(pos)
        
        # Konfirmasi ganti posisi
        if any(k in msg_lower for k in ['ya', 'ok', 'boleh', 'gas', 'silahkan']):
            if self.character.waiting_confirmation and self.character.pending_action:
                if self.character.confirm_position_change():
                    return self.scene_builder.build_position_request_scene(self.character.tracker.position)
        
        # Tolak ganti posisi
        if any(k in msg_lower for k in ['gak', 'nggak', 'tidak', 'nanti']):
            if self.character.waiting_confirmation:
                self.character.waiting_confirmation = False
                self.character.pending_action = None
                return "*gak jadi ganti posisi*"
        
        # Respons natural
        if any(k in msg_lower for k in ['cepat', 'kenceng', 'harder', 'faster']):
            self.character.emotional.add_stimulation("Mas minta kenceng", 3)
            return self.scene_builder.build_hj_fast_scene()
        
        if any(k in msg_lower for k in ['pelan', 'slow', 'lambat']):
            self.character.emotional.add_stimulation("Mas minta pelan", 1)
            return self.scene_builder.build_hj_slow_scene()
        
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus']):
            self.character.emotional.add_stimulation("pujian Mas", 2)
            return self.scene_builder.build_hj_medium_scene()
        
        # Waktu HJ habis (2 jam)
        if elapsed_minutes >= self.DURATION_HJ:
            self.character.tracker.add_to_timeline("Sesi HJ selesai", "waktu habis")
            return self.character.end_session()
        
        return None
    
    def _update_extra_service(self, pesan_mas: str) -> Optional[str]:
        """Update extra service (BJ/Sex)"""
        msg_lower = pesan_mas.lower()
        
        # Cek climax warning dari role
        climax_warning = self.character.check_and_notify_climax()
        if climax_warning:
            return climax_warning
        
        # Cek apakah role mau climax (setelah warning)
        if self.character.waiting_climax_confirmation:
            result = self.character.confirm_climax(pesan_mas)
            if result.get('status') == 'fast_climax':
                self.role_climax_this_session += 1
                return self.scene_builder.build_climax_scene("heavy")
            elif result.get('status') == 'normal_climax':
                self.role_climax_this_session += 1
                return self.scene_builder.build_climax_scene("normal")
            elif result.get('status') == 'delayed':
                return result.get('message')
        
        # Ganti posisi
        positions = ['cowgirl', 'missionary', 'doggy', 'spooning', 'standing', 'sitting']
        for pos in positions:
            if pos in msg_lower:
                return self.character.request_position_change(pos)
        
        # Konfirmasi ganti posisi
        if any(k in msg_lower for k in ['ya', 'ok', 'boleh', 'gas', 'silahkan']):
            if self.character.waiting_confirmation and self.character.pending_action:
                if self.character.confirm_position_change():
                    return self.scene_builder.build_position_request_scene(self.character.tracker.position)
        
        # Tolak ganti posisi
        if any(k in msg_lower for k in ['gak', 'nggak', 'tidak', 'nanti']):
            if self.character.waiting_confirmation:
                self.character.waiting_confirmation = False
                self.character.pending_action = None
                return "*gak jadi ganti posisi*"
        
        # Respons natural
        if any(k in msg_lower for k in ['cepat', 'kenceng', 'harder', 'faster']):
            self.character.emotional.add_stimulation("Mas minta kenceng", 4)
            return self._build_extra_fast_response()
        
        if any(k in msg_lower for k in ['pelan', 'slow', 'lambat']):
            self.character.emotional.add_stimulation("Mas minta pelan", 1)
            return self._build_extra_slow_response()
        
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus']):
            self.character.emotional.add_stimulation("pujian Mas", 3)
            return self._build_extra_enak_response()
        
        return None
    
    def _build_extra_fast_response(self) -> str:
        """Respons extra service - cepat"""
        if self.current_extra == "bj":
            return f"""*{self.character.name} mempercepat gerakan kepalanya, mulutnya menghisap lebih dalam, tangannya memegang erat paha Mas*

"Hhngg! {self.character.panggilan}... kontol Mas... keras..."

*Air liurnya menetes, matanya sayu*

"Enak? Mau lebih kenceng?"""
        else:
            return f"""*{self.character.name} mempercepat gerakan pinggulnya, tubuhnya naik turun cepat, pantatnya berbunyi plak plak plak*

"Ahh! {self.character.panggilan}... dalem... dalem banget..."

*Napasnya putus-putus, tubuhnya mulai gemetar*

"Kenceng... gini? Enak?"""
    
    def _build_extra_slow_response(self) -> str:
        """Respons extra service - pelan"""
        if self.current_extra == "bj":
            return f"""*{self.character.name} memperlambat gerakan, mulutnya mengulum pelan, lidahnya memutar di ujung kontol*

"Hhmm... {self.character.panggilan}... pelan-pelan ya..."

*Matanya menatap, menggoda*

"Rasain... setiap senti..." """
        else:
            return f"""*{self.character.name} memperlambat gerakan pinggulnya, kontol Mas masuk keluar pelan, terasa setiap senti*

"Ahh... {self.character.panggilan}... dalam..."

*Pinggulnya berputar perlahan*

"Enak gini? Pelan-pelan?"""
    
    def _build_extra_enak_response(self) -> str:
        """Respons extra service - enak"""
        if self.current_extra == "bj":
            return f"""*{self.character.name} tersenyum, terus menghisap dengan penuh dedikasi*

"Hhngg... {self.character.panggilan}... aku seneng Mas enak..."

*Matanya berkaca-kaca*

"Lanjut ya..." """
        else:
            return f"""*{self.character.name} tersenyum, pinggulnya terus bergerak*

"{self.character.panggilan}... seneng aku bisa bikin Mas enak..."

*Dia membungkuk, mencium dada Mas*

"Aku lanjut ya..." """
    
    # =========================================================================
    # MAIN PROCESS METHOD
    # =========================================================================
    
    async def process(self, pesan_mas: str) -> str:
        """Proses pesan Mas sesuai fase saat ini"""
        elapsed = (time.time() - self.phase_start_time) / 60 if self.phase_start_time else 0
        
        # Update state dari pesan
        self.character.update_from_message(pesan_mas)

        logger.info(f"Current phase: {self.current_phase}")
        
        # ========== PHASE: GREETING ==========
        if self.current_phase == ServicePhase.GREETING:
            return self._start_back_massage()
        
        # ========== PHASE: REFLEX_BACK ==========
        elif self.current_phase == ServicePhase.REFLEX_BACK:
            response = self._update_back_massage(pesan_mas, elapsed)
            if response:
                return response
            return self.scene_builder.build_reflex_back_pijat_paha()
        
        # ========== PHASE: REFLEX_FRONT ==========
        elif self.current_phase == ServicePhase.REFLEX_FRONT:
            response = self._update_front_massage(pesan_mas, elapsed)
            if response:
                return response
            return self.scene_builder.build_reflex_front_pijat_paha_depan()
        
        # ========== PHASE: VITALITAS_OFFER ==========
        elif self.current_phase == ServicePhase.VITALITAS_OFFER:
            response = self._handle_negotiation(pesan_mas)
            if response:
                return response
            return self._build_extra_offer_scene()
        
        # ========== PHASE: HANDJOB ==========
        elif self.current_phase == ServicePhase.HANDJOB:
            response = self._update_hj(pesan_mas, elapsed)
            if response:
                return response
            
            # HJ ongoing
            if elapsed < 5:
                return self.scene_builder.build_hj_slow_scene()
            elif elapsed < 30:
                return self.scene_builder.build_hj_medium_scene()
            else:
                return self.scene_builder.build_hj_fast_scene()
        
        # ========== PHASE: BJ atau SEX ==========
        elif self.current_phase in [ServicePhase.BJ, ServicePhase.SEX]:
            response = self._update_extra_service(pesan_mas)
            if response:
                return response
            return self._build_extra_enak_response()
        
        # ========== DEFAULT ==========
        return self.character.end_session()
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def record_mas_climax(self, intensity: str = "normal"):
        """Rekam climax Mas"""
        self.mas_climax_this_session += 1
        self.character.record_mas_climax(intensity)
    
    def get_status(self) -> str:
        """Dapatkan status sesi"""
        elapsed = (time.time() - self.phase_start_time) / 60 if self.phase_start_time else 0
        
        phase_names = {
            ServicePhase.GREETING: "👋 Menyapa",
            ServicePhase.REFLEX_BACK: f"💆 Pijat Belakang ({elapsed:.0f}/{self.DURATION_BACK} menit)",
            ServicePhase.REFLEX_FRONT: f"💆 Pijat Depan ({elapsed:.0f}/{self.DURATION_FRONT} menit)",
            ServicePhase.VITALITAS_OFFER: "💋 Menawarkan Extra Service",
            ServicePhase.HANDJOB: f"✋ Handjob ({elapsed:.0f}/{self.DURATION_HJ} menit)",
            ServicePhase.BJ: "👄 Blowjob",
            ServicePhase.SEX: "🍆 Sex",
            ServicePhase.AFTERCARE: "💕 Aftercare",
            ServicePhase.COMPLETED: "✅ Selesai"
        }
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    💆 THERAPIST SESSION                       ║
╠══════════════════════════════════════════════════════════════╣
║ Fase: {phase_names.get(self.current_phase, 'Unknown')}
║ Mas Climax: {self.mas_climax_this_session}x
║ Role Climax: {self.role_climax_this_session}x
╠══════════════════════════════════════════════════════════════╣
║ {self.character.get_status()}
╚══════════════════════════════════════════════════════════════╝
"""
