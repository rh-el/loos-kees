import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
import logging
from config import Config

logger = logging.getLogger(__name__)

class SpotifyClient:
    def __init__(self):
        # Authentification Spotify (optionnelle pour playlists publiques)
        if Config.SPOTIFY_CLIENT_ID and Config.SPOTIFY_CLIENT_SECRET:
            try:
                credentials = SpotifyClientCredentials(
                    client_id=Config.SPOTIFY_CLIENT_ID,
                    client_secret=Config.SPOTIFY_CLIENT_SECRET
                )
                self.sp = spotipy.Spotify(client_credentials_manager=credentials)
                logger.info("Authentification Spotify réussie")
            except Exception as e:
                logger.warning(f"Échec de l'authentification Spotify: {e}")
                self.sp = spotipy.Spotify()
        else:
            # Mode sans authentification - fonctionne pour les playlists publiques
            self.sp = spotipy.Spotify()
            logger.info("Mode Spotify anonyme - playlists publiques uniquement")
    
    def extract_playlist_id(self, url: str) -> str:
        """Extrait l'ID de playlist depuis une URL Spotify"""
        patterns = [
            r'https://open\.spotify\.com/playlist/([a-zA-Z0-9]+)',
            r'spotify:playlist:([a-zA-Z0-9]+)',
            r'^([a-zA-Z0-9]+)$'  # ID direct
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"URL Spotify invalide: {url}")
    
    async def get_playlist_tracks(self, playlist_url: str) -> list:
        """Récupère toutes les tracks d'une playlist Spotify"""
        try:
            playlist_id = self.extract_playlist_id(playlist_url)
            logger.info(f"ID de playlist extrait: {playlist_id}")
            
            # Récupérer les informations de la playlist avec gestion d'erreur
            try:
                playlist = self.sp.playlist(playlist_id)
                logger.info(f"Playlist: {playlist['name']} par {playlist['owner']['display_name']}")
            except Exception as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    raise ValueError(f"Playlist non trouvée ou privée. Vérifiez que la playlist est publique et que l'URL est correcte.")
                else:
                    raise e
            
            tracks = []
            
            try:
                results = self.sp.playlist_tracks(playlist_id)
            except Exception as e:
                if "404" in str(e):
                    raise ValueError("Cette playlist nécessite une authentification Spotify. Ajoutez vos credentials dans le .env")
                else:
                    raise e
            
            while results:
                for item in results['items']:
                    if item['track'] and item['track']['type'] == 'track':
                        track = item['track']
                        
                        # Extraire les informations essentielles
                        track_info = {
                            'title': track['name'],
                            'artist': ', '.join([artist['name'] for artist in track['artists']]),
                            'album': track['album']['name'],
                            'duration_ms': track['duration_ms'],
                            'popularity': track['popularity'],
                            'spotify_id': track['id'],
                            'spotify_url': track['external_urls']['spotify']
                        }
                        
                        tracks.append(track_info)
                        logger.debug(f"Ajouté: {track_info['artist']} - {track_info['title']}")
                
                # Pagination
                if results['next']:
                    results = self.sp.next(results)
                else:
                    break
            
            logger.info(f"Récupéré {len(tracks)} tracks de la playlist")
            return tracks
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la playlist: {e}")
            raise
    
    def clean_search_query(self, track: dict) -> str:
        """Nettoie et formate une requête de recherche"""
        artist = track['artist']
        title = track['title']
        
        # Nettoyer les caractères spéciaux et parenthèses
        artist = re.sub(r'\([^)]*\)', '', artist).strip()
        title = re.sub(r'\([^)]*\)', '', title).strip()
        title = re.sub(r'\[[^\]]*\]', '', title).strip()
        
        # Supprimer les feat., ft., etc.
        title = re.sub(r'\s+(feat|ft|featuring)\.?\s+.*', '', title, flags=re.IGNORECASE)
        
        return f"{artist} {title}".strip()