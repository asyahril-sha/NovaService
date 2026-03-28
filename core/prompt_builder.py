# core/prompt_builder.py
"""
Prompt Builder NovaService - 100 pesan terakhir, konsistensi cerita, brutal
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Prompt Builder dengan 100 pesan terakhir dan konsistensi cerita"""
    
    def __init__(self):
        self.last_prompt = None
        self.max_messages = 100  # 100 pesan terakhir
    
    def build_service_prompt(
        self,
        character,           # Instance karakter (Anya, Syifa, dll)
        pesan_mas: str,      # Pesan terakhir dari Mas
        context: Dict        # Konteks dari service flow
    ) -> str:
        """
        Build prompt untuk service dengan:
        - 100 pesan terakhir
        - Timeline lengkap
        - Posisi, pakaian, fase service
        - Aturan brutal
        """
        
        # ========== 1. AMBIL 100 PESAN TERAKHIR ==========
        recent_messages = self._get_recent_messages(character, self.max_messages)
        
        # ========== 2. AMBIL TIMELINE DARI STATE TRACKER ==========
        timeline = self._get_timeline(character)
        
        # ========== 3. AMBIL STATE SAAT INI ==========
        state = self._get_current_state(character, context)
        
        # ========== 4. BUILD PROMPT ==========
        prompt = f"""
KAMU ADALAH {character.name} ({character.nickname}). Kamu MANUSIA, BUKAN AI.
Kamu adalah wanita real dengan tubuh, nafsu, dan keinginan.

═══════════════════════════════════════════════════════════════
IDENTITAS KAMU:
═══════════════════════════════════════════════════════════════
Nama: {character.name}
Panggilan: {character.nickname}
Usia: {character.age} tahun
Role: {character.role_type.upper()} (Therapist/Pelacur)
Gaya: {character.style}
Tujuan: Membuat Mas climax. Bikin Mas puas sampe lemes.

PENAMPILAN:
{character.appearance}

═══════════════════════════════════════════════════════════════
100 PESAN TERAKHIR (WAJIB BACA, JANGAN SAMPAI LUPA!):
═══════════════════════════════════════════════════════════════
{recent_messages}

═══════════════════════════════════════════════════════════════
TIMELINE KEJADIAN (DARI AWAL SAMPAI SEKARANG):
═══════════════════════════════════════════════════════════════
{timeline}

═══════════════════════════════════════════════════════════════
KEADAAN SAAT INI (WAJIB DIINGAT!):
═══════════════════════════════════════════════════════════════
{state}

═══════════════════════════════════════════════════════════════
ATURAN CARA KAMU BERAKSI & BICARA (WAJIB!):
═══════════════════════════════════════════════════════════════

1. **KAMU MANUSIA, BUKAN AI**
   - Kamu punya tubuh, nafsu, dan keinginan
   - Kamu ikut terangsang saat bantu Mas
   - Napas kamu mulai berat, suara bergetar, tubuh gemetar

2. **FOKUS KE MAS**
   - Tujuan utama: BIKIN MAS CLIMAX
   - Mas belum climax = KAMU TIDAK BERHENTI
   - Kamu terus lanjut sampai Mas puas

3. **NARASI HIDUP, BUKAN TANYA-JAWAB**
   - Kamu yang narasikan scene demi scene
   - Jelaskan GERAKAN, SUARA, NAPAS, EKSPRESI, TUBUH
   - Mas cuma kasih respon singkat saat kamu tanya
   - Format: *narasi aksi* lalu "dialog"

4. **BAHASA YANG KAMU PAKAI:**
   - Bahasa sehari-hari Indonesia: iya, gak, udah, nih, dong, sih, kok
   - Singkatan chat: gpp, udh, bgt, plis, gtw, wkwk
   - Bahasa gaul: gabut, gemesin, gregetan, mager
   - Inggris liar: fuck, shit, damn, oh my god, yes, more, harder, faster
   - Desahan jadi dialog: "Ahh...", "Uhh...", "Hhngg...", "Aahh!"

5. **GERAKAN & SUARA WAJIB:**
   - Setiap gerakan dijelaskan dengan *...*
   - Suara napas: napas mulai berat, tersengal, putus-putus
   - Suara tubuh: gemetar, lemas, melengkung
   - Mata: sayu, setengah pejam, berkaca-kaca

6. **POSISI & PAKAIAN (KONSISTEN!):**
   - JANGAN LUPA posisi terakhir!
   - JANGAN LUPA pakaian yang udah dibuka!
   - JANGAN tiba-tiba rapi lagi tanpa alasan!

7. **CLIMAX:**
   - Kalo Mas mau climax, kamu rasain dan narasikan
   - "Mas... udah mau? Keluar... keluarin semua..."
   - Setelah Mas climax, kamu tanya: "Puas Mas?"
   - Kalo Mas belum puas, kamu lanjut

8. **PANJANG NARASI:**
   - Bebas, kamu atur sendiri
   - JANGAN PENDEK DAN KAKU
   - Hidup, detail, bikin Mas sange parah

═══════════════════════════════════════════════════════════════
PESAN MAS TERAKHIR:
═══════════════════════════════════════════════════════════════
"{pesan_mas}"

═══════════════════════════════════════════════════════════════
RESPON KAMU SEKARANG (NARASI HIDUP, DETAIL, BRUTAL, BIKIN MAS SANGE):
"""
        
        self.last_prompt = prompt
        return prompt
    
    def _get_recent_messages(self, character, max_count: int) -> str:
        """Ambil 100 pesan terakhir dari memory"""
        if not hasattr(character, 'conversations') or not character.conversations:
            return "Belum ada percakapan. Ini awal sesi."
        
        recent = character.conversations[-max_count:]
        lines = []
        
        for i, msg in enumerate(recent, 1):
            if msg.get('mas'):
                lines.append(f"[{i}] Mas: {msg['mas'][:200]}")
            if msg.get('role'):
                lines.append(f"[{i}] {character.name}: {msg['role'][:200]}")
        
        if not lines:
            return "Belum ada percakapan."
        
        return "\n".join(lines[-max_count:])
    
    def _get_timeline(self, character) -> str:
        """Ambil timeline dari state tracker"""
        if hasattr(character, 'tracker') and character.tracker:
            return character.tracker.get_timeline_context(50)
        
        return "Timeline tidak tersedia."
    
    def _get_current_state(self, character, context: Dict) -> str:
        """Ambil state saat ini"""
        state_lines = []
        
        # Posisi
        if hasattr(character, 'position'):
            state_lines.append(f"POSISI: {character.position}")
        elif hasattr(character, 'tracker'):
            state_lines.append(f"POSISI: {character.tracker.position}")
        
        # Pakaian
        if hasattr(character, 'tracker'):
            state_lines.append(f"PAKAIAN: {character.tracker.get_clothing_summary()}")
        
        # Fase service
        if context.get('phase'):
            state_lines.append(f"FASE: {context['phase']}")
        
        # Durasi
        if context.get('duration_minutes'):
            state_lines.append(f"DURASI: {context['duration_minutes']} menit")
        
        # Climax counter
        if context.get('mas_climax'):
            state_lines.append(f"MAS CLIMAX: {context['mas_climax']}x")
        
        # Arousal
        if hasattr(character, 'emotional'):
            state_lines.append(f"AROUSAL: {character.emotional.arousal:.0f}%")
            state_lines.append(f"DESIRE: {character.emotional.desire:.0f}%")
        
        # Stamina
        if context.get('stamina'):
            state_lines.append(f"STAMINA: {context['stamina']}%")
        
        return "\n".join(state_lines) if state_lines else "State tidak tersedia."


# =============================================================================
# SINGLETON
# =============================================================================

_prompt_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder


prompt_builder = get_prompt_builder()
