import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
import logging
from config import Config

logger = logging.getLogger(__name__)

class SpotifyClient:
    def __init__(self):

        if Config.SPOTIFY_CLIENT_ID and Config.SPOTIFY_CLIENT_SECRET:
            try:
                credentials = SpotifyClientCredentials(
                    client_id=Config.SPOTIFY_CLIENT_ID,
                    client_secret=Config.SPOTIFY_CLIENT_SECRET
                )
                self.sp = spotipy.Spotify(client_credentials_manager=credentials)
                logger.info("spotify authentication success")
            except Exception as e:
                logger.warning(f"spotify authentication error: {e}")
                self.sp = spotipy.Spotify()
        else:
            self.sp = spotipy.Spotify()
            logger.info("spotify anonymous mode - public playlists only")
    
    def extract_playlist_id(self, url: str) -> str:
        patterns = [
            r'https://open\.spotify\.com/playlist/([a-zA-Z0-9]+)',
            r'spotify:playlist:([a-zA-Z0-9]+)',
            r'^([a-zA-Z0-9]+)$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"invalid spotify url: {url}")
    
    async def get_playlist_tracks(self, playlist_url: str) -> list:
        try:
            playlist_id = self.extract_playlist_id(playlist_url)
            logger.info(f"extracted playlist id: {playlist_id}")
            
            try:
                playlist = self.sp.playlist(playlist_id)
                logger.info(f"playlist: {playlist['name']} by {playlist['owner']['display_name']}")
            except Exception as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    raise ValueError(f"playlist not found or private.")
                else:
                    raise e
            
            tracks = []
            
            try:
                results = self.sp.playlist_tracks(playlist_id)
            except Exception as e:
                if "404" in str(e):
                    raise ValueError("authentication needed for this playlist.")
                else:
                    raise e
            
            while results:
                for item in results['items']:
                    if item['track'] and item['track']['type'] == 'track':
                        track = item['track']
                        
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
                        logger.debug(f"added: {track_info['artist']} - {track_info['title']}")
                
                if results['next']:
                    results = self.sp.next(results)
                else:
                    break
            
            logger.info(f"found {len(tracks)} tracks")
            return tracks
            
        except Exception as e:
            logger.error(f"error while getting playlist informations: {e}")
            raise
    
    # def clean_search_query(self, track: dict) -> str:
    #     artist = track['artist']
    #     title = track['title']
        
    #     artist = re.sub(r'\([^)]*\)', '', artist).strip()
    #     title = re.sub(r'\([^)]*\)', '', title).strip()
    #     title = re.sub(r'\[[^\]]*\]', '', title).strip()
        
    #     title = re.sub(r'\s+(feat|ft|featuring)\.?\s+.*', '', title, flags=re.IGNORECASE)
        
    #     return f"{artist} {title}".strip()