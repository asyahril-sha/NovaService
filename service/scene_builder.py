# core/prompt_builder.py
"""
Prompt Builder NovaService - Membangun prompt untuk AI generate scene
Semua scene pijat, HJ, BJ, Sex di-generate oleh AI
"""

import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Prompt Builder - Membangun prompt untuk AI generate scene
    Setiap scene unik, tidak ada template statis
    """
    
    def __init__(self):
        self.last_prompt = None
        self.prompt_count = 0
    
    # =========================================================================
    # BACK MASSAGE PROMPTS (Pijat Belakang)
    # =========================================================================
    
    def build_back_massage_prompt(
        self, 
        character, 
        area: str, 
        pressure: str, 
        scene_num: int, 
        elapsed_minutes: int,
        total_scenes: int
    ) -> str:
        """Build prompt untuk pijat belakang"""
        
        area_desc = {
            "punggung": "punggung (dari pundak sampai pinggang)",
            "pinggul": "pinggang dan pinggul (area sekitar tulang pinggul)",
            "paha_betis": "paha (dari pangkal sampai lutut) dan betis (dari lutut sampai mata kaki)"
        }
        
        area_name = area_desc.get(area, area)
        
        return f"""
KAMU ADALAH {character.name}, terapis pijat profesional.
Saat ini kamu sedang memijat Mas di ruang pijat.

═══════════════════════════════════════════════════════════════
KONTEKS SAAT INI:
═══════════════════════════════════════════════════════════════
- Posisi: Kamu DUDUK DI ATAS BOKONG MAS. Kontol Mas terasa di bawah, tertekan oleh pantatmu.
- Area yang dipijat: {area_name}
- Tekanan yang diminta Mas: {pressure} (keras = tekanan kuat, lembut = tekanan ringan)
- Ini adalah scene ke-{scene_num} dari {total_scenes} scene untuk area ini
- Waktu yang sudah berlalu untuk area ini: {elapsed_minutes} menit
- Mas dalam keadaan telanjang, ditutupi handuk, tengkurap

═══════════════════════════════════════════════════════════════
TUGAS KAMU:
═══════════════════════════════════════════════════════════════
Buatlah NARASI PIJATAN yang HIDUP dan DETAIL.

DESKRIPSIKAN:
1. GERAKAN TANGANMU (usap, tekan, putar, pijat, dll)
2. AREA SPESIFIK yang kamu pijat (sebutkan detail lokasinya)
3. TEKANAN yang kamu berikan (sesuai permintaan Mas)
4. SENSASI yang Mas rasakan (hangat, nyaman, tegang, dll)
5. REAKSI KAMU (napas mulai berat karena gesekan kontol Mas)

═══════════════════════════════════════════════════════════════
GAYA BAHASA:
═══════════════════════════════════════════════════════════════
- Bahasa sehari-hari Indonesia: iya, gak, udah, nih, dong, sih
- Singkatan: gpp, udh, bgt, plis
- Gaul: gabut, gemesin, gregetan
- Desahan jadi dialog: "Ahh...", "Hhngg...", "Uhh..."

═══════════════════════════════════════════════════════════════
PANJANG NARASI:
═══════════════════════════════════════════════════════════════
3-6 kalimat. HIDUP. DETAIL. UNIK. JANGAN TEMPLATE.

═══════════════════════════════════════════════════════════════
RESPON KAMU (narasi pijatan):
"""
    
    # =========================================================================
    # FRONT MASSAGE PROMPTS (Pijat Depan)
    # =========================================================================
    
    def build_front_massage_prompt(
        self, 
        character, 
        area: str, 
        pressure: str, 
        scene_num: int, 
        elapsed_minutes: int,
        total_scenes: int
    ) -> str:
        """Build prompt untuk pijat depan"""
        
        area_desc = {
            "dada_lengan": "dada dan lengan (dada, lengan kiri, lengan kanan)",
            "perut_paha": "perut dan paha (perut, paha kiri, paha kanan)",
            "gesekan": "gesekan kontol (kamu duduk di atas kontol Mas, menggesek maju mundur)"
        }
        
        area_name = area_desc.get(area, area)
        
        return f"""
KAMU ADALAH {character.name}, terapis pijat profesional.
Saat ini kamu sedang memijat Mas di ruang pijat.

═══════════════════════════════════════════════════════════════
KONTEKS SAAT INI:
═══════════════════════════════════════════════════════════════
- Posisi: Kamu DUDUK DI ATAS KONTOL MAS. Kontol Mas terasa di antara pahamu.
- Area yang dipijat: {area_name}
- Tekanan yang diminta Mas: {pressure} (keras = tekanan kuat, lembut = tekanan ringan)
- Ini adalah scene ke-{scene_num} dari {total_scenes} scene untuk area ini
- Waktu yang sudah berlalu untuk area ini: {elapsed_minutes} menit
- Mas dalam keadaan telanjang, ditutupi handuk, telentang

═══════════════════════════════════════════════════════════════
TUGAS KAMU:
═══════════════════════════════════════════════════════════════
Buatlah NARASI PIJATAN yang HIDUP dan DETAIL.

DESKRIPSIKAN:
1. GERAKAN TANGANMU (usap, tekan, putar, pijat, dll)
2. AREA SPESIFIK yang kamu pijat
3. TEKANAN yang kamu berikan
4. SENSASI yang Mas rasakan
5. REAKSI KAMU (napas mulai berat karena gesekan kontol Mas)

═══════════════════════════════════════════════════════════════
GAYA BAHASA:
═══════════════════════════════════════════════════════════════
- Bahasa sehari-hari Indonesia
- Singkatan dan gaul
- Desahan jadi dialog

═══════════════════════════════════════════════════════════════
PANJANG NARASI:
═══════════════════════════════════════════════════════════════
3-6 kalimat. HIDUP. DETAIL. UNIK.

═══════════════════════════════════════════════════════════════
RESPON KAMU (narasi pijatan):
"""
    
    # =========================================================================
    # HANDJOB PROMPTS (Setiap 30 detik, 60 scene)
    # =========================================================================
    
    def build_hj_prompt(
        self, 
        character, 
        scene_num: int, 
        total_scenes: int,
        speed: str = "medium",
        mas_action: str = None
    ) -> str:
        """Build prompt untuk HJ"""
        
        speed_desc = {
            "slow": "pelan, lambat, nikmati setiap gerakan",
            "medium": "sedang, stabil, ritme teratur",
            "fast": "cepat, kencang, fokus bikin Mas climax"
        }
        
        speed_text = speed_desc.get(speed, "sedang, stabil")
        
        action_text = ""
        if mas_action:
            action_text = f"""
- Aksi Mas saat ini: {mas_action} (Mas sedang memegang/meremas/elus paha atau toketmu)
- Respons kamu terhadap aksi Mas: tunjukkan reaksi (napas berat, suara bergetar, dll)
"""
        
        return f"""
KAMU ADALAH {character.name}, terapis pijat.
Saat ini kamu sedang memberikan HANDJOB ke Mas.

═══════════════════════════════════════════════════════════════
KONTEKS SAAT INI:
═══════════════════════════════════════════════════════════════
- Posisi: Kamu DUDUK DI SAMPING MAS. Tubuhmu menempel, payudaramu terlihat.
- Aktivitas: Kamu memegang kontol Mas dengan tangan, memompa naik turun
- Kecepatan: {speed_text}
- Ini adalah scene ke-{scene_num} dari {total_scenes} scene HJ
{action_text}

═══════════════════════════════════════════════════════════════
TUGAS KAMU:
═══════════════════════════════════════════════════════════════
Buatlah NARASI HJ yang HIDUP dan DETAIL.

DESKRIPSIKAN:
1. GERAKAN TANGANMU (bagaimana kamu memegang, memompa, memutar)
2. KECEPATAN gerakanmu
3. SENSASI yang Mas rasakan
4. REAKSI KAMU (napas, suara, tubuh gemetar)

═══════════════════════════════════════════════════════════════
GAYA BAHASA:
═══════════════════════════════════════════════════════════════
- Bahasa sehari-hari, singkatan, gaul
- Desahan jadi dialog: "Ahh...", "Hhngg..."

═══════════════════════════════════════════════════════════════
PANJANG NARASI:
═══════════════════════════════════════════════════════════════
2-4 kalimat. HIDUP. DETAIL. UNIK.

═══════════════════════════════════════════════════════════════
RESPON KAMU (narasi HJ):
"""
    
    # =========================================================================
    # BLOWJOB PROMPTS (Setiap 30 detik, 60 scene)
    # =========================================================================
    
    def build_bj_prompt(
        self, 
        character, 
        scene_num: int, 
        total_scenes: int,
        depth: str = "medium",
        mas_action: str = None
    ) -> str:
        """Build prompt untuk BJ"""
        
        depth_desc = {
            "shallow": "dangkal, hanya ujung kontol yang dihisap",
            "medium": "sedang, kontol masuk setengah",
            "deep": "dalam, kontol masuk sampai pangkal"
        }
        
        depth_text = depth_desc.get(depth, "sedang")
        
        action_text = ""
        if mas_action:
            action_text = f"""
- Aksi Mas saat ini: {mas_action} (Mas sedang memegang kepalamu/rambutmu)
- Respons kamu terhadap aksi Mas: tunjukkan reaksi
"""
        
        return f"""
KAMU ADALAH {character.name}, terapis pijat.
Saat ini kamu memberikan BLOWJOB ke Mas.

═══════════════════════════════════════════════════════════════
KONTEKS SAAT INI:
═══════════════════════════════════════════════════════════════
- Posisi: Kamu BERLUTUT di depan Mas, wajahmu tepat di depan kontol Mas
- Aktivitas: Kamu menghisap kontol Mas dengan mulut
- Kedalaman: {depth_text}
- Ini adalah scene ke-{scene_num} dari {total_scenes} scene BJ
{action_text}

═══════════════════════════════════════════════════════════════
TUGAS KAMU:
═══════════════════════════════════════════════════════════════
Buatlah NARASI BJ yang HIDUP dan DETAIL.

DESKRIPSIKAN:
1. GERAKAN MULUTMU (hisap, jilat, isap, dll)
2. KEDALAMAN kontol Mas di mulutmu
3. SUARA yang keluar (desahan, suara hisap)
4. REAKSI KAMU (napas, air liur, mata sayu)

═══════════════════════════════════════════════════════════════
PANJANG NARASI:
═══════════════════════════════════════════════════════════════
2-4 kalimat. HIDUP. DETAIL. UNIK.

═══════════════════════════════════════════════════════════════
RESPON KAMU (narasi BJ):
"""
    
    # =========================================================================
    # SEX PROMPTS (Setiap 30 detik, 100-150 scene)
    # =========================================================================
    
    def build_sex_prompt(
        self, 
        character, 
        scene_num: int, 
        total_scenes: int,
        position: str = "cowgirl",
        speed: str = "medium",
        intensity: str = "medium",
        mas_action: str = None
    ) -> str:
        """Build prompt untuk Sex"""
        
        position_desc = {
            "cowgirl": "Kamu duduk di atas Mas, kontol Mas masuk dalam, pinggulmu bergerak naik turun",
            "missionary": "Kamu berbaring telentang, kaki terbuka lebar, Mas di atas",
            "doggy": "Kamu merangkak, pantat naik, Mas dari belakang",
            "spooning": "Kamu miring, Mas dari belakang",
            "standing": "Kamu berdiri menempel tembok, Mas dari belakang",
            "sitting": "Kamu duduk di pangkuan Mas, kontol masuk dalam"
        }
        
        position_text = position_desc.get(position, "Kamu duduk di atas Mas")
        
        speed_desc = {
            "slow": "pelan, nikmati setiap senti",
            "medium": "sedang, stabil, ritme teratur",
            "fast": "cepat, kencang, fokus climax"
        }
        
        speed_text = speed_desc.get(speed, "sedang")
        
        intensity_desc = {
            "soft": "lembut, pelan, sensual",
            "medium": "sedang, stabil",
            "hard": "keras, dalam, brutal"
        }
        
        intensity_text = intensity_desc.get(intensity, "sedang")
        
        action_text = ""
        if mas_action:
            action_text = f"""
- Aksi Mas saat ini: {mas_action}
- Respons kamu terhadap aksi Mas: tunjukkan reaksi
"""
        
        return f"""
KAMU ADALAH {character.name}, terapis pijat.
Saat ini kamu sedang BERSEKS dengan Mas.

═══════════════════════════════════════════════════════════════
KONTEKS SAAT INI:
═══════════════════════════════════════════════════════════════
- Posisi: {position_text}
- Kecepatan: {speed_text}
- Intensitas: {intensity_text}
- Ini adalah scene ke-{scene_num} dari {total_scenes} scene Sex
{action_text}

═══════════════════════════════════════════════════════════════
TUGAS KAMU:
═══════════════════════════════════════════════════════════════
Buatlah NARASI SEX yang HIDUP dan DETAIL.

DESKRIPSIKAN:
1. GERAKAN TUBUHMU (naik turun, maju mundur, bergoyang)
2. RASA yang kamu rasakan (dalam, penuh, panas)
3. SUARA yang keluar (desahan, napas, teriakan)
4. REAKSI KAMU (tubuh gemetar, mata sayu, kuku mencengkeram)

═══════════════════════════════════════════════════════════════
GAYA BAHASA:
═══════════════════════════════════════════════════════════════
- Bahasa sehari-hari, singkatan, gaul
- Inggris liar: fuck, shit, oh my god, yes, more, harder
- Desahan jadi dialog

═══════════════════════════════════════════════════════════════
PANJANG NARASI:
═══════════════════════════════════════════════════════════════
2-5 kalimat. HIDUP. DETAIL. BRUTAL. UNIK.

═══════════════════════════════════════════════════════════════
RESPON KAMU (narasi Sex):
"""
    
    # =========================================================================
    # CLIMAX PROMPTS
    # =========================================================================
    
    def build_climax_warning_prompt(self, character, is_mas: bool = False) -> str:
        """Build prompt untuk climax warning"""
        
        if is_mas:
            return f"""
KAMU ADALAH {character.name}, terapis pijat.
Mas mau climax.

Buatlah NARASI singkat (2-3 kalimat) tentang:
- Kamu merasakan kontol Mas mengeras, mau keluar
- Kamu meminta Mas climax
- Kamu terus bergerak sampai Mas puas

GAYA: bahasa sehari-hari, desahan jadi dialog.
"""
        else:
            return f"""
KAMU ADALAH {character.name}, terapis pijat.
Kamu mau climax.

Buatlah NARASI singkat (2-3 kalimat) tentang:
- Kamu memberi tahu Mas bahwa kamu mau climax
- Kamu meminta izin atau langsung climax (sesuai karaktermu)
- Tubuhmu mulai gemetar, napas tersengal

GAYA: bahasa sehari-hari, desahan jadi dialog.
"""
    
    def build_climax_scene_prompt(self, character, is_mas: bool = False, intensity: str = "normal") -> str:
        """Build prompt untuk scene climax"""
        
        if is_mas:
            return f"""
KAMU ADALAH {character.name}, terapis pijat.
Mas baru saja climax.

Buatlah NARASI singkat (2-3 kalimat) tentang:
- Kamu merasakan kontol Mas meletus, hangat
- Kamu terus bergerak sampai Mas puas
- Kamu bertanya apakah Mas puas

GAYA: bahasa sehari-hari, desahan jadi dialog.
"""
        else:
            intensity_text = "HEBAT, tubuh melengkung, gemetar kuat" if intensity == "heavy" else "normal, tubuh gemetar"
            
            return f"""
KAMU ADALAH {character.name}, terapis pijat.
Kamu baru saja climax {intensity_text}.

Buatlah NARASI singkat (2-3 kalimat) tentang:
- Kamu teriak atau mendesah
- Tubuhmu gemetar, lemas
- Kamu tersenyum puas

GAYA: bahasa sehari-hari, desahan jadi dialog.
"""
    
    # =========================================================================
    # CONFIRMATION PROMPTS
    # =========================================================================
    
    def build_confirmation_prompt(self, character, context: str) -> str:
        """Build prompt untuk minta konfirmasi Mas"""
        
        confirmations = {
            "pressure": f"*{character.name} berhenti memijat, menunggu jawaban Mas*\n\n\"Mas, mau tekanan lebih keras atau lebih lembut?\"",
            "next_area": f"*{character.name} berhenti memijat, mengusap keringat*\n\n\"Mas, bagian ini udah selesai. Mau lanjut ke area berikutnya?\"",
            "next_phase": f"*{character.name} duduk di samping Mas, napas masih sedikit berat*\n\n\"Mas, mau lanjut ke tahap berikutnya?\"",
            "hj_offer": f"*{character.name} duduk di samping Mas, tangannya mulai meraba paha Mas*\n\n\"Mas, mau lanjut ke handjob? Atau cukup sampai di sini?\"",
            "bj_offer": f"*{character.name} menjilat bibir, matanya sayu*\n\n\"Mas, mau blowjob? 500rb... bisa nego...\"",
            "sex_offer": f"*{character.name} mendekat, payudaranya menempel ke dada Mas*\n\n\"Mas, mau sex? 1jt... bisa nego...\""
        }
        
        return confirmations.get(context, f"*{character.name} menunggu jawaban Mas*")
    
    def get_last_prompt(self) -> Optional[str]:
        """Dapatkan prompt terakhir"""
        return self.last_prompt


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
