from clients.soulseek_client import SoulseekClient
from clients.spotify_client import SpotifyClient
from config import Config
import asyncio


class PlaylistDownloader:
    def __init__(self):
        Config.validate()
        self.spotify = SpotifyClient()
        self.soulseek = SoulseekClient()
        
    async def download_playlist(self, playlist_url: str):
        try:
            
            tracks = await self.spotify.get_playlist_tracks(playlist_url)
            print(f"found {len(tracks)} tracks in the playlist")
            
            await self.soulseek.connect()
            
            result = await asyncio.gather(*[self.soulseek.search_and_download(track) for track in tracks])
            total_downloads = [ entry for entry in result if entry.get("success") is True]

            print(f"{len(total_downloads)} / {len(tracks)} downloads")

            # for i, track in enumerate(tracks, 1):
                # print(f"[{i}/{len(tracks)}] Search: {track['artist']} - {track['title']}")

            #     result = self.soulseek.search_and_download(track)
                # results.append(result)
                
                # if result['success']:
                #     logger.info(f"✓ Téléchargement réussi: {track['title']}")
                # else:
                #     logger.warning(f"✗ Échec: {track['title']} - {result['error']}")
            
            # 4. Statistiques finales
            # successful = sum(1 for r in results if r['success'])
            # logger.info(f"Terminé! {successful}/{len(tracks)} téléchargements réussis")
            
            return total_downloads
            
        except Exception as e:
            print(f"download error: {e}")
            raise
        finally:
            await self.soulseek.disconnect()