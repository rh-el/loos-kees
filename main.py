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
downloader = PlaylistDownloader()


async def spotify_playlist_download():
    playlist_url = input("enter a public spotify playlist url: ").strip()
    if not playlist_url:
        print("playlist URL required")
    results = await downloader.extract_spotify_metadata(playlist_url)
    return results

async def bandcamp_likes_download():
    cookie = input("enter your bandcamp cookie: ")
    results = await downloader.get_bandcamp_likes_metadata(cookie)
    return results

def get_result(playlist, download_result):
    successful = sum(1 for r in download_result if r['success'])
    print(f"done! found {successful}/{len(playlist)} tracks")

async def main():
    while True:
        is_spotify_playlist = input("spotify playlist download?: y/n - ").strip().lower()
        if is_spotify_playlist == "y":
            spotify_playlist = await spotify_playlist_download()
            result = await downloader.download_playlist(spotify_playlist)
            get_result(spotify_playlist, result)

        is_bandcamp_likes = input("bandcamp likes download?: y/n - ").strip().lower()
        if is_bandcamp_likes == "y":
            bandcamp_playlist = await bandcamp_likes_download()
            # print(bandcamp_playlist)
            result = await downloader.download_playlist(bandcamp_playlist)
            get_result(bandcamp_playlist, result)

        is_done = input("anything else?: y/n - ").strip().lower()
        if is_done == "n":
            print("farewell, friend.")
            break

if __name__ == "__main__":
    asyncio.run(main())



# log tracks not found
# bandcamp -> get all tracks from each album
# format scrapped obj to fit download_playlist format