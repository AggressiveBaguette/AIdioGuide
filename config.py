from enum import Enum

class Languages(Enum):
    fr_FR = ("fr-FR","fr-FR-Vivienne:DragonHDLatestNeural")
    en_US = ("en-US", "en-US-JennyMultilingualNeural")

    def __init__(self, code, voice_id):
        self.code = code
        self.voice_id = voice_id

    @classmethod
    def get_by_code(cls, code: str) -> "Languages":
        for lang in cls:
            if lang.code == code:
                return lang
        raise ValueError(f"Language {code} not available")

    @classmethod
    def list_all_codes(cls) -> list[str]:
        return [lang.code for lang in cls]

TTS_LANGUAGES_NO_PHONEMES = {
    "ar-EG", "ar-SA", "ca-ES", "cs-CZ", "da-DK", "de-AT", "de-CH", "de-DE", 
    "el-GR", "en-AU", "en-CA", "en-GB", "en-IE", "en-IN", "en-US", "es-ES", 
    "es-MX", "fi-FI", "fr-BE", "fr-CA", "fr-CH", "fr-FR", "he-IL", "hi-IN", 
    "hu-HU", "id-ID", "it-IT", "ja-JP", "ko-KR", "nb-NO", "nl-BE", "nl-NL", 
    "pl-PL", "pt-BR", "pt-PT", "ro-RO", "ru-RU", "sk-SK", "sv-SE", "th-TH", 
    "tr-TR", "uk-UA", "vi-VN", "zh-CN", "zh-HK", "zh-TW"
}
