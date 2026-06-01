import requests
import json
import os
from datetime import datetime
import urllib.parse

class LyricsTranslator:
    def __init__(self):
        self.saved_lyrics_file = "saved_translations.json"
        
        self.language_map = {
            'es': 'Spanish', 'en': 'English', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ja': 'Japanese', 'ko': 'Korean',
            'zh': 'Chinese', 'ru': 'Russian', 'ar': 'Arabic', 'hi': 'Hindi'
        }
    
    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> dict:
        try:
            print(f"Translating: {text} to {target_lang}")
            
            # Use Google Translate direct API
            translated_text = self._translate_google(text, source_lang, target_lang)
            
            if not translated_text or translated_text == text:
                translated_text = self._translate_mymemory(text, source_lang, target_lang)
            
            if not translated_text or translated_text == text:
                translated_text = f"[Translation] {text}"
            
            detected_lang = None
            if source_lang == "auto":
                detected_lang = self._detect_language(text)
            
            return {
                "original": text,
                "translated": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "detected_lang": detected_lang
            }
        except Exception as e:
            print(f"Error: {e}")
            return {
                "original": text,
                "translated": f"[Error] {text}",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "detected_lang": None
            }
    
    def _translate_google(self, text, source_lang, target_lang):
        try:
            source = source_lang if source_lang != 'auto' else 'auto'
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": source,
                "tl": target_lang,
                "dt": "t",
                "q": text
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and data[0] and len(data[0]) > 0:
                    return data[0][0][0]
            return None
        except Exception as e:
            print(f"Google translate error: {e}")
            return None
    
    def _translate_mymemory(self, text, source_lang, target_lang):
        try:
            source = source_lang if source_lang != 'auto' else 'en'
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text,
                "langpair": f"{source}|{target_lang}"
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                translated = data.get("responseData", {}).get("translatedText", text)
                if " [" in translated:
                    translated = translated.split(" [")[0]
                if translated and translated != text:
                    return translated
            return None
        except Exception as e:
            print(f"MyMemory error: {e}")
            return None
    
    def _detect_language(self, text: str) -> str:
        if any('\u0900' <= c <= '\u097F' for c in text):
            return "hi"
        return "en"
    
    def save_translation(self, original, translated, source_lang, target_lang):
        try:
            translations = []
            if os.path.exists(self.saved_lyrics_file):
                with open(self.saved_lyrics_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
            
            new_translation = {
                "id": len(translations) + 1,
                "timestamp": datetime.now().isoformat(),
                "original": original,
                "translated": translated,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_lang_name": self.language_map.get(source_lang, source_lang),
                "target_lang_name": self.language_map.get(target_lang, target_lang)
            }
            translations.append(new_translation)
            
            with open(self.saved_lyrics_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False
    
    def get_saved_translations(self):
        try:
            if os.path.exists(self.saved_lyrics_file):
                with open(self.saved_lyrics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def get_pronunciation_guide(self, text, lang='es'):
        text_lower = text.lower()
        
        guides = {
            'hi': {
                'guide': text_lower,
                'tips': [
                    "Hindi uses Devanagari script",
                    "Practice with common words: Namaste"
                ]
            },
            'es': {
                'guide': text_lower.replace('ll', 'y').replace('n', 'ny'),
                'tips': [
                    "LL sounds like Y in yes",
                    "N with tilde sounds like NY",
                    "Roll your R's"
                ]
            }
        }
        
        guide_info = guides.get(lang, {
            'guide': text_lower,
            'tips': [
                "Break words into syllables",
                "Practice slowly at first",
                "Listen to native speakers"
            ]
        })
        
        return {
            "text": text,
            "guide": guide_info['guide'],
            "tips": guide_info['tips'],
            "language": self.language_map.get(lang, lang)
        }