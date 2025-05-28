import asyncio
import json
import logging
from pathlib import Path
import slskd_api 
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from config import Config
from urllib.parse import urlparse
import aiohttp


logger = logging.getLogger(__name__)

class SoulseekClient:
    def __init__(self):
        # Valider et corriger l'URL du host
        self.host = self._validate_host_url(Config.SLSKD_HOST)
        
        # Initialiser l'API slskd avec ou sans API key
        if Config.SLSKD_API_KEY:
            self.api = slskd_api.SlskdClient(
                host=self.host,
                username=Config.SLSKD_USERNAME,
                password=Config.SLSKD_PASSWORD,
                api_key=Config.SLSKD_API_KEY
            )
        else:
            # Utiliser seulement username/password
            self.api = slskd_api.SlskdClient(
                host=self.host,
                username=Config.SLSKD_USERNAME,
                password=Config.SLSKD_PASSWORD
            )
        self.connected = False
    
    def _validate_host_url(self, host):
        """Valider et corriger l'URL du host slskd"""
        if not host:
            raise ValueError("SLSKD_HOST ne peut pas être vide")
        
        # Si l'URL ne commence pas par http:// ou https://, ajouter http://
        if not host.startswith(('http://', 'https://')):
            host = f"http://{host}"
            logger.info(f"Schéma ajouté à l'URL: {host}")
        
        # Valider l'URL
        try:
            parsed = urlparse(host)
            if not parsed.netloc:
                raise ValueError(f"URL invalide: {host}")
        except Exception as e:
            raise ValueError(f"Erreur lors de la validation de l'URL {host}: {e}")
        
        return host
    
    async def connect(self):
        """Se connecter à slskd"""
        try:
            logger.info("Tentative de connexion à slskd...")
            
            # Diagnostic détaillé de la connexion
            await self._diagnose_connection()
            
            # Vérifier la connexion via l'API (sans await car ce ne sont pas des coroutines)
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
        """Diagnostiquer la connexion slskd"""
        
        # Tests de connectivité
        test_urls = [
            f"{self.host}",
            f"{self.host}/api/v0/application/version",
            f"{self.host}/api/v0/application/state"
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in test_urls:
                try:
                    logger.info(f"Test de {url}")
                    
                    # Préparer les headers d'authentification si nécessaire
                    auth = None
                    if Config.SLSKD_USERNAME and Config.SLSKD_PASSWORD:
                        auth = aiohttp.BasicAuth(Config.SLSKD_USERNAME, Config.SLSKD_PASSWORD)
                    
                    headers = {}
                    if Config.SLSKD_API_KEY:
                        headers['X-API-Key'] = Config.SLSKD_API_KEY
                    
                    async with session.get(url, auth=auth, headers=headers, timeout=10) as response:
                        logger.info(f"Status: {response.status}")
                        logger.info(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                        
                        # Lire le contenu pour diagnostic
                        content = await response.text()
                        if len(content) > 500:
                            content = content[:500] + "..."
                        logger.info(f"Réponse: {content}")
                        
                        if response.status == 401:
                            logger.error("Erreur d'authentification (401) - Vérifiez username/password/API key")
                        elif response.status == 403:
                            logger.error("Accès interdit (403) - Permissions insuffisantes")
                        elif response.status == 404:
                            logger.error("Endpoint non trouvé (404) - Vérifiez l'URL et la version de slskd")
                        elif response.status >= 500:
                            logger.error(f"Erreur serveur ({response.status}) - Problème avec slskd")
                        
                except asyncio.TimeoutError:
                    logger.error(f"Timeout sur {url}")
                except Exception as e:
                    logger.error(f"Erreur lors du test de {url}: {e}")
    
    
    async def disconnect(self):
        """Déconnecter de slskd"""
        if self.connected:
            # Note: slskd-api ne nécessite pas de déconnexion explicite
            self.connected = False
            logger.info("Déconnecté de slskd")
    
    async def search_and_download(self, track: dict) -> dict:
        """Recherche et télécharge une track"""
        try:
            # 1. Formater la requête de recherche
            query = self._format_search_query(track)
            
            # 2. Effectuer la recherche
            search_results = await self.api.searches.search_text(query)

            tmp = True
            while tmp:
                logger.debug(f"Requête de recherche: {search_results}")
                state = await self.api.searches.state(search_results["id"])
                if state["state"] != "InProgress":
                    break

            search_responses = await self.api.searches.search_responses(search_results["id"])

            mp3_responses = []
            flac_responses = []

            for singleTrack in search_responses:
                print(f"🅰️{singleTrack}")
                if len(singleTrack["files"]) == 0:
                    continue

                if singleTrack["files"][0]["filename"].split(".")[-1] == "mp3":
                    if "bitRate" not in singleTrack["files"][0]: 
                        continue
                    if singleTrack["files"][0]["bitRate"] == 320:
                        mp3_responses.append(singleTrack)
                        break

                if singleTrack["files"][0]["filename"].split(".")[-1] == "flac":
                    flac_responses.append(singleTrack)

            print(f"#️🆔{mp3_responses}")
            
            if len(search_responses) == 0:
                return {'success': False, 'error': 'Aucun résultat trouvé'}
            
            if len(mp3_responses) > 0:
                download_result = await self._download_file(mp3_responses[0], track)
                return download_result
             
            return
                    
        except Exception as e:
            logger.error(f"Erreur lors de la recherche/téléchargement: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_search_query(self, track: dict) -> str:
        """Formate une requête de recherche optimisée"""
        artist = track['artist']
        title = track['title']
        
        # Nettoyer les caractères spéciaux
        artist = re.sub(r'[^\w\s]', ' ', artist).strip()
        title = re.sub(r'[^\w\s]', ' ', title).strip()
        
        # Supprimer les mots en trop
        title = re.sub(r'\b(feat|ft|featuring|remix|remastered|deluxe)\b.*', '', title, flags=re.IGNORECASE)
        
        return f"{artist} {title}".strip()
    
    def _find_best_match(self, track: dict, files: list) -> dict:
        """Trouve le meilleur match parmi les résultats"""
        if not files:
            return None
        
        scored_files = []
        
        for file in files:
            # Vérifier le format audio
            if not self._is_valid_audio_file(file.get('filename', '')):
                continue
            
            # Vérifier la qualité minimum
            if not self._meets_quality_requirements(file):
                continue
            
            # Calculer le score de similarité
            score = self._calculate_similarity_score(track, file)
            
            scored_files.append({
                'file': file,
                'score': score
            })
        
        if not scored_files:
            return None
        
        # Trier par score décroissant
        scored_files.sort(key=lambda x: x['score'], reverse=True)
        
        logger.debug(f"Meilleur match (score: {scored_files[0]['score']}): {scored_files[0]['file'].get('filename')}")
        
        return scored_files[0]['file']
    
    def _is_valid_audio_file(self, filename: str) -> bool:
        """Vérifie si le fichier est un format audio valide"""
        audio_extensions = ['.mp3', '.flac', '.m4a', '.wav', '.ogg', '.aac']
        return any(filename.lower().endswith(ext) for ext in audio_extensions)
    
    def _meets_quality_requirements(self, file: dict) -> bool:
        """Vérifie si le fichier respecte les critères de qualité"""
        # Vérifier la taille (éviter les fichiers trop petits)
        size = file.get('size', 0)
        if size < 1024 * 1024:  # < 1MB
            return False
        
        # Vérifier le bitrate si disponible
        filename = file.get('filename', '').lower()
        
        # Exclure les bitrates trop bas mentionnés dans le nom
        bad_bitrates = ['64kbps', '96kbps', '128kbps']
        if any(br in filename for br in bad_bitrates):
            return False
        
        return True
    
    def _calculate_similarity_score(self, track: dict, file: dict) -> int:
        """Calcule un score de similarité entre la track et le fichier"""
        filename = file.get('filename', '').lower()
        
        artist = track['artist'].lower()
        title = track['title'].lower()
        
        # Score basé sur la similarité fuzzy
        artist_score = fuzz.partial_ratio(artist, filename)
        title_score = fuzz.partial_ratio(title, filename)
        
        # Score combiné
        combined_score = (artist_score + title_score) / 2
        
        # Bonus pour certains formats
        if '.flac' in filename:
            combined_score += 10
        elif '.mp3' in filename and '320' in filename:
            combined_score += 5
        
        # Malus pour certains mots-clés indésirables
        bad_keywords = ['karaoke', 'instrumental', 'cover', 'live']
        for keyword in bad_keywords:
            if keyword in filename:
                combined_score -= 20
        
        return int(combined_score)
    
    async def _download_file(self, file: dict, track: dict) -> dict:
        """Télécharge un fichier"""
        try:
            username = file.get('username')
            filename = file["files"][0].get('filename')
            
            if not username or not filename:
                return {'success': False, 'error': 'Informations de fichier incomplètes'}

            enqueue = await self.api.transfers.enqueue(username=username, files=file["files"])

                # download_request = await self.api.transfers.get_download(
                #     username=username,
                #     id=filename
                # )
                # print(download_request)
                
                # # Si pas de réponse JSON, considérer que c'est normal
                # if download_request is None:
                #     logger.info(f"Téléchargement initié (pas de réponse): {filename}")
                #     return {
                #         'success': True,
                #         'filename': filename,
                #         'username': username,
                #         'download_id': None
                #     }
                
            
            return 
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement: {e}")
            return {'success': False, 'error': str(e)}
    
    def _sanitize_filename(self, filename: str) -> str:
        """Nettoie un nom de fichier pour le système de fichiers"""
        # Supprimer les caractères interdits
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        return filename.strip()