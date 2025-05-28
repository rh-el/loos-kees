import asyncio
import logging
import time
import unicodedata
import slskd_api 
import re
from config import Config
from urllib.parse import urlparse
import aiohttp


logger = logging.getLogger(__name__)

class SoulseekClient:
    def __init__(self):
        self.host = self._validate_host_url(Config.SLSKD_HOST)
        
        if Config.SLSKD_API_KEY:
            self.api = slskd_api.SlskdClient(
                host=self.host,
                username=Config.SLSKD_USERNAME,
                password=Config.SLSKD_PASSWORD,
                api_key=Config.SLSKD_API_KEY
            )
        else:
            self.api = slskd_api.SlskdClient(
                host=self.host,
                username=Config.SLSKD_USERNAME,
                password=Config.SLSKD_PASSWORD
            )
        self.connected = False
    
    def _validate_host_url(self, host):
        if not host:
            raise ValueError("SLSKD_HOST can not be empty")
        
        if not host.startswith(('http://', 'https://')):
            host = f"http://{host}"
        
        try:
            parsed = urlparse(host)
            if not parsed.netloc:
                raise ValueError(f"invalid url: {host}")
        except Exception as e:
            raise ValueError(f"url validation error {host}: {e}")
        
        return host
    
    async def connect(self):
        try:
            logger.info("Tentative de connexion à slskd...")
            
            await self._diagnose_connection()
            
            try:
                status = self.api.application.state()
                logger.info(f"slskd status: {status}")
            except Exception as api_error:
                logger.warning(f"Erreur API application.state(): {api_error}")
                # Essayer une autre méthode
                try:
                    version = self.api.application.version()
                    logger.info(f"slskd version: {version}")
                except Exception as version_error:
                    logger.error(f"Impossible d'obtenir la version: {version_error}")
                    raise
            
            # Vérifier et établir la connexion Soulseek
            await self._ensure_soulseek_connection()
            
            self.connected = True
            logger.info("Connecté à slskd avec succès")
            
        except Exception as e:
            logger.error(f"Erreur de connexion à slskd: {e}")
            logger.error(f"Configuration utilisée - Host: {self.host}, Username: {Config.SLSKD_USERNAME}")
            raise
    
    async def _ensure_soulseek_connection(self):
        """S'assurer que slskd est connecté au réseau Soulseek"""
        try:
            # Vérifier l'état de la connexion Soulseek
            server_state = self.api.server.state()
            logger.info(f"État du serveur Soulseek: {server_state}")
            
            if server_state.get('state') == 'Disconnected':
                logger.info("Connexion au réseau Soulseek en cours...")
                
                # Tenter de se connecter au serveur Soulseek
                connect_result = self.api.server.connect()
                logger.info(f"Résultat de connexion Soulseek: {connect_result}")
                
                # Attendre que la connexion s'établisse
                max_attempts = 30  # 30 secondes max
                for attempt in range(max_attempts):
                    await asyncio.sleep(1)
                    current_state = self.api.server.state()
                    logger.debug(f"Tentative {attempt + 1}: État = {current_state.get('state', 'Unknown')}")
                    
                    if current_state.get('state') == 'Connected, LoggedIn':
                        logger.info("Connecté et authentifié sur le réseau Soulseek")
                        return
                    elif current_state.get('state') in ['Connected', 'Connecting', 'Logging in']:
                        continue  # En cours de connexion
                    elif current_state.get('state') == 'Disconnected':
                        if attempt > 5:  # Retry après quelques tentatives
                            logger.warning("Nouvelle tentative de connexion Soulseek...")
                            self.api.server.connect()
                
                # Si on arrive ici, la connexion a échoué
                final_state = self.api.server.state()
                raise Exception(f"Impossible de se connecter au réseau Soulseek après 30s. État final: {final_state.get('state', 'Unknown')}")
            
            elif server_state.get('state') == 'Connected, LoggedIn':
                logger.info("Déjà connecté et authentifié sur le réseau Soulseek")
            else:
                logger.warning(f"État Soulseek inattendu: {server_state.get('state')}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la connexion Soulseek: {e}")
            raise
    
    async def _diagnose_connection(self):
        
        test_urls = [
            f"{self.host}",
            f"{self.host}/api/v0/application/version",
            f"{self.host}/api/v0/application/state"
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in test_urls:
                try:
                    logger.info(f"url test: {url}")
                    
                    auth = None
                    if Config.SLSKD_USERNAME and Config.SLSKD_PASSWORD:
                        auth = aiohttp.BasicAuth(Config.SLSKD_USERNAME, Config.SLSKD_PASSWORD)
                    
                    headers = {}
                    if Config.SLSKD_API_KEY:
                        headers['X-API-Key'] = Config.SLSKD_API_KEY
                    
                    async with session.get(url, auth=auth, headers=headers, timeout=10) as response:
                        logger.info(f"Status: {response.status}")
                        logger.info(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                        
                        content = await response.text()
                        if len(content) > 500:
                            content = content[:500] + "..."
                        
                        if response.status == 401:
                            logger.error("authentication error (401) - verify username/password/apikey")
                        elif response.status == 403:
                            logger.error("forbidden error (403)")
                        elif response.status == 404:
                            logger.error("endpoint not found (404) - verify url and slskd version")
                        elif response.status >= 500:
                            logger.error(f"server error ({response.status}) - slskd issue")
                        
                except asyncio.TimeoutError:
                    logger.error(f"{url} timeout")
                except Exception as e:
                    logger.error(f"test error {url}: {e}")
    
    
    async def disconnect(self):
        if self.connected:
            self.connected = False
            logger.info("disconnected from slskd")
    
    async def search_and_download(self, track: dict) -> dict:
        track_artist_title = f"{track['artist']} - {track['title']}"
        print(f"track: {track_artist_title}")

        try:
            query = self._format_search_query(track)
            search_results = self.api.searches.search_text(query)

            while True:
                logger.debug(f"search: {search_results}")
                state = self.api.searches.state(search_results["id"])
                if state["state"] != "InProgress":
                    break
                await asyncio.sleep(2)
            search_responses = self.api.searches.search_responses(search_results["id"])
            print(f"😡 {search_responses}")
            print(f"🤓 processing track: {track_artist_title}")

            if len(search_responses) == 0:
                print(f"🙀 {track_artist_title} - not found")
                return {'success': False, 'error': 'track not found'}

            mp3_responses = []
            flac_responses = []

            for singleTrack in search_responses:
                if len(singleTrack["files"]) == 0:
                    continue
                filename = singleTrack["files"][0]["filename"]

                if self._is_valid_audio_file(filename, "mp3"):
                    if "bitRate" not in singleTrack["files"][0]: 
                        continue
                    if singleTrack["files"][0]["bitRate"] == 320:
                        mp3_responses.append(singleTrack)
                        break

                if self._is_valid_audio_file(filename, "flac"):
                    flac_responses.append(singleTrack)
            
            if len(mp3_responses) > 0:
                print(f"👾 // downloading: {mp3_responses[0]}")
                downloading = self._download_file(mp3_responses[0])
                if downloading["success"]:
                    return {'success': True, 'message': f"downloading mp3 {track}"}
            
            if len(flac_responses) > 0:
                downloading = self._download_file(flac_responses[0])
                if downloading["success"]:
                    return {'success': True, 'message': f"downloading flac {track}"}
                
            print(f"🙀 could not find {track_artist_title} with specified criteria")
            return {'success': False, 'error': 'could not find track with specified criteria'}

        except Exception as e:
            logger.error(f"search / download error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _remove_accents(self, text: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(c)
        )
    
    def _format_search_query(self, track: dict) -> str:
        artist = track['artist']
        title = track['title']

        artist = re.sub(r'[^\w\s]', ' ', artist).strip()
        title = re.sub(r'[^\w\s]', ' ', title).strip()
        
        artist = self._remove_accents(artist)
        title = self._remove_accents(title)

        title = re.sub(r'\b(feat|ft|featuring|remix|remastered|deluxe)\b.*', '', title, flags=re.IGNORECASE)
        
        return f"{artist} {title}".strip()
    
    def _is_valid_audio_file(self, filename: str, format: str) -> bool:
        if filename.lower().endswith(format): 
            return True
        return False
    
    def _download_file(self, file: dict) -> dict:
        try:
            username = file.get('username')
            filename = file["files"][0].get('filename')
            
            if not username or not filename:
                print("missing filename or username")
                return {'success': False, 'error': 'missing filename or username'}

            self.api.transfers.enqueue(username=username, files=file["files"])
            return {"success": True}                
            
        except Exception as e:
            logger.error(f"download error: {e}")
            return {'success': False, 'error': str(e)}
        
    # def _meets_quality_requirements(self, file: dict) -> bool:
    #     """Vérifie si le fichier respecte les critères de qualité"""
    #     # Vérifier la taille (éviter les fichiers trop petits)
    #     size = file.get('size', 0)
    #     if size < 1024 * 1024:  # < 1MB
    #         return False
        
    #     # Vérifier le bitrate si disponible
    #     filename = file.get('filename', '').lower()
        
    #     # Exclure les bitrates trop bas mentionnés dans le nom
    #     bad_bitrates = ['64kbps', '96kbps', '128kbps']
    #     if any(br in filename for br in bad_bitrates):
    #         return False
        
    #     return True
    
    # def _calculate_similarity_score(self, track: dict, file: dict) -> int:
    #     """Calcule un score de similarité entre la track et le fichier"""
    #     filename = file.get('filename', '').lower()
        
    #     artist = track['artist'].lower()
    #     title = track['title'].lower()
        
    #     # Score basé sur la similarité fuzzy
    #     artist_score = fuzz.partial_ratio(artist, filename)
    #     title_score = fuzz.partial_ratio(title, filename)
        
    #     # Score combiné
    #     combined_score = (artist_score + title_score) / 2
        
    #     # Bonus pour certains formats
    #     if '.flac' in filename:
    #         combined_score += 10
    #     elif '.mp3' in filename and '320' in filename:
    #         combined_score += 5
        
    #     # Malus pour certains mots-clés indésirables
    #     bad_keywords = ['karaoke', 'instrumental', 'cover', 'live']
    #     for keyword in bad_keywords:
    #         if keyword in filename:
    #             combined_score -= 20
        
    #     return int(combined_score)
    
    # def _sanitize_filename(self, filename: str) -> str:
    #     """Nettoie un nom de fichier pour le système de fichiers"""
    #     # Supprimer les caractères interdits
    #     invalid_chars = '<>:"/\\|?*'
    #     for char in invalid_chars:
    #         filename = filename.replace(char, '_')
        
    #     return filename.strip()
    

        # def _find_best_match(self, track: dict, files: list) -> dict:
    #     """Trouve le meilleur match parmi les résultats"""
    #     if not files:
    #         return None
        
    #     scored_files = []
        
    #     for file in files:
    #         # Vérifier le format audio
    #         if not self._is_valid_audio_file(file.get('filename', '')):
    #             continue
            
    #         # Vérifier la qualité minimum
    #         if not self._meets_quality_requirements(file):
    #             continue
            
    #         # Calculer le score de similarité
    #         score = self._calculate_similarity_score(track, file)
            
    #         scored_files.append({
    #             'file': file,
    #             'score': score
    #         })
        
    #     if not scored_files:
    #         return None
        
    #     # Trier par score décroissant
    #     scored_files.sort(key=lambda x: x['score'], reverse=True)
        
    #     logger.debug(f"Meilleur match (score: {scored_files[0]['score']}): {scored_files[0]['file'].get('filename')}")
        
    #     return scored_files[0]['file']