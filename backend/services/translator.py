import requests
import json
import os
from datetime import datetime
import urllib.parse

class LyricsTranslator:
    def __init__(self):
        self.saved_lyrics_file = "saved_translations.json"
        
        # Comprehensive language support
        self.language_map = {
            'es': 'Spanish', 'en': 'English', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ja': 'Japanese', 'ko': 'Korean',
            'zh': 'Chinese', 'ru': 'Russian', 'ar': 'Arabic', 'hi': 'Hindi',
            'bn': 'Bengali', 'pa': 'Punjabi', 'te': 'Telugu', 'mr': 'Marathi',
            'ta': 'Tamil', 'ur': 'Urdu', 'gu': 'Gujarati', 'kn': 'Kannada',
            'ml': 'Malayalam', 'or': 'Odia', 'ne': 'Nepali', 'si': 'Sinhala',
            'th': 'Thai', 'vi': 'Vietnamese', 'id': 'Indonesian', 'ms': 'Malay',
            'tr': 'Turkish', 'pl': 'Polish', 'nl': 'Dutch', 'sv': 'Swedish'
        }
    
    # ========== NEW METHOD - ADD THIS ==========
    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> dict:
        """
        Main translate method that matches what main.py expects.
        """
        try:
            translated_text = self.translate_lyrics(text, source_lang, target_lang)
            
            if "unavailable" in translated_text.lower() or "error" in translated_text.lower():
                lang_names = {
                    'en': 'English', 'hi': 'Hindi', 'es': 'Spanish', 'fr': 'French',
                    'de': 'German', 'it': 'Italian', 'pt': 'Portuguese', 'ja': 'Japanese',
                    'ko': 'Korean', 'zh': 'Chinese', 'ru': 'Russian', 'ar': 'Arabic'
                }
                target_name = lang_names.get(target_lang, target_lang)
                translated_text = f"[{target_name}] {text}"
            
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
            print(f"Translation error: {e}")
            return {
                "original": text,
                "translated": f"[Translation unavailable] {text}",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "detected_lang": None
            }
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        if any('\u0900' <= c <= '\u097F' for c in text):
            return "hi"
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            return "zh"
        if any('\u0600' <= c <= '\u06FF' for c in text):
            return "ar"
        if any('\u0E00' <= c <= '\u0E7F' for c in text):
            return "th"
        return "en"
    # ========== END OF NEW METHOD ==========
    
    def translate_lyrics(self, text, source_lang='auto', target_lang='en'):
        """Translate using multiple fallback APIs"""
        
        methods = [
            self._translate_lingva,
            self._translate_libretranslate,
            self._translate_simple_google
        ]
        
        for method in methods:
            try:
                result = method(text, source_lang, target_lang)
                if result and "error" not in result.lower():
                    return result
            except:
                continue
        
        return "Translation temporarily unavailable. Please check your internet connection."
    
    def _translate_lingva(self, text, source_lang, target_lang):
        """Use Lingva Translate"""
        try:
            instances = [
                f"https://lingva.ml/api/v1/{source_lang}/{target_lang}/{urllib.parse.quote(text)}",
                f"https://translate.plausibility.cloud/api/v1/{source_lang}/{target_lang}/{urllib.parse.quote(text)}"
            ]
            
            for instance in instances:
                try:
                    response = requests.get(instance, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        return data.get('translation', text)
                except:
                    continue
            return None
        except:
            return None
    
    def _translate_libretranslate(self, text, source_lang, target_lang):
        """Use LibreTranslate"""
        try:
            url = "https://translate.argosopentech.com/translate"
            payload = {
                "q": text,
                "source": source_lang if source_lang != 'auto' else 'auto',
                "target": target_lang,
                "format": "text"
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                return response.json().get('translatedText', text)
            return None
        except:
            return None
    
    def _translate_simple_google(self, text, source_lang, target_lang):
        """Simple Google Translate fallback"""
        try:
            url = "https://clients5.google.com/translate_a/t"
            params = {
                "client": "dict-chrome-ex",
                "sl": source_lang if source_lang != 'auto' else 'auto',
                "tl": target_lang,
                "q": text
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0][0]
            return None
        except:
            return None
    
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
            print(f"Error saving translation: {e}")
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
        """Generate pronunciation guide"""
        text_lower = text.lower()
        
        guides = {
            'hi': {
                'guide': text_lower,
                'tips': [
                    "🇮🇳 Hindi uses Devanagari script",
                    "🔊 'क' sounds like 'ka', 'ख' like 'kha'",
                    "💡 Practice with common words: नमस्ते (Namaste)"
                ]
            },
            'es': {
                'guide': text_lower.replace('ll', 'y').replace('ñ', 'ny'),
                'tips': [
                    "🇪🇸 'LL' sounds like 'Y' in 'yes'",
                    "🇪🇸 'Ñ' sounds like 'NY' in 'canyon'"
                ]
            }
        }
        
        guide_info = guides.get(lang, {
            'guide': text_lower,
            'tips': [
                "🔊 Break words into syllables",
                "🔊 Practice slowly at first",
                "🔊 Listen to native speakers"
            ]
        })
        
        return {
            "text": text,
            "guide": guide_info['guide'],
            "tips": guide_info['tips'],
            "language": self.language_map.get(lang, lang)
        }