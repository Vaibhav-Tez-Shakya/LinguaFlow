from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import json
import os
import sys
from datetime import datetime

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# FIXED IMPORT - no 'backend.' prefix
from services.translator import LyricsTranslator

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize translator
translator = LyricsTranslator()

# File for storing translations
SAVED_FILE = os.path.join(os.path.dirname(__file__), "saved_translations.json")

# ============================================
# FIND FRONTEND PATH
# ============================================

def find_frontend_path():
    """Automatically find where index.html is located"""
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend/public"),
        os.path.join(os.path.dirname(__file__), "../frontend/public"),
        os.path.join(os.getcwd(), "frontend/public"),
    ]
    
    for path in possible_paths:
        full_path = os.path.abspath(path)
        index_file = os.path.join(full_path, "index.html")
        if os.path.exists(index_file):
            print(f"✅ Found frontend at: {full_path}")
            return full_path
    
    print("⚠️ Frontend not found - API will work but web UI won't load")
    return None

FRONTEND_PATH = find_frontend_path()

if FRONTEND_PATH:
    app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")

# ============================================
# API Endpoints
# ============================================

def load_saved_translations():
    if os.path.exists(SAVED_FILE):
        with open(SAVED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"translations": []}

def save_translations(data):
    with open(SAVED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "en"
    song_id: str = "web_translation"

class TranslateResponse(BaseModel):
    original: str
    translated: str
    source_lang: str
    target_lang: str
    detected_lang: Optional[str] = None

class SaveRequest(BaseModel):
    original: str
    translated: str
    source_lang: str
    target_lang: str

class ShareRequest(BaseModel):
    original: str
    translated: str
    platform: str

class PronunciationRequest(BaseModel):
    text: str
    lang: str

@app.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate text between languages"""
    try:
        result = translator.translate(
            request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save")
async def save_translation(request: SaveRequest):
    """Save translation to library"""
    data = load_saved_translations()
    
    lang_names = {
        'en': 'English', 'hi': 'Hindi', 'es': 'Spanish', 'fr': 'French',
        'de': 'German', 'it': 'Italian', 'pt': 'Portuguese', 'ja': 'Japanese',
        'ko': 'Korean', 'zh': 'Chinese', 'ru': 'Russian', 'ar': 'Arabic'
    }
    
    translation_entry = {
        "id": len(data["translations"]) + 1,
        "original": request.original,
        "translated": request.translated,
        "source_lang": request.source_lang,
        "source_lang_name": lang_names.get(request.source_lang, request.source_lang),
        "target_lang": request.target_lang,
        "target_lang_name": lang_names.get(request.target_lang, request.target_lang),
        "timestamp": datetime.now().isoformat()
    }
    
    data["translations"].insert(0, translation_entry)
    data["translations"] = data["translations"][:100]
    save_translations(data)
    
    return {"success": True, "id": translation_entry["id"]}

@app.get("/saved")
async def get_saved_translations():
    """Get all saved translations"""
    return load_saved_translations()

@app.post("/share")
async def share_translation(request: ShareRequest):
    """Generate share URLs for social media"""
    import requests.utils
    text = f"Translation: {request.original} → {request.translated}"
    encoded_text = requests.utils.quote(text)
    
    urls = {
        "twitter": f"https://twitter.com/intent/tweet?text={encoded_text}",
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u=&quote={encoded_text}",
        "whatsapp": f"https://wa.me/?text={encoded_text}"
    }
    
    return {"share_url": urls.get(request.platform, urls["twitter"])}

@app.post("/pronunciation")
async def get_pronunciation(request: PronunciationRequest):
    """Generate pronunciation guide"""
    guide = {
        "es": f"Pronunciation for '{request.text}' in Spanish",
        "hi": f"उच्चारण: {request.text}",
        "en": f"Pronunciation: {request.text}",
        "fr": f"Prononciation: {request.text}",
        "de": f"Aussprache: {request.text}"
    }
    
    tips = {
        "es": ["Roll your R's", "Stress the second-to-last syllable"],
        "hi": ["Use soft sounds", "Aspirate consonants"],
        "en": ["Use schwa for unstressed vowels", "Stress content words"],
        "fr": ["Use nasal vowels", "Silent final consonants"],
        "de": ["Pronounce 'ch' as in 'Bach'", "Umlauts change vowel sounds"]
    }
    
    return {
        "text": request.text,
        "guide": guide.get(request.lang, f"Pronunciation guide for '{request.text}'"),
        "tips": tips.get(request.lang, ["Listen to native speakers", "Practice slowly"])
    }

# ============================================
# SERVE FRONTEND
# ============================================

@app.get("/")
@app.get("/index.html")
async def serve_frontend():
    """Serve the main HTML file"""
    if FRONTEND_PATH:
        index_path = os.path.join(FRONTEND_PATH, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    
    return {"message": "Frontend not found. API is working at /translate, /save, /saved"}

# ============================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"\n🚀 Server starting on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)