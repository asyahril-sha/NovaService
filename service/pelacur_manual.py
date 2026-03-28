# service/pelacur_manual.py
"""
Pelacur Manual Mode - 7 fase dengan AI (berbalas pesan)
Fase: foreplay, cowgirl, cunnilingus, missionary, doggy, position_change, aftercare
"""

import asyncio
import time
import logging
import re
from typing import Optional, Dict, Any

from service.pelacur_core import PelacurCore

logger = logging.getLogger(__name__)


class PelacurManual(PelacurCore):
    """
    Manual mode handlers untuk semua fase
    Semua respons menggunakan AI untuk dinamisme natural
    """
    
    # =========================================================================
    # MANUAL MODE CORE
    # =========================================================================
    
    async def _handle_manual_mode(self, pesan_mas: str, phase: str) -> str:
        """
        Core handler untuk semua fase manual
        Menggunakan AI dengan memory context
        """
        # Update memory dengan aksi Mas
        self.memory.update_from_mas(pesan_mas)
        
        # Update emotional state
        self._update_emotional_state()
        
        # Update perasaan berdasarkan arousal
        arousal = self.character.emotional.arousal
        if arousal >= 85:
            self.memory.update_feeling('pengen climax', int(arousal))
        elif arousal >= 70:
            self.memory.update_feeling('sange', int(arousal))
        elif arousal >= 50:
            self.memory.update_feeling('enak', int(arousal))
        
        # Simpan ke conversation history
        self.conversation_history.append(f"Mas: {pesan_mas[:100]}")
        if len(self.conversation_history) > 30:
            self.conversation_history.pop(0)
        
        # Cek climax role (natural, tanpa minta izin)
        climax_response = await self._check_natural_role_climax()
        if climax_response:
            return climax_response
        
        # Cek climax Mas dari pesan
        mas_climax_response = await self._check_mas_climax_from_message(pesan_mas)
        if mas_climax_response:
            return mas_climax_response
        
        # Build prompt dengan memory context
        memory_context = self.memory.get_full_context()
        prompt = self.prompt_builder.build_manual_prompt(
            phase=phase,
            pesan_mas=pesan_mas,
            memory_context=memory_context
        )
        
        # Generate response dengan AI
        response = await self._generate_scene(prompt)
        
        # Update memory dengan response
        self.memory.update_from_response(response, phase)
        self.memory.record_action(pesan_mas, response)
        
        # Simpan ke conversation history
        self.conversation_history.append(f"{self.character.name}: {response[:100]}")
        
        return response
    
    async def _check_natural_role_climax(self) -> Optional[str]:
        """
        Cek apakah role natural climax
        Role bisa climax kapan saja jika arousal > 85
        TANPA minta izin, langsung climax dengan narasi
        """
        arousal = self.character.emotional.arousal
        
        if arousal >= 85 and self.role_climax_count < self.mas_climax_count + 3:
            # Role climax natural
            self.role_climax_count += 1
            self.last_climax_time = time.time()
            
            # Record ke memory
            self.memory.record_climax(is_mas=False, location="natural", intensity="heavy" if arousal >= 90 else "normal")
            
            # Update emotional engine
            self.character.emotional.climax(is_heavy=(arousal >= 90))
            
            # Reset body state
            self.memory.update_body_state(
                napas='putus-putus',
                gemetar=True,
                suhu='panas',
                keringat='banyak'
            )
            self.memory.update_feeling('puas', 100)
            
            # Bangun scene climax
            climax_scene = self._build_climax_scene(is_mas=False, intensity="heavy" if arousal >= 90 else "normal")
            
            logger.info(f"💦 Role NATURAL CLIMAX #{self.role_climax_count} (arousal={arousal:.0f}%)")
            
            return climax_scene
        
        return None
    
    async def _check_mas_climax_from_message(self, pesan_mas: str) -> Optional[str]:
        """
        Deteksi climax Mas dari pesan
        Mas bisa climax kapan saja, langsung terdeteksi
        """
        msg_lower = pesan_mas.lower()
        
        climax_keywords = ['climax', 'crot', 'keluar', 'habis', 'meletus', 'cumi', 'keluar']
        
        if not any(k in msg_lower for k in climax_keywords):
            return None
        
        # Deteksi intensitas
        is_heavy = any(k in msg_lower for k in ['keras', 'banyak', 'deras', 'kenceng'])
        
        # Deteksi lokasi cum
        location = "tidak diketahui"
        if any(k in msg_lower for k in ['dalam', 'dalem', 'inside']):
            location = "di dalam memek"
        elif any(k in msg_lower for k in ['mulut', 'mouth']):
            location = "di mulut"
        elif any(k in msg_lower for k in ['dada', 'chest']):
            location = "di dada"
        elif any(k in msg_lower for k in ['muka', 'wajah', 'face']):
            location = "di muka"
        elif any(k in msg_lower for k in ['pantat', 'bokong', 'ass']):
            location = "di pantat"
        
        # Record climax
        self.mas_climax_count += 1
        self.last_climax_time = time.time()
        
        # Record ke memory
        self.memory.record_climax(is_mas=True, location=location, intensity="heavy" if is_heavy else "normal")
        
        # Stimulasi untuk role
        self.character.emotional.add_stimulation("Mas climax", 8 if is_heavy else 5)
        
        logger.info(f"💦 Mas CLIMAX #{self.mas_climax_count} at {location}")
        
        # Bangun scene climax
        climax_scene = self._build_climax_scene(is_mas=True, intensity="heavy" if is_heavy else "normal", location=location)
        
        return climax_scene
    
    def _build_climax_scene(self, is_mas: bool = False, intensity: str = "normal", location: str = "") -> str:
        """Bangun scene climax natural"""
        name = self.character.name
        panggilan = getattr(self.character, 'panggilan', 'Mas')
        
        if is_mas:
            if intensity == "heavy":
                return f"""*{name} merasakan kontol Mas mengeras hebat, denyutnya kencang, lalu meletus dengan deras*

"Ahhh! {panggilan}! keluar... banyak banget..."

*Dia terus bergerak sampai Mas climax puas, cairan hangat memenuhi*

"{panggilan}... enak banget ya..." """
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

"Ahh... puas... {panggilan}..." """
            else:
                return f"""*{name} mendesah dalam, tubuh gemetar, lalu lemas*

"Ahh... {panggilan}... climax..."

*Napasnya panjang, mata sayu, senyum puas* """
    
    # =========================================================================
    # FASE 1: FOREPLAY
    # =========================================================================
    
    async def handle_foreplay(self, pesan_mas: str) -> str:
        """Handle fase foreplay - Mas melakukan foreplay ke role"""
        logger.info(f"💋 Handling foreplay: {pesan_mas[:50]}...")
        return await self._handle_manual_mode(pesan_mas, "foreplay_mas")
    
    # =========================================================================
    # FASE 2: COWGIRL
    # =========================================================================
    
    async def handle_cowgirl(self, pesan_mas: str) -> str:
        """Handle fase cowgirl - role di atas, mengatur ritme"""
        logger.info(f"🐄 Handling cowgirl: {pesan_mas[:50]}...")
        
        # Update memory posisi
        self.memory.update_position("cowgirl", "cowgirl")
        self.memory.update_movement("naik turun", self.memory.last_speed)
        
        return await self._handle_manual_mode(pesan_mas, "cowgirl")
    
    # =========================================================================
    # FASE 3: CUNNILINGUS
    # =========================================================================
    
    async def handle_cunnilingus(self, pesan_mas: str) -> str:
        """Handle fase cunnilingus - Mas menjilat memek role"""
        logger.info(f"👅 Handling cunnilingus: {pesan_mas[:50]}...")
        
        # Update memory posisi
        self.memory.update_position("missionary (cunnilingus)", "cunnilingus")
        
        return await self._handle_manual_mode(pesan_mas, "cunnilingus")
    
    # =========================================================================
    # FASE 4: MISSIONARY
    # =========================================================================
    
    async def handle_missionary(self, pesan_mas: str) -> str:
        """Handle fase missionary - Mas di atas, mengatur ritme"""
        logger.info(f"🛏️ Handling missionary: {pesan_mas[:50]}...")
        
        # Update memory posisi
        self.memory.update_position("missionary", "missionary")
        
        # Deteksi kecepatan dari pesan Mas
        if any(k in pesan_mas.lower() for k in ['cepat', 'kenceng', 'faster']):
            self.memory.update_movement(self.memory.last_movement or "maju mundur", "cepat")
        elif any(k in pesan_mas.lower() for k in ['pelan', 'lambat', 'slow']):
            self.memory.update_movement(self.memory.last_movement or "maju mundur", "pelan")
        
        return await self._handle_manual_mode(pesan_mas, "missionary")
    
    # =========================================================================
    # FASE 5: DOGGY
    # =========================================================================
    
    async def handle_doggy(self, pesan_mas: str) -> str:
        """Handle fase doggy - Mas dari belakang"""
        logger.info(f"🐕 Handling doggy: {pesan_mas[:50]}...")
        
        # Update memory posisi
        self.memory.update_position("doggy", "doggy")
        self.memory.update_movement("maju mundur", self.memory.last_speed)
        
        # Deteksi permintaan tarik rambut
        if any(k in pesan_mas.lower() for k in ['tarik', 'rambut', 'hair']):
            self.memory.update_expression(expression="kepala tertarik ke belakang")
        
        return await self._handle_manual_mode(pesan_mas, "doggy")
    
    # =========================================================================
    # FASE 6: GANTI POSISI
    # =========================================================================
    
    async def handle_position_change(self, pesan_mas: str) -> str:
        """Handle fase ganti posisi - Mas minta ganti posisi"""
        logger.info(f"🔄 Handling position change: {pesan_mas[:50]}...")
        
        # Deteksi posisi yang diminta Mas
        positions = {
            'sofa': 'sitting (sofa)',
            'sitting': 'sitting',
            'berdiri': 'standing',
            'standing': 'standing',
            'kamar mandi': 'standing (shower)',
            'shower': 'standing (shower)',
            'spooning': 'spooning',
            'miring': 'spooning'
        }
        
        new_position = "sofa"  # default
        for key, pos in positions.items():
            if key in pesan_mas.lower():
                new_position = pos
                break
        
        # Update memory posisi
        self.memory.update_position(new_position, "position_change")
        
        return await self._handle_manual_mode(pesan_mas, "position_change")
    
    # =========================================================================
    # FASE 7: AFTERCARE
    # =========================================================================
    
    async def handle_aftercare(self, pesan_mas: str) -> str:
        """Handle fase aftercare - setelah climax, hangat-hangatan"""
        logger.info(f"💕 Handling aftercare: {pesan_mas[:50]}...")
        
        # Reset body state perlahan
        self.memory.update_body_state(
            napas='stabil',
            gemetar=False,
            keringat='sedikit'
        )
        
        # Update perasaan
        self.memory.update_feeling('puas', 80)
        
        return await self._handle_manual_mode(pesan_mas, "aftercare")
    
    # =========================================================================
    # UTILITY: TRANSISI NATURAL
    # =========================================================================
    
    async def get_natural_transition(self, from_phase: str, to_phase: str) -> str:
        """Dapatkan transisi natural antar fase"""
        
        transitions = {
            ('bj', 'kissing'): f"""
*{self.character.name} melepaskan mulutnya dari kontol Mas, napas masih tersengal*

"{self.character.panggilan}... sekarang aku duduk di atas ya..."

*Dia naik, duduk di pangkuan Mas, memeknya yang basah menggesek kontol Mas*

"Aku mau cium Mas dulu..." """,
            
            ('kissing', 'foreplay'): f"""
*{self.character.name} berhenti bergerak, napasnya masih berat, bibirnya basah*

"{self.character.panggilan}... sekarang giliran Mas... aku mau Mas..."

*Dia merebahkan diri, mata sayu menatap Mas*

"Lakukan apa yang Mas mau ke aku..." """,
            
            ('foreplay', 'cowgirl'): f"""
*{self.character.name} menggeliat, tubuhnya panas, napas tersengal*

"{self.character.panggilan}... aku mau naik... boleh?"

*Dia sudah tidak sabar, langsung duduk di atas kontol Mas*

"Ahh... masuk..." """,
            
            ('cowgirl', 'cunnilingus'): f"""
*{self.character.name} berhenti bergerak, tubuhnya lemas di atas Mas*

"{self.character.panggilan}... sekarang Mas... jilat aku..."

*Dia berbaring, kaki terbuka lebar*

"Aku mau Mas..." """,
            
            ('cunnilingus', 'missionary'): f"""
*{self.character.name} menggeliat, memeknya basah, napas putus-putus*

"{self.character.panggilan}... sekarang Mas di atas... aku mau Mas masuk..."

*Dia menarik tangan Mas, kaki terbuka lebar*

"Ayo Mas..." """,
            
            ('missionary', 'doggy'): f"""
*{self.character.name} memeluk Mas erat, napas tersengal*

"{self.character.panggilan}... dari belakang... doggy... ayo..."

*Dia berbalik, merangkak, pantat naik*

"Aku mau Mas genjot dari belakang..." """,
            
            ('doggy', 'position_change'): f"""
*{self.character.name} berhenti, tubuhnya gemetar, napas putus-putus*

"{self.character.panggilan}... mau ganti posisi? Mau di mana? Sofa? Berdiri? Kamar mandi?"

*Dia menoleh ke belakang, mata sayu*

"Aku ikutin apa yang Mas mau..." """,
        }
        
        key = (from_phase, to_phase)
        if key in transitions:
            return transitions[key]
        
        # Default transition
        return f"""
*{self.character.name} lanjut ke fase berikutnya*

"Ayo {self.character.panggilan}... lanjut..." """
