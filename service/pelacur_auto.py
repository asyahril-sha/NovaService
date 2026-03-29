# service/pelacur_auto.py
"""
Pelacur Auto Phase - BJ (30 menit) dan Kissing (30 menit)
Auto send scene setiap 30 detik
"""

import asyncio
import time
import logging
import re
from typing import Optional

from service.pelacur_core import PelacurCore

logger = logging.getLogger(__name__)


class PelacurAuto(PelacurCore):
    """
    Auto phase untuk Pelacur Flow
    - BJ: 30 menit, auto scene setiap 30 detik
    - Kissing: 30 menit, auto scene setiap 30 detik
    """
    def _clean_markdown(self, text: str) -> str:
        """Bersihkan markdown yang tidak lengkap sebelum dikirim ke Telegram"""
        import re
        
        asterisk_count = text.count('*')
        underscore_count = text.count('_')
    
        if asterisk_count % 2 != 0:
            text = re.sub(r'\*([^*]*)$', r'\1', text)
    
        if underscore_count % 2 != 0:
            text = re.sub(r'_([^_]*)$', r'\1', text)
    
        special_chars = ['[', ']', '(', ')', '\\', '`']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
    
        return text
    
    # =========================================================================
    # AUTO SEND TASK MANAGEMENT
    # =========================================================================
    
    async def _start_auto_send_task(self):
        """Mulai background task untuk auto-send scene"""
        if self.auto_send_running:
            return
        
        self.auto_send_running = True
        self.auto_send_task = asyncio.create_task(self._auto_send_loop())
        logger.info(f"🚀 Auto-send task started for {self.current_phase_name}")
    
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
        """Loop background untuk auto-send scene"""
    
        # ✅ TUNGGU CALLBACK SIAP (max 5 detik)
        wait_count = 0
        while not self._send_callback and wait_count < 50:  # 5 detik
            await asyncio.sleep(0.1)
            wait_count += 1
    
        if not self._send_callback:
            logger.error("❌ Send callback not available after waiting!")
            return
    
        logger.info("✅ Send callback ready, starting auto-send loop")
    
        while self.auto_send_running and self.is_active and self.auto_send_active:
            try:
                if self.waiting_for_response:
                    await asyncio.sleep(1)
                    continue
            
                if self._is_auto_phase_complete():
                    logger.info(f"✅ Auto phase {self.current_phase_name} completed")
                    await self._stop_auto_send_task()
                    await self._on_auto_phase_complete()
                    break
            
                if self._should_send_next_auto_scene():
                    scene = await self._generate_current_auto_scene()
                    if scene:
                        logger.info(f"📤 Auto-send scene #{self.scene_count}")
                    
                        if self._send_callback:
                            try:
                                await self._send_callback(scene)
                                logger.info(f"✅ Scene #{self.scene_count} sent")
                            except Exception as e:
                                logger.error(f"❌ Send callback failed: {e}")
                        else:
                            logger.error("❌ No send callback available!")
            
                await asyncio.sleep(1)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-send loop error: {e}")
                await asyncio.sleep(5)
    
    async def _generate_current_auto_scene(self) -> str:
        """Generate scene untuk auto phase saat ini"""
        if self.current_phase_name == "bj":
            return await self._generate_bj_auto_scene()
        elif self.current_phase_name == "kissing":
            return await self._generate_kissing_auto_scene()
        return None
    
    async def _on_auto_phase_complete(self):
        """Handler saat auto phase selesai"""
        self.auto_send_active = False
        
        if self.current_phase_name == "bj":
            # BJ selesai, lanjut ke kissing
            logger.info("BJ completed, moving to kissing phase")
            await self._start_kissing_auto()
        elif self.current_phase_name == "kissing":
            # Kissing selesai, lanjut ke foreplay manual
            logger.info("Kissing completed, moving to foreplay manual")
            self.auto_send_active = False
            self.current_phase_name = "foreplay_mas"
            self.waiting_for_response = True
            self.waiting_for_type = "foreplay"
            self.waiting_start_time = time.time()
            
            foreplay_msg = await self._build_foreplay_request()
            if hasattr(self.character, 'send_message'):
                await self.character.send_message(foreplay_msg)
    
    # =========================================================================
    # BJ AUTO PHASE
    # =========================================================================
    
    async def _start_bj_auto(self) -> str:
        """Mulai fase BJ auto (30 menit)"""
        logger.info("🔥 Starting BJ auto phase (30 minutes)")
        
        self.current_phase_name = "bj"
        self.phase_start_time = time.time()
        self.scene_count = 0
        self.total_scenes = self.BJ_SCENES
        self.auto_send_active = True
        self.waiting_for_response = False
        
        # Update posisi di memory
        self.memory.update_position("berlutut di antara kaki Mas", "bj")
        self.memory.update_movement("menghisap", "sedang")
        
        # Update body state
        self.memory.update_body_state(napas='stabil', suhu='normal')
        
        # Start auto-send task
        await self._start_auto_send_task()
        
        # Generate scene pertama
        first_scene = await self._generate_bj_auto_scene()
        
        # Simpan ke memory
        self.memory.record_action("start_bj", first_scene)
        self.memory.update_from_response(first_scene, "bj")
        
        return first_scene
    
    async def _generate_bj_auto_scene(self) -> str:
        """Generate scene BJ auto menggunakan AI"""
        scene_num = self.scene_count
        total_scenes = self.BJ_SCENES

        # ✅ Dapatkan memory context TERLEBIH DAHULU
        memory_context = self.memory.get_full_context()

        # ✅ TAMBAHKAN PENGINGAT POSISI
        position_reminder = """
🔴🔴🔴 PERINGATAN POSISI (WAJIB!) 🔴🔴🔴

KAMU SEDANG BERLUTUT DI DEPAN MAS ATAU TENGKURAP DIBAWAH KAKI MAS DI KASUR
AKTIVITAS: MENGHISAP KONTOL MAS (BLOWJOB)

JANGAN BERUBAH POSISI!
JANGAN DUDUK DI ATAS!
JANGAN SEBUT "NAIK TURUN" atau "COWGIRL"!

FOKUS: GERAKAN MULUT, LIDAH, HISAPAN
"""

        # Build prompt menggunakan prompt builder
        prompt = self.prompt_builder.build_auto_prompt("bj", scene_num, total_scenes)
    
        full_prompt = f"""
{memory_context}

{position_reminder}

═══════════════════════════════════════════════════════════════
INSTRUKSI KHUSUS UNTUK SCENE INI:
═══════════════════════════════════════════════════════════════
- Ini adalah scene ke-{scene_num} dari {total_scenes} scene BJ
- Waktu sudah berjalan {self._get_phase_elapsed() // 60} menit
- {self.memory.get_position_context()}
- {self.memory.get_movement_context()}

{prompt}

RESPON KAMU (narasi BJ, bukan jawaban AI):
"""
    
        scene = await self._generate_scene(full_prompt)
        scene = self._clean_markdown(scene)
        return scene
    
    # =========================================================================
    # KISSING AUTO PHASE
    # =========================================================================
    
    async def _start_kissing_auto(self) -> str:
        """Mulai fase kissing auto (30 menit)"""
        logger.info("💋 Starting Kissing auto phase (30 minutes)")
        
        self.current_phase_name = "kissing"
        self.phase_start_time = time.time()
        self.scene_count = 0
        self.total_scenes = self.KISSING_SCENES
        self.auto_send_active = True
        self.waiting_for_response = False
        
        # Update posisi di memory
        self.memory.update_position("duduk di atas kontol Mas", "kissing")
        self.memory.update_movement("menggesek", "sedang")
        
        # Update body state
        self.memory.update_body_state(napas='berat', suhu='hangat')
        self.memory.update_feeling('sange', 50)
        
        # Start auto-send task
        await self._start_auto_send_task()
        
        # Generate scene pertama
        first_scene = await self._generate_kissing_auto_scene()
        
        # Simpan ke memory
        self.memory.record_action("start_kissing", first_scene)
        self.memory.update_from_response(first_scene, "kissing")
        
        return first_scene
    
    async def _generate_kissing_auto_scene(self) -> str:
        """Generate scene kissing auto menggunakan AI"""
        scene_num = self.scene_count
        total_scenes = self.KISSING_SCENES

        memory_context = self.memory.get_full_context()

        position_reminder = """
🔴🔴🔴 PERINGATAN POSISI (WAJIB!) 🔴🔴🔴

KAMU SEDANG DUDUK DI PANGKUAN MAS
AKTIVITAS: MENGESEK MEMEK + KISSING

JANGAN MASUKIN KONTOL MAS KEDALAM MEMEK! HANYA GESEKAN!
JANGAN LANGSUNG COWGIRL!
FOKUS: GESEKAN PINGGUL, CIUMAN, NAPAS, DESAH, BUAT MAS HORNY, KAMU BEBAS ORGASM
"""

        prompt = self.prompt_builder.build_auto_prompt("kissing", scene_num, total_scenes)
    
        full_prompt = f"""
{memory_context}

{position_reminder}

═══════════════════════════════════════════════════════════════
INSTRUKSI KHUSUS UNTUK SCENE INI:
═══════════════════════════════════════════════════════════════
- Ini adalah scene ke-{scene_num} dari {total_scenes} scene kissing
- Waktu sudah berjalan {self._get_phase_elapsed() // 60} menit
- {self.memory.get_position_context()}
- {self.memory.get_movement_context()}

{prompt}

RESPON KAMU (narasi kissing + gesekan, bukan jawaban AI):
"""
    
        scene = await self._generate_scene(full_prompt)
        scene = self._clean_markdown(scene)
        return scene
    
    # =========================================================================
    # FOREPLAY REQUEST (Transisi ke manual)
    # =========================================================================
    
    async def _build_foreplay_request(self) -> str:
        """Bangun pesan minta Mas foreplay (natural)"""
        # Update perasaan
        self.memory.update_feeling('pengen disentuh', 70)
        
        return f"""*{self.character.name} berhenti bergerak, napasnya masih tersengal. Tubuhnya masih hangat, matanya sayu menatap Mas.*

"{self.character.panggilan}... sekarang giliran Mas... aku mau Mas..."

*Dia merebahkan diri, kaki sedikit terbuka, tangan terbuka lebar*

"Lakukan apa yang Mas mau ke aku... aku tunggu..."

*Napasnya masih berat, dadanya naik turun*

"Mas... ayo..." """
    
    # =========================================================================
    # TRANSITION MESSAGES
    # =========================================================================
    
    async def _build_transition_to_cowgirl(self) -> str:
        """Bangun pesan transisi dari foreplay ke cowgirl"""
        return f"""*{self.character.name} menggeliat, tubuhnya panas, napas tersengal*

"{self.character.panggilan}... aku mau naik... boleh?"

*Dia sudah tidak sabar, langsung duduk di atas kontol Mas*

"Ahh... masuk..." """
    
    async def _build_transition_to_cunnilingus(self) -> str:
        """Bangun pesan transisi dari cowgirl ke cunnilingus"""
        return f"""*{self.character.name} berhenti bergerak, tubuhnya lemas di atas Mas*

"{self.character.panggilan}... sekarang Mas... jilat aku..."

*Dia berbaring, kaki terbuka lebar*

"Aku mau Mas..." """
    
    async def _build_transition_to_missionary(self) -> str:
        """Bangun pesan transisi dari cunnilingus ke missionary"""
        return f"""*{self.character.name} menggeliat, memeknya basah, napas putus-putus*

"{self.character.panggilan}... sekarang Mas di atas... aku mau Mas masuk..."

*Dia menarik tangan Mas, kaki terbuka lebar*

"Ayo Mas..." """
    
    async def _build_transition_to_doggy(self) -> str:
        """Bangun pesan transisi dari missionary ke doggy"""
        return f"""*{self.character.name} memeluk Mas erat, napas tersengal*

"{self.character.panggilan}... dari belakang... doggy... ayo..."

*Dia berbalik, merangkak, pantat naik*

"Aku mau Mas genjot dari belakang..." """
    
    async def _build_transition_to_position_change(self) -> str:
        """Bangun pesan transisi dari doggy ke ganti posisi"""
        return f"""*{self.character.name} berhenti, tubuhnya gemetar, napas putus-putus*

"{self.character.panggilan}... mau ganti posisi? Mau di mana? Sofa? Berdiri? Kamar mandi?"

*Dia menoleh ke belakang, mata sayu*

"Aku ikutin apa yang Mas mau..." """
    
    async def _build_aftercare_transition(self) -> str:
        """Bangun pesan transisi ke aftercare"""
        return f"""*{self.character.name} memeluk Mas erat, napas mulai stabil*

"{self.character.panggilan}... puas?"

*Dia mengusap dada Mas pelan*

"Mas mau lagi? Aku masih siap..." """
