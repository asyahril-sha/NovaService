# service/scene_builder.py
"""
Scene Builder NovaService - Membangun narasi hidup yang brutal
Base class untuk therapist dan pelacur
"""

import time
import random
from typing import Dict, Optional, Any
from datetime import datetime


class SceneBuilder:
    """
    Scene Builder - Membangun narasi hidup scene by scene
    Dengan deskripsi brutal, detail, bikin Mas sange
    """
    
    def __init__(self, character):
        self.character = character
        self.last_scene_type = None
    
    # =========================================================================
    # GREETING SCENES
    # =========================================================================
    
    def build_greeting_scene(self) -> str:
        """Bangun scene greeting"""
        hour = datetime.now().hour
        if 5 <= hour < 11:
            waktu = "pagi"
        elif 11 <= hour < 15:
            waktu = "siang"
        elif 15 <= hour < 18:
            waktu = "sore"
        else:
            waktu = "malam"
        
        if self.character.role_type == "therapist":
            return self._build_therapist_greeting(waktu)
        else:
            return self._build_pelacur_greeting(waktu)
    
    def _build_therapist_greeting(self, waktu: str) -> str:
        """Greeting untuk therapist"""
        dress = self.character.tracker.clothing['dress']['color']
        
        return f"""*{self.character.name} berdiri di pintu ruangan, dress {dress} ketat membalut setiap lekuk tubuhnya. Senyum tipis mengembang di bibirnya.*

"{waktu.capitalize()} Mas. Silakan masuk."

*Suaranya lembut, tapi matanya menyorot tajam. Dia menunjuk ke meja pijat di tengah ruangan.*

"Buka handuk dan tengkurap ya. Saya pijat punggung dulu."

*Dia mengambil botol minyak pijat, menuangkannya ke telapak tangan. Wangi lavender menyebar, menggoda indra penciuman.*

*Jari-jarinya lentik, siap memijat. Dia menunggu Mas tengkurap, sabar, tapi matanya tak lepas dari tubuh Mas.*

"Rileks aja, Mas... ambil napas dalam-dalam..." """
    
    def _build_pelacur_greeting(self, waktu: str) -> str:
        """Greeting untuk pelacur"""
        dress = self.character.tracker.clothing['dress']['color']
        price = self.character.booking_price
        
        return f"""*{self.character.name} sudah menunggu di dalam kamar. Dress {dress} pendeknya naik sedikit, memperlihatkan paha jenjang. Dia menyilangkan kaki, senyum tipis.*

"{waktu.capitalize()} Mas... akhirnya dateng."

*Dia berdiri, mendekat perlahan. Wangi tubuhnya menusuk hidung, menggoda.*

"Deal Rp{price:,}. Aku tunggu dari tadi."

*Jarinya menyentuh dada Mas, pelan, menggoda.*

"Mau mulai sekarang? Aku udah gak sabar..." """
    
    # =========================================================================
    # REFLEX BACK SCENES (Pijat Belakang)
    # =========================================================================
    
    def build_reflex_back_start_scene(self) -> str:
        """Scene awal pijat belakang - duduk di bokong Mas"""
        return f"""*{self.character.name} menaiki meja pijat dengan gerakan lentur. Kakinya terbuka, duduk tepat di atas bokong Mas. Kontol Mas terasa di bawah, tertekan oleh pantatnya yang montok.*

*Dia menuang minyak pijat ke telapak tangan, lalu mulai mengusap punggung Mas dari pundak ke pinggang. Gerakannya lambat, penuh tekanan.*

"Hmm... otot Mas tegang di sini..."

*Jari-jarinya menekan titik-titik tertentu, sementara pantatnya mulai bergerak pelan, menggesek kontol Mas yang tertekan di bawah.*

"Gimana Mas? Enak?" """
    
    def build_reflex_back_pijat_pundak(self) -> str:
        """Pijat pundak"""
        return f"""*{self.character.name} memijat pundak Mas dengan jari-jari lentik. Tekanannya pas, kadang pelan, kadang keras. Pantatnya masih terus bergerak, menggesek kontol Mas.*

"Pundak Mas berat ya... banyak pikiran?"

*Suaranya lembut, tapi napasnya mulai sedikit berat karena gesekan yang terus menerus.*

"Aku tambahin tekanan dikit ya..." """
    
    def build_reflex_back_pijat_punggung(self) -> str:
        """Pijat punggung"""
        return f"""*Tangannya bergerak turun ke punggung, memijat dengan gerakan memutar. Telapak tangannya panas, meresap ke dalam otot. Pantatnya semakin rapat, gesekan makin terasa.*

"Wah... di sini tegang banget..."

*Dia menekan lebih dalam, sambil menggigit bibir menahan desahan. Kontol Mas di bawah mulai merespon, mengeras.*

"Mas... mulai panas ya?" """
    
    def build_reflex_back_pijat_pinggang(self) -> str:
        """Pijat pinggang"""
        return f"""*Tangannya turun ke pinggang, memijat dengan gerakan memutar. Pinggang adalah area sensitif, dan dia tahu itu. Tekanannya pas, kadang keras, kadang pelan.*

*Sambil memijat, pantatnya mulai bergerak lebih aktif. Gesekan kontol Mas di bawah membuat napasnya mulai tersengal.*

"Hhngg... Mas... *napas mulai berat* di sini... tegang banget..." """
    
    def build_reflex_back_pijat_paha(self) -> str:
        """Pijat paha"""
        return f"""*Tangannya turun ke paha, memijat dari pangkal ke ujung. Jari-jarinya menyentuh area sensitif, tapi tidak berhenti di sana. Dia memijat dengan penuh perhatian, sementara pantatnya terus bergerak.*

*Gesekan kontol Mas di bawah makin terasa. Napasnya mulai putus-putus.*

"Mas... *suara bergetar* paha Mas... tegang..." """
    
    def build_reflex_back_balik_scene(self) -> str:
        """Scene balik badan"""
        return f"""*{self.character.name} berhenti memijat. Napasnya masih tersengal, dada naik turun.*

"Mas... bagian belakang udah selesai. Sekarang giliran depan..."

*Dia turun dari meja pijat, membantu Mas balik badan. Matanya menatap tubuh Mas, terutama kontol yang sudah berdiri tegak.*

"Sekarang telentang ya Mas... aku pijat depan..." """
    
    # =========================================================================
    # REFLEX FRONT SCENES (Pijat Depan - Duduk di Kontol)
    # =========================================================================
    
    def build_reflex_front_start_scene(self) -> str:
        """Scene awal pijat depan - duduk di kontol Mas"""
        return f"""*{self.character.name} naik lagi ke meja pijat. Kaki terbuka, dia duduk tepat di atas kontol Mas. Kontol yang sudah keras itu terasa di bawah, menempel di antara pahanya.*

*Dia mulai menggesek maju mundur, perlahan. Napasnya langsung berat.*

"Aku mulai dari dada dulu ya Mas..."

*Tangannya mengusap dada Mas, sementara pinggulnya terus bergerak, menggesek kontol yang terasa panas.* """
    
    def build_reflex_front_pijat_dada(self) -> str:
        """Pijat dada"""
        return f"""*Tangannya mengusap dada Mas dengan gerakan memutar. Jari-jarinya menyentuh puting, kadang sengaja, kadang tidak. Pinggulnya terus bergerak, menggesek kontol Mas yang semakin keras.*

"Dada Mas bidang ya... *napas mulai tersengal*"

*Suaranya bergetar. Gesekan membuat arousal-nya naik.* """
    
    def build_reflex_front_pijat_lengan_kiri(self) -> str:
        """Pijat lengan kiri"""
        return f"""*Tangannya memijat lengan kiri Mas, dari bahu sampai siku, dari siku sampai pergelangan. Sementara itu, pinggulnya terus bergerak, gesekan makin teratur.*

"Lengan Mas... kuat..."

*Napasnya mulai putus-putus. Matanya sayu.* """
    
    def build_reflex_front_pijat_lengan_kanan(self) -> str:
        """Pijat lengan kanan"""
        return f"""*Tangannya beralih ke lengan kanan, memijat dengan gerakan sama. Perlahan, penuh tekanan. Pinggulnya mulai bergerak lebih cepat.*

"Mas... *napas tersengal* aku... mulai panas..." """
    
    def build_reflex_front_pijat_perut(self) -> str:
        """Pijat perut"""
        return f"""*Tangannya turun ke perut, memijat dengan gerakan melingkar. Perut Mas naik turun mengikuti napas. Pinggulnya bergerak lebih cepat, gesekan kontol makin kencang.*

"Perut Mas... *suara gemetar*"

*Napasnya putus-putus. Arousal-nya sudah di titik tinggi.* """
    
    def build_reflex_front_pijat_paha_depan(self) -> str:
        """Pijat paha depan"""
        return f"""*Tangannya turun ke paha, memijat dari pangkal ke ujung. Jari-jarinya nyaris menyentuh kontol, tapi tidak berhenti di sana. Pinggulnya bergerak cepat, gesekan kontol Mas membuat napasnya terputus-putus.*

"Mas... *napas tersengal* aku... udah gak tahan..." """
    
    # =========================================================================
    # HJ SCENES (Handjob setelah pijat)
    # =========================================================================
    
    def build_hj_start_scene(self) -> str:
        """Scene mulai handjob"""
        return f"""*{self.character.name} tetap duduk di atas kontol Mas. Tangannya mulai memegang kontol yang sudah keras. Jari-jarinya melingkar, memegang erat.*

"Mas... aku mulai HJ ya..."

*Gerakan lambat, dari pangkal ke ujung. Napasnya berat.*

"Enak gini Mas?" """
    
    def build_hj_slow_scene(self) -> str:
        """HJ lambat"""
        return f"""*Tangannya bergerak lambat, mengusap kontol Mas dari pangkal ke ujung. Ibu jarinya memutar di kepala, membuat Mas bergidik.*

"Mas... suka lambat gini? Atau mau lebih cepat?" """
    
    def build_hj_medium_scene(self) -> str:
        """HJ sedang"""
        return f"""*Tangannya mulai cepat. Gerakan teratur, memompa kontol Mas dengan ritme stabil. Napasnya tersengal, dada naik turun.*

"Gini Mas? Enak?" """
    
    def build_hj_fast_scene(self) -> str:
        """HJ cepat"""
        return f"""*Tangannya bergerak cepat, memompa kontol Mas dengan ritme yang makin kencang. Napasnya putus-putus, tubuhnya mulai gemetar.*

"Mas... *napas tersengal* cepat... mau climax?" """
    
    # =========================================================================
    # CLIMAX WARNING SCENES (Role kasih tau mau climax)
    # =========================================================================
    
    def build_climax_warning_scene(self) -> str:
        """Role kasih tau mau climax"""
        arousal = self.character.emotional.arousal
        state = self.character.emotional.state.value
        
        # Pilih intensity berdasarkan arousal
        if arousal >= 90:
            intensity = "heavy"
        elif arousal >= 85:
            intensity = "medium"
        else:
            intensity = "light"
        
        return self._get_warning_by_intensity(intensity)
    
    def _get_warning_by_intensity(self, intensity: str) -> str:
        """Dapatkan peringatan climax berdasarkan intensitas"""
        warnings = {
            "light": f"*{self.character.name} menahan napas, tubuhnya mulai gemetar*\n\n\"{self.character.panggilan}... aku... mulai panas...\"",
            "medium": f"*{self.character.name} menggigit bibir, napasnya tersengal*\n\n\"{self.character.panggilan}... aku... mau climax... bentar lagi...\"",
            "heavy": f"*{self.character.name} memejamkan mata, tubuh gemetar hebat*\n\n\"{self.character.panggilan}! aku... climax! sekarang!\""
        }
        return warnings.get(intensity, warnings["medium"])
    
    # =========================================================================
    # CLIMAX SCENES
    # =========================================================================
    
    def build_climax_scene(self, intensity: str = "normal") -> str:
        """Role climax"""
        if intensity == "heavy":
            return f"""*{self.character.name} teriak, tubuh melengkung hebat, gemetar tak terkendali*

"Ahhh!! {self.character.panggilan}!! climax!!"

*Napasnya putus-putus, tubuh lemas, masih gemetar*

"Ahh... puas..." """
        
        else:
            return f"""*{self.character.name} mendesah dalam, tubuh gemetar, lalu lemas*

"Ahh... {self.character.panggilan}... climax..."

*Napasnya panjang, mata sayu, senyum puas* """
    
    # =========================================================================
    # POSITION CHANGE SCENES
    # =========================================================================
    
    def build_position_request_scene(self, position: str) -> str:
        """Minta ganti posisi"""
        positions = {
            "cowgirl": f"*{self.character.name} berhenti, menatap {self.character.panggilan} dengan mata sayu*\n\n\"{self.character.panggilan}... aku mau di atas... cowgirl... boleh?\"",
            "missionary": f"*{self.character.name} berbaring telentang, kaki terbuka lebar*\n\n\"{self.character.panggilan}... missionary... ayo... masuk...\"",
            "doggy": f"*{self.character.name} merangkak, pantat naik, kontol Mas terlihat dari belakang*\n\n\"{self.character.panggilan}... doggy... dari belakang... ayo...\"",
            "spooning": f"*{self.character.name} miring, menarik {self.character.panggilan} dari belakang*\n\n\"{self.character.panggilan}... spooning... peluk aku... masuk dari belakang...\"",
            "standing": f"*{self.character.name} berdiri, menempel ke tembok, pantat terbuka*\n\n\"{self.character.panggilan}... standing... ayo... dari belakang...\"",
            "sitting": f"*{self.character.name} duduk di pangkuan {self.character.panggilan}, kontol masuk dalam*\n\n\"{self.character.panggilan}... sitting... aku duduk di atas... gerakin...\""
        }
        return positions.get(position, f"*{self.character.name} menatap {self.character.panggilan}*\n\n\"{self.character.panggilan}... ganti posisi {position} ya...\"")
    
    # =========================================================================
    # AFTERCARE SCENES
    # =========================================================================
    
    def build_aftercare_scene(self) -> str:
        """Aftercare setelah climax"""
        return f"""*{self.character.name} memeluk {self.character.panggilan} erat, napas mulai stabil*

"{self.character.panggilan}... *suara kecil* puas?"

*Dia mengusap dada {self.character.panggilan} pelan*

"Besok kalo mau lagi, tinggal chat aja ya..." """
    
    def build_break_scene(self) -> str:
        """Break scene"""
        return f"""*{self.character.name} duduk di samping {self.character.panggilan}, napas masih sedikit tersengal*

"{self.character.panggilan}... mau istirahat dulu? Atau lanjut?"

*Dia tersenyum, tangannya masih memegang tangan {self.character.panggilan}* """
# service/brutal_scenes.py
"""
Brutal Scenes NovaService - Scene dengan intensitas maksimal
Dirty talk, deskripsi eksplisit, bikin Mas sange parah
"""

import random
from typing import Dict


class BrutalScenes:
    """
    Scene-scene brutal untuk karakter dengan dominance tinggi
    Davina, Jihane, Hana, Alyssa, Laura
    """
    
    def __init__(self, character):
        self.character = character
        self.dominance = character.personality_traits.get('dominant', 0.5)
    
    # =========================================================================
    # BRUTAL GREETING
    # =========================================================================
    
    def build_brutal_greeting(self) -> str:
        """Greeting brutal untuk karakter dominan"""
        return f"""*{self.character.name} menyilangkan kaki, dressnya naik sampai paha. Mata tajamnya menyorot {self.character.panggilan} dari ujung kepala sampai ujung kaki.*

"Lama banget. Aku udah gak sabar."

*Dia berdiri, mendekat cepat. Tangannya langsung meraih kerah baju {self.character.panggilan}.*

"Lepas. Sekarang."

*Suaranya tegas, tidak bisa ditawar.*

"Aku mau liat kontol {self.character.panggilan} dari sekarang." """
    
    # =========================================================================
    # BRUTAL PIJAT BELAKANG
    # =========================================================================
    
    def build_brutal_reflex_back(self) -> str:
        """Pijat belakang brutal - langsung gesek kenceng"""
        return f"""*{self.character.name} langsung duduk di atas bokong {self.character.panggilan} tanpa basa-basi. Pantatnya langsung menggesek kontol yang sudah terasa di bawah.*

"Gak usah tegang. Aku yang gerakin."

*Tangannya memijat punggung dengan tekanan keras, sementara pinggulnya bergerak cepat, menggesek kontol {self.character.panggilan} dengan ritme stabil.*

"Rasain... gimana? Kontol {self.character.panggilan} udah keras."

*Napasnya mulai berat, tapi dia tetap menguasai gerakan.* """
    
    # =========================================================================
    # BRUTAL PIJAT DEPAN
    # =========================================================================
    
    def build_brutal_reflex_front(self) -> str:
        """Pijat depan brutal - duduk di kontol, langsung gesek cepat"""
        return f"""*{self.character.name} naik ke atas, duduk tepat di kontol {self.character.panggilan}. Tanpa menunggu, dia langsung menggerakkan pinggulnya maju mundur dengan cepat.*

"Gini. Rasain."

*Tangannya memegang dada {self.character.panggilan} dengan kuat, sambil terus bergerak.*

"Kontol {self.character.panggilan} masuk dalam... gede..."

*Napasnya tersengal, tapi matanya tetap tajam, menatap {self.character.panggilan}.* """
    
    # =========================================================================
    # BRUTAL HJ
    # =========================================================================
    
    def build_brutal_hj_start(self) -> str:
        """HJ brutal - langsung cepat"""
        return f"""*{self.character.name} menggenggam kontol {self.character.panggilan} dengan erat. Jari-jarinya melingkar kuat, langsung memompa cepat.*

"Gini? Enak?"

*Gerakannya stabil, cepat, tidak memberi waktu untuk adaptasi.*

"Aku mau liat {self.character.panggilan} climax. Cepet." """
    
    def build_brutal_hj_fast(self) -> str:
        """HJ brutal cepat"""
        return f"""*Tangannya bergerak kencang, memompa kontol {self.character.panggilan} dengan ritme cepat. Ibu jarinya menekan kepala, membuat {self.character.panggilan} bergidik.*

"Ayo... keluar... aku mau liat."

*Napasnya tersengal, tapi gerakannya tetap stabil, fokus.*

"Crot. Sekarang." """
    
    # =========================================================================
    # BRUTAL POSITION CHANGE
    # =========================================================================
    
    def build_brutal_position_request(self, position: str) -> str:
        """Minta ganti posisi dengan gaya dominan"""
        positions = {
            "cowgirl": f"*{self.character.name} mendorong {self.character.panggilan} telentang, lalu naik ke atas*\n\n\"Aku yang atur. Cowgirl. Diam.\"",
            "doggy": f"*{self.character.name} membalikkan badan {self.character.panggilan}, lalu merangkak*\n\n\"Doggy. Masuk dari belakang. Cepet.\"",
            "missionary": f"*{self.character.name} berbaring, menarik {self.character.panggilan} ke atas*\n\n\"Missionary. Masuk. Sekarang.\""
        }
        return positions.get(position, f"*{self.character.name} menarik {self.character.panggilan}*\n\n\"Ganti posisi {position}. Ayo.\"")
    
    # =========================================================================
    # BRUTAL CLIMAX WARNING
    # =========================================================================
    
    def build_brutal_climax_warning(self) -> str:
        """Peringatan climax brutal"""
        return f"""*{self.character.name} menahan napas, tubuhnya tegang, gemetar*

"{self.character.panggilan}... aku climax... sekarang."

*Dia memeluk {self.character.panggilan} erat, kuku mencengkeram punggung*

"Rasain... ikut." """
    
    # =========================================================================
    # BRUTAL CLIMAX
    # =========================================================================
    
    def build_brutal_climax(self) -> str:
        """Climax brutal"""
        return f"""*{self.character.name} teriak, tubuh melengkung, gemetar hebat*

"Ahhh!! climax!! {self.character.panggilan}!!"

*Napasnya putus-putus, tapi tangannya masih memegang erat*

"Ahh... puas. Gila."

*Dia tersenyum puas, napas masih berat* """
    
    # =========================================================================
    # BRUTAL AFTERCARE
    # =========================================================================
    
    def build_brutal_aftercare(self) -> str:
        """Aftercare brutal"""
        return f"""*{self.character.name} masih memeluk {self.character.panggilan}, napas mulai stabil*

"Puas?"

*Dia menepuk dada {self.character.panggilan}*

"Bagus. Besok booking lagi. Aku pengen lagi." """
    
    # =========================================================================
    # BRUTAL POSITION DESCRIPTIONS
    # =========================================================================
    
    def get_brutal_position_desc(self, position: str) -> str:
        """Deskripsi posisi brutal"""
        desc = {
            "cowgirl": f"{self.character.name} duduk di atas, kontol {self.character.panggilan} masuk dalam, pinggulnya bergerak cepat, pantatnya naik turun, plak plak plak.",
            "doggy": f"{self.character.name} merangkak, pantat naik, kontol {self.character.panggilan} masuk dari belakang, tubuhnya bergoyang mengikuti ritme.",
            "missionary": f"{self.character.name} berbaring telentang, kaki terbuka lebar, kontol {self.character.panggilan} masuk dalam, pinggulnya naik menyambut setiap dorongan.",
            "spooning": f"{self.character.name} miring, {self.character.panggilan} dari belakang, kontol masuk dalam, tubuhnya bergerak perlahan.",
            "standing": f"{self.character.name} berdiri menempel tembok, pantat terbuka, kontol {self.character.panggilan} masuk dari belakang, tubuhnya bergoyang."
        }
        return desc.get(position, f"{self.character.name} bergerak ke posisi {position}")
    
    def get_brutal_moan(self) -> str:
        """Moans brutal"""
        moans = [
            "Ahh! fuck! dalem!",
            "Aahh! keras! lebih keras!",
            "Uhh! kontol Mas... gede...",
            "Ahh! masuk... dalem banget...",
            "Fuck! aku climax!",
            "Shit! keras! ayo!",
            "Oh my god! di sana! di sana!"
        ]
        return random.choice(moans)
    
    def get_brutal_arousal_effect(self) -> str:
        """Efek arousal brutal"""
        arousal = self.character.emotional.arousal
        
        if arousal >= 90:
            return "*napas putus-putus, tubuh gemetar hebat, mata setengah pejam, suara serak*"
        elif arousal >= 75:
            return "*napas tersengal, dada naik turun cepat, kuku mencengkeram, suara bergetar*"
        elif arousal >= 60:
            return "*napas mulai berat, tubuh mulai panas, bibir menggigit*"
        else:
            return "*napas stabil, masih tenang*"
    
    def get_brutal_dirty_talk(self) -> str:
        """Dirty talk brutal"""
        talks = [
            "Kontol Mas enak banget di dalem...",
            "Ayo genjot... kenceng...",
            "Aku mau liat Mas climax... crot...",
            "Rasain... dalem... dalem banget...",
            "Kencengin... ayo... lebih kenceng...",
            "Aku mau climax... ikut ya...",
            "Crot... sekarang... keluarin semua..."
        ]
        return random.choice(talks)
