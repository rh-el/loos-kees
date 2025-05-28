#!/usr/bin/env python3

import asyncio
import logging
from pathlib import Path
from config import Config
from clients.spotify_client import SpotifyClient
from clients.soulseek_client import SoulseekClient

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('slsk_downloader.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class PlaylistDownloader:
    def __init__(self):
        Config.validate()
        self.spotify = SpotifyClient()
        self.soulseek = SoulseekClient()
        
    async def download_playlist(self, playlist_url: str):
        """Télécharge une playlist Spotify via Soulseek"""
        try:
            logger.info(f"Début du téléchargement de la playlist: {playlist_url}")
            
            # 1. Récupérer les tracks de la playlist Spotify
            tracks = await self.spotify.get_playlist_tracks(playlist_url)
            logger.info(f"Trouvé {len(tracks)} tracks dans la playlist")
            
            # 2. Connecter à slskd
            await self.soulseek.connect()
            
            # 3. Télécharger chaque track
            results = []
            for i, track in enumerate(tracks, 1):
                logger.info(f"[{i}/{len(tracks)}] Recherche: {track['artist']} - {track['title']}")
                
                result = await self.soulseek.search_and_download(track)
                results.append(result)
                
                # if result['success']:
                #     logger.info(f"✓ Téléchargement réussi: {track['title']}")
                # else:
                #     logger.warning(f"✗ Échec: {track['title']} - {result['error']}")
            
            # 4. Statistiques finales
            # successful = sum(1 for r in results if r['success'])
            # logger.info(f"Terminé! {successful}/{len(tracks)} téléchargements réussis")
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement: {e}")
            raise
        finally:
            await self.soulseek.disconnect()

async def main():
    """Point d'entrée principal"""
    downloader = PlaylistDownloader()
    
    # Exemple d'utilisation
    playlist_url = input("Entrez l'URL de la playlist Spotify: ").strip()
    
    if not playlist_url:
        logger.error("URL de playlist requise")
        return
    
    # try:
    results = await downloader.download_playlist(playlist_url)
    #     print(f"\nRésultats: {sum(1 for r in results if r['success'])} succès sur {len(results)} tentatives")
    
    # except KeyboardInterrupt:
    #     logger.info("Arrêt demandé par l'utilisateur")
    # except Exception as e:
    #     logger.error(f"Erreur fatale: {e}")

if __name__ == "__main__":
    asyncio.run(main())

