import requests
import json
import os
from datetime import datetime

class LyricsTranslator:
    def __init__(self):
        self.saved_lyrics_file = "saved_translations.json"
        
        self.language_map = {
            'es': 'Spanish', 'en': 'English', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ja': 'Japanese', 'ko': 'Korean',
            'zh': 'Chinese', 'ru': 'Russian', 'ar': 'Arabic', 'hi': 'Hindi',
            'tr': 'Turkish', 'nl': 'Dutch', 'pl': 'Polish', 'vi': 'Vietnamese'
        }
        
        # Reverse map for language names to codes
        self.lang_code_map = {v.lower(): k for k, v in self.language_map.items()}
        self.lang_code_map.update({'spanish': 'es', 'english': 'en', 'french': 'fr', 
                                   'german': 'de', 'italian': 'it', 'portuguese': 'pt',
                                   'japanese': 'ja', 'korean': 'ko', 'chinese': 'zh',
                                   'russian': 'ru', 'arabic': 'ar', 'hindi': 'hi'})
    
    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> dict:
        """
        Translate text using free Google Translate API (no API key required)
        """
        try:
            # Validate target language
            if target_lang not in self.language_map and target_lang not in self.lang_code_map:
                target_lang = 'en'
            elif target_lang in self.lang_code_map:
                target_lang = self.lang_code_map[target_lang]
            
            # Handle auto detection
            detected_lang = None
            if source_lang == "auto" or source_lang not in self.language_map:
                detected_lang = self._detect_language_api(text)
                source_lang_code = detected_lang if detected_lang else 'auto'
            else:
                if source_lang in self.lang_code_map:
                    source_lang_code = self.lang_code_map[source_lang]
                else:
                    source_lang_code = source_lang
            
            # Call translation API
            translated_text = self._google_translate(text, source_lang_code, target_lang)
            
            return {
                "original": text,
                "translated": translated_text,
                "source_lang": source_lang if source_lang != "auto" else (detected_lang or "unknown"),
                "target_lang": target_lang,
                "detected_lang": detected_lang,
                "source_lang_name": self.language_map.get(source_lang if source_lang != "auto" else (detected_lang or "unknown"), source_lang),
                "target_lang_name": self.language_map.get(target_lang, target_lang)
            }
        except Exception as e:
            print(f"Translation error: {e}")
            return {
                "original": text,
                "translated": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "detected_lang": None,
                "error": str(e)
            }
    
    def _google_translate(self, text: str, source: str, target: str) -> str:
        """Use Google Translate's free API"""
        # Using translate.googleapis.com (no API key needed)
        url = "https://translate.googleapis.com/translate_a/single"
        
        params = {
            'client': 'gtx',
            'sl': source,
            'tl': target,
            'dt': 't',
            'q': text
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        translated = ''.join([part[0] for part in result[0] if part[0]])
        
        return translated
    
    def _detect_language_api(self, text: str) -> str:
        """Detect language using Google Translate API"""
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'tl': 'en',
                'dt': 't',
                'q': text[:200]  # Send first 200 chars for detection
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Language detection is in the response
            result = response.json()
            if len(result) > 2 and result[2]:
                return result[2]  # Detected language code
            return 'en'
        except:
            return self._simple_detect(text)
    
    def _simple_detect(self, text: str) -> str:
        """Fallback simple language detection"""
        # Hindi detection
        hindi_range = range(0x0900, 0x097F)
        if any(ord(c) in hindi_range for c in text):
            return "hi"
        
        # Common words detection
        text_lower = text.lower()
        if any(word in text_lower for word in ['namaste', 'mera', 'hai', 'kaise']):
            return "hi"
        if any(word in text_lower for word in ['hola', 'como', 'gracias', 'bueno']):
            return "es"
        if any(word in text_lower for word in ['bonjour', 'merci', 'comment']):
            return "fr"
        if any(word in text_lower for word in ['hallo', 'danke', 'guten']):
            return "de"
        
        return "en"
    
    def translate_lyrics(self, lyrics: str, target_lang: str = "en") -> dict:
        """
        Translate full lyrics (handles line by line for better results)
        """
        lines = lyrics.split('\n')
        translated_lines = []
        
        for line in lines:
            if line.strip():
                result = self.translate(line.strip(), "auto", target_lang)
                translated_lines.append(result['translated'])
            else:
                translated_lines.append('')
        
        translated_lyrics = '\n'.join(translated_lines)
        
        return {
            "original_lyrics": lyrics,
            "translated_lyrics": translated_lyrics,
            "target_lang": target_lang,
            "target_lang_name": self.language_map.get(target_lang, target_lang)
        }
    
    def save_translation(self, original, translated, source_lang, target_lang):
        """Save translation to file"""
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
        """Get all saved translations"""
        try:
            if os.path.exists(self.saved_lyrics_file):
                with open(self.saved_lyrics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def get_pronunciation_guide(self, text, lang='es'):
        """Get pronunciation guide (basic version)"""
        return {
            "text": text,
            "guide": text,
            "tips": ["Practice saying the words slowly", "Listen to native speakers"],
            "language": self.language_map.get(lang, lang)
        }


# Example usage
if __name__ == "__main__":
    translator = LyricsTranslator()
    
    # Test with various languages
    test_texts = [
        "Namaste, mera naam Vaibhav hai",
        "Hello, how are you?",
        "Hola, ¿cómo estás?",
        "Bonjour, comment allez-vous?",
        "今日は元気ですか"  # Japanese
    ]
    
    print("=== Translation Tests ===\n")
    
    for text in test_texts:
        result = translator.translate(text, "auto", "en")
        print(f"Original: {result['original']}")
        print(f"Translated: {result['translated']}")
        print(f"Detected: {result.get('detected_lang', 'N/A')}")
        print("-" * 50)
    
    # Test lyrics translation
    print("\n=== Lyrics Translation Test ===")
    lyrics = """Namaste
Mera naam Vaibhav hai
Kaise ho aap?
Main theek hoon"""

    lyrics_result = translator.translate_lyrics(lyrics, "en")
    print(f"Original Lyrics:\n{lyrics_result['original_lyrics']}")
    print(f"\nTranslated to {lyrics_result['target_lang_name']}:\n{lyrics_result['translated_lyrics']}")