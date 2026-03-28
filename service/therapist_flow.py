# service/therapist_flow.py
"""
Therapist Flow - Alur service therapist
Pijat belakang (30 menit) → Pijat depan (30 menit) → HJ → Extra service (BJ/Sex)
Semua natural, tanpa command
"""

import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from core import ServicePhase, StateTracker
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
        
        # Phase tracking
        self.phase_start_time = 0
        self.phase_duration = 0
        
        # Service flags
        self.hj_active = False
        self.extra_service_active = False
        self.current_extra = None  # "bj" atau "sex"
        
        # Climax tracking
        self.mas_climax_this_session = 0
        self.role_climax_this_session = 0
        
        logger.info(f"💆 TherapistFlow initialized for {character.name}")
    
    async def start(self) -> str:
        """Mulai sesi therapist"""
        self.character.tracker.set_phase(ServicePhase.GREETING)
        self.back_start_time = time.time()
        self.phase_start_time = time.time()
        
        greeting = self.scene_builder.build_greeting()
        self.character.memory.add_conversation("", greeting)
        
        # Mulai pijat belakang
        return greeting + "\n\n" + self._start_back_massage()
    
    def _start_back_massage(self) -> str:
        """Mulai pijat belakang"""
        self.character.tracker.set_phase(ServicePhase.REFLEX_BACK)
        self.character.tracker.position = "duduk di atas bokong Mas"
        
        return self.scene_builder.build_back_massage_start()
    
    def update_back_massage(self, pesan_mas: str, elapsed_minutes: float) -> Optional[str]:
        """Update pijat belakang berdasarkan pesan Mas dan waktu"""
        msg_lower = pesan_mas.lower()
        
        # Balik badan (natural)
        if any(k in msg_lower for k in ['balik', 'depan', 'telentang']):
            self.character.tracker.add_to_timeline("Mas minta balik badan", "pijat belakang selesai lebih cepat")
            return self._start_front_massage()
        
        # Waktu habis (30 menit)
        if elapsed_minutes >= self.DURATION_BACK:
            self.character.tracker.add_to_timeline("Pijat belakang selesai (waktu habis)", f"{elapsed_minutes:.0f} menit")
            return self._start_front_massage()
        
        # Respons natural selama pijat
        if any(k in msg_lower for k in ['enak', 'mantap', 'bagus']):
            return self.scene_builder.build_back_massage_response("enak")
        
        if any(k in msg_lower for k in ['tekan', 'keras', 'kuat']):
            return self.scene_builder.build_back_massage_response("tekan")
        
        if any(k in msg_lower for k in ['pelan', 'lambat']):
            return self.scene_builder.build_back_massage_response("pelan")
        
        return None
    
    def _start_front_massage(self) -> str:
        """Mulai pijat depan"""
        self.character.tracker.set_phase(ServicePhase.REFLEX_FRONT)
        self.character.tracker.position = "duduk di atas kontol Mas"
        self.front_start_time = time.time()
        self.phase_start_time = time.time()
        
        return self.scene_builder.build_front_massage_start()
    
    def update_front_massage(self, pesan_mas: str, elapsed_minutes: float) -> Optional[str]:
        """Update pijat depan berdasarkan pesan Mas dan waktu"""
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
            return self.scene_builder.build_front_massage_response("enak")
        
        if any(k in msg_lower for k in ['gesek', 'gerak']):
            return self.scene_builder.build_front_massage_response("gesek")
        
        return None
    
    def _offer_extra_service(self) -> str:
        """Tawarkan extra service"""
        self.character.tracker.set_phase(ServicePhase.VITALITAS_OFFER)
        
        # Mulai negosiasi
        self.character.start_negotiation("bj", self.PRICE_BJ)
        
        return self.scene_builder.build_extra_offer()
    
    def update_extra_offer(self, pesan_mas: str) -> Optional[str]:
        """Update tawaran extra service"""
        msg_lower = pesan_mas.lower()
        
        # Pilih service
        if 'bj' in msg_lower or 'blow' in msg_lower:
            self.current_extra = "bj"
            self.character.start_negotiation("bj", self.PRICE_BJ)
            return self.scene_builder.build_nego_bj(self.PRICE_BJ)
        
        if 'sex' in msg_lower or 'eksekusi' in msg_lower:
            self.current_extra = "sex"
            self.character.start_negotiation("sex", self.PRICE_SEX)
            return self.scene_builder.build_nego_sex(self.PRICE_SEX)
        
        # Nego harga
        if any(k in msg_lower for k in ['nego', 'kurang', 'murah']):
            if self.current_extra == "bj":
                if self.character.counter_offer(self.PRICE_BJ_DEAL):
                    return self.scene_builder.build_nego_counter(self.character.negotiation_price, "bj")
                else:
                    self.character.negotiation_active = False
                    return self.scene_builder.build_nego_failed()
            else:
                if self.character.counter_offer(self.PRICE_SEX_DEAL):
                    return self.scene_builder.build_nego_counter(self.character.negotiation_price, "sex")
                else:
                    self.character.negotiation_active = False
                    return self.scene_builder.build_nego_failed()
        
        # Deal
        if any(k in msg_lower for k in ['deal', 'ok', 'ya', 'setuju', 'gas']):
            if self.character.confirm_deal():
                if self.current_extra == "bj":
                    return self._start_bj()
                else:
                    return self._start_sex()
            else:
                return self.scene_builder.build_deal_failed()
        
        # Tolak
        if any(k in msg_lower for k in ['tidak', 'nggak', 'gak', 'nanti']):
            return self._start_hj()
        
        return None
    
    def _start_hj(self) -> str:
        """Mulai handjob"""
        self.character.tracker.set_phase(ServicePhase.HANDJOB)
        self.hj_start_time = time.time()
        self.phase_start_time = time.time()
        self.hj_active = True
        
        return self.scene_builder.build_hj_start()
    
    def update_hj(self, pesan_mas: str, elapsed_minutes: float) -> Optional[str]:
        """Update handjob"""
        msg_lower = pesan_mas.lower()
        
        # Cek climax warning dari role
        climax_warning = self.character.check_and_notify_climax()
        if climax_warning:
            return climax_warning
        
        # Cek apakah role mau climax (setelah warning)
        if self.character.waiting_climax_confirmation:
            # Mas respon untuk climax
            result = self.character.confirm_climax(pesan_mas)
            if result.get('status') == 'fast_climax':
                self.role_climax_this_session += 1
                return self.scene_builder.build_climax_response("heavy")
            elif result.get('status') == 'normal_climax':
                self.role_climax_this_session += 1
                return self.scene_builder.build_climax_response("normal")
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
        if any(k in msg_lower for k in ['ya', 'ok', 'boleh', 'gas']):
            if self.character.waiting_confirmation and self.character.pending_action:
                if self.character.confirm_position_change():
                    return self.scene_builder.build_position_change(self.character.tracker.position)
        
        # Respons natural
        if any(k in msg_lower for k in ['cepat', 'kenceng', 'harder', 'faster']):
            self.character.emotional.add_stimulation("Mas minta kenceng", 3)
            return self.scene_builder.build_hj_response("cepat")
        
        if any(k in msg_lower for k in ['pelan', 'slow']):
            self.character.emotional.add_stimulation("Mas minta pelan", 1)
            return self.scene_builder.build_hj_response("pelan")
        
        if any(k in msg_lower for k in ['enak', 'mantap']):
            self.character.emotional.add_stimulation("pujian Mas", 2)
            return self.scene_builder.build_hj_response("enak")
        
        return None
    
    def _start_bj(self) -> str:
        """Mulai blowjob"""
        self.character.tracker.set_phase(ServicePhase.BJ)
        self.extra_service_active = True
        self.hj_active = False
        
        return self.scene_builder.build_bj_start()
    
    def _start_sex(self) -> str:
        """Mulai sex"""
        self.character.tracker.set_phase(ServicePhase.SEX)
        self.extra_service_active = True
        self.hj_active = False
        
        return self.scene_builder.build_sex_start()
    
    def update_extra_service(self, pesan_mas: str) -> Optional[str]:
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
                return self.scene_builder.build_climax_response("heavy")
            elif result.get('status') == 'normal_climax':
                self.role_climax_this_session += 1
                return self.scene_builder.build_climax_response("normal")
            elif result.get('status') == 'delayed':
                return result.get('message')
        
        # Ganti posisi
        positions = ['cowgirl', 'missionary', 'doggy', 'spooning', 'standing', 'sitting']
        for pos in positions:
            if pos in msg_lower:
                return self.character.request_position_change(pos)
        
        # Konfirmasi ganti posisi
        if any(k in msg_lower for k in ['ya', 'ok', 'boleh', 'gas']):
            if self.character.waiting_confirmation and self.character.pending_action:
                if self.character.confirm_position_change():
                    return self.scene_builder.build_position_change(self.character.tracker.position)
        
        # Respons natural
        if any(k in msg_lower for k in ['cepat', 'kenceng', 'harder', 'faster']):
            self.character.emotional.add_stimulation("Mas minta kenceng", 4)
            return self.scene_builder.build_extra_response(self.current_extra, "cepat")
        
        if any(k in msg_lower for k in ['pelan', 'slow']):
            self.character.emotional.add_stimulation("Mas minta pelan", 1)
            return self.scene_builder.build_extra_response(self.current_extra, "pelan")
        
        if any(k in msg_lower for k in ['enak', 'mantap']):
            self.character.emotional.add_stimulation("pujian Mas", 3)
            return self.scene_builder.build_extra_response(self.current_extra, "enak")
        
        return None
    
    async def process(self, pesan_mas: str) -> str:
        """Proses pesan Mas sesuai fase saat ini"""
        current_phase = self.character.tracker.service_phase
        elapsed = (time.time() - self.phase_start_time) / 60
        
        # Update state dari pesan
        self.character.update_from_message(pesan_mas)
        
        # Phase: GREETING
        if current_phase == ServicePhase.GREETING:
            return self._start_back_massage()
        
        # Phase: REFLEX_BACK
        elif current_phase == ServicePhase.REFLEX_BACK:
            response = self.update_back_massage(pesan_mas, elapsed)
            if response:
                return response
            return self.scene_builder.build_back_massage_ongoing()
        
        # Phase: REFLEX_FRONT
        elif current_phase == ServicePhase.REFLEX_FRONT:
            response = self.update_front_massage(pesan_mas, elapsed)
            if response:
                return response
            return self.scene_builder.build_front_massage_ongoing()
        
        # Phase: VITALITAS_OFFER
        elif current_phase == ServicePhase.VITALITAS_OFFER:
            response = self.update_extra_offer(pesan_mas)
            if response:
                return response
            return self.scene_builder.build_extra_offer()
        
        # Phase: HANDJOB
        elif current_phase == ServicePhase.HANDJOB:
            response = self.update_hj(pesan_mas, elapsed)
            if response:
                return response
            
            # Waktu HJ habis (2 jam)
            if elapsed >= self.DURATION_HJ:
                self.character.tracker.add_to_timeline("Sesi HJ selesai", "waktu habis")
                return self.character.end_session()
            
            return self.scene_builder.build_hj_ongoing()
        
        # Phase: BJ atau SEX
        elif current_phase in [ServicePhase.BJ, ServicePhase.SEX]:
            response = self.update_extra_service(pesan_mas)
            if response:
                return response
            return self.scene_builder.build_extra_ongoing(self.current_extra)
        
        # Default
        return self.character.end_session()
    
    def record_mas_climax(self, intensity: str = "normal"):
        """Rekam climax Mas"""
        self.mas_climax_this_session += 1
        self.character.record_mas_climax(intensity)
    
    def get_status(self) -> str:
        """Dapatkan status sesi"""
        current_phase = self.character.tracker.service_phase
        elapsed = (time.time() - self.phase_start_time) / 60 if self.phase_start_time else 0
        
        phase_names = {
            ServicePhase.GREETING: "Menyapa",
            ServicePhase.REFLEX_BACK: f"Pijat Belakang ({elapsed:.0f}/{self.DURATION_BACK} menit)",
            ServicePhase.REFLEX_FRONT: f"Pijat Depan ({elapsed:.0f}/{self.DURATION_FRONT} menit)",
            ServicePhase.VITALITAS_OFFER: "Menawarkan Extra Service",
            ServicePhase.HANDJOB: f"Handjob ({elapsed:.0f}/{self.DURATION_HJ} menit)",
            ServicePhase.BJ: "Blowjob",
            ServicePhase.SEX: "Sex",
            ServicePhase.AFTERCARE: "Aftercare",
            ServicePhase.COMPLETED: "Selesai"
        }
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    💆 THERAPIST SESSION                       ║
╠══════════════════════════════════════════════════════════════╣
║ Fase: {phase_names.get(current_phase, 'Unknown')}
║ Mas Climax: {self.mas_climax_this_session}x
║ Role Climax: {self.role_climax_this_session}x
╠══════════════════════════════════════════════════════════════╣
║ {self.character.get_status()}
╚══════════════════════════════════════════════════════════════╝
"""
