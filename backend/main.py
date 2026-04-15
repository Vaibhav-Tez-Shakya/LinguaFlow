from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional
from backend.services.translator import LyricsTranslator
from backend.services.spotify_service import SpotifyService
import os
import json

app = FastAPI(title="Universal Lyrics Translation API", version="4.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

translator = LyricsTranslator()
spotify = SpotifyService()

class TranslateRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "auto"
    target_lang: str = "en"
    song_id: Optional[str] = ""

class SaveRequest(BaseModel):
    original: str
    translated: str
    source_lang: str
    target_lang: str

class SocialShareRequest(BaseModel):
    original: str
    translated: str
    platform: str

class PronunciationRequest(BaseModel):
    text: str
    lang: Optional[str] = "es"

class TTSRequest(BaseModel):
    text: str
    lang: str = "en"

@app.get("/")
async def root():
    html_path = os.path.join("frontend", "public", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    return {"message": "Universal Lyrics Translation API is running!"}

@app.get("/spotify/login")
async def spotify_login():
    """Get Spotify login URL"""
    auth_url = spotify.get_auth_url()
    return {"auth_url": auth_url}

@app.get("/callback")
async def spotify_callback(code: str):
    """Handle Spotify callback"""
    success = spotify.authenticate(code)
    if success:
        return RedirectResponse(url="/?spotify_connected=true")
    return JSONResponse({"error": "Authentication failed"}, status_code=400)

@app.get("/spotify/current")
async def get_current_song():
    """Get currently playing song from Spotify"""
    try:
        song = spotify.get_current_song()
        if song:
            # Search for lyrics
            lyrics = spotify.search_lyrics(song['name'], song['artist'])
            return {
                "success": True,
                "song": song,
                "lyrics": lyrics
            }
        return {
            "success": False,
            "message": "No song currently playing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spotify/lyrics")
async def get_song_lyrics(song_name: str, artist_name: str):
    """Get lyrics for a specific song"""
    try:
        lyrics = spotify.search_lyrics(song_name, artist_name)
        if lyrics:
            return {"lyrics": lyrics, "success": True}
        return {"success": False, "message": "Lyrics not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate")
async def translate_lyrics(request: TranslateRequest):
    try:
        translated = translator.translate_lyrics(
            request.text, 
            request.source_lang, 
            request.target_lang
        )
        return {
            "song_id": request.song_id,
            "original": request.text,
            "translated": translated,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "source_lang_name": translator.language_map.get(request.source_lang, request.source_lang if request.source_lang != 'auto' else 'Auto-detected'),
            "target_lang_name": translator.language_map.get(request.target_lang, request.target_lang)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        return {
            "text": request.text,
            "lang": request.lang,
            "message": "Text-to-speech handled by browser"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save")
async def save_translation(request: SaveRequest):
    try:
        success = translator.save_translation(
            request.original,
            request.translated,
            request.source_lang,
            request.target_lang
        )
        if success:
            return {"message": "Translation saved successfully!", "success": True}
        else:
            return {"message": "Failed to save translation", "success": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/saved")
async def get_saved_translations():
    try:
        translations = translator.get_saved_translations()
        return {"translations": translations, "count": len(translations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pronunciation")
async def get_pronunciation(request: PronunciationRequest):
    try:
        guide = translator.get_pronunciation_guide(request.text, request.lang)
        return guide
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/share")
async def share_translation(request: SocialShareRequest):
    try:
        share_urls = {
            "twitter": f"https://twitter.com/intent/tweet?text={request.translated[:200]} - Translated&url=",
            "facebook": f"https://www.facebook.com/sharer/sharer.php?quote={request.translated[:200]}",
            "whatsapp": f"https://wa.me/?text={request.translated[:200]}"
        }
        
        if request.platform in share_urls:
            return {"share_url": share_urls[request.platform], "platform": request.platform}
        else:
            return {"error": "Platform not supported", "platforms": list(share_urls.keys())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages")
async def get_supported_languages():
    return {"languages": translator.language_map}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "4.0.0"}
