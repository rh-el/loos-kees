#!/usr/bin/env python3

import asyncio
import logging
from services.playlist_downloader import PlaylistDownloader

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



async def main():
    downloader = PlaylistDownloader()
    
    while True:
        is_spotify_playlist = input("spotify playlist download?: y/n").strip().lower()
        if is_spotify_playlist == "y":
            playlist_url = input("enter a public spotify playlist url: ").strip()
            if not playlist_url:
                print("playlist URL required")
                continue
            

            results = await downloader.download_playlist(playlist_url)
    
    # try:
    #     print(f"\nRésultats: {sum(1 for r in results if r['success'])} succès sur {len(results)} tentatives")
    
    # except KeyboardInterrupt:
    #     logger.info("Arrêt demandé par l'utilisateur")
    # except Exception as e:
    #     logger.error(f"Erreur fatale: {e}")

if __name__ == "__main__":
    asyncio.run(main())

