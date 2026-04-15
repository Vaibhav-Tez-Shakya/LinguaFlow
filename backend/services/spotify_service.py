import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv

load_dotenv()

class SpotifyService:
    def __init__(self):
        # You need to create a Spotify App at https://developer.spotify.com/dashboard
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID', 'YOUR_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8000/callback')
        
        self.sp = None
        self.token_info = None
        
    def get_auth_url(self):
        """Get Spotify authorization URL"""
        auth_url = f"https://accounts.spotify.com/authorize?client_id={self.client_id}&response_type=code&redirect_uri={self.redirect_uri}&scope=user-read-currently-playing user-read-playback-state"
        return auth_url
    
    def authenticate(self, code):
        """Authenticate with Spotify using authorization code"""
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope="user-read-currently-playing user-read-playback-state"
            )
            self.token_info = auth_manager.get_access_token(code)
            self.sp = spotipy.Spotify(auth=self.token_info['access_token'])
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def get_current_song(self):
        """Get currently playing song from Spotify"""
        try:
            if not self.sp:
                return None
            
            current = self.sp.current_user_playing_track()
            if current and current['is_playing']:
                track = current['item']
                return {
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'progress_ms': current['progress_ms'],
                    'track_id': track['id'],
                    'artist_id': track['artists'][0]['id'],
                    'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None
                }
            return None
        except Exception as e:
            print(f"Error getting current song: {e}")
            return None
    
    def search_lyrics(self, song_name, artist_name):
        """Search for lyrics using Genius API or alternative sources"""
        try:
            # Try Genius API first
            lyrics = self._search_genius_lyrics(song_name, artist_name)
            if lyrics:
                return lyrics
            
            # Fallback to AZLyrics
            lyrics = self._search_azlyrics(song_name, artist_name)
            if lyrics:
                return lyrics
            
            # Fallback to Musixmatch
            lyrics = self._search_musixmatch(song_name, artist_name)
            if lyrics:
                return lyrics
            
            return None
        except Exception as e:
            print(f"Error searching lyrics: {e}")
            return None
    
    def _search_genius_lyrics(self, song_name, artist_name):
        """Search lyrics using Genius API"""
        try:
            # Genius API requires a token (free)
            genius_token = os.getenv('GENIUS_ACCESS_TOKEN', '')
            if not genius_token:
                return None
            
            search_url = "https://api.genius.com/search"
            headers = {"Authorization": f"Bearer {genius_token}"}
            params = {"q": f"{song_name} {artist_name}"}
            
            response = requests.get(search_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['response']['hits']:
                    song_url = data['response']['hits'][0]['result']['url']
                    # Scrape lyrics from Genius page
                    lyrics = self._scrape_genius_lyrics(song_url)
                    return lyrics
            return None
        except:
            return None
    
    def _scrape_genius_lyrics(self, url):
        """Scrape lyrics from Genius page"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find lyrics container
            lyrics_div = soup.find('div', {'data-lyrics-container': 'true'})
            if lyrics_div:
                lyrics = lyrics_div.get_text()
                return lyrics.strip()
            return None
        except:
            return None
    
    def _search_azlyrics(self, song_name, artist_name):
        """Search lyrics from AZLyrics as fallback"""
        try:
            # Format for AZLyrics URL
            artist = artist_name.lower().replace(' ', '')
            song = song_name.lower().replace(' ', '')
            url = f"https://www.azlyrics.com/lyrics/{artist}/{song}.html"
            
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Find lyrics div
                lyrics_div = soup.find('div', {'class': 'lyricsh'})
                if lyrics_div:
                    # Find the next div with actual lyrics
                    lyrics = lyrics_div.find_next('div')
                    if lyrics:
                        return lyrics.get_text().strip()
            return None
        except:
            return None
    
    def _search_musixmatch(self, song_name, artist_name):
        """Search lyrics from Musixmatch API"""
        try:
            api_key = os.getenv('MUSIXMATCH_API_KEY', '')
            if not api_key:
                return None
            
            url = "https://api.musixmatch.com/ws/1.1/matcher.lyrics.get"
            params = {
                'q_track': song_name,
                'q_artist': artist_name,
                'apikey': api_key,
                'format': 'json'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['message']['body']['lyrics']:
                    return data['message']['body']['lyrics']['lyrics_body']
            return None
        except:
            return None
    
    def get_playback_state(self):
        """Get current playback state"""
        try:
            if not self.sp:
                return None
            
            playback = self.sp.current_playback()
            if playback:
                return {
                    'is_playing': playback['is_playing'],
                    'progress_ms': playback['progress_ms'],
                    'device_name': playback['device']['name']
                }
            return None
        except:
            return None
