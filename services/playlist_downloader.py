import json
from clients.soulseek_client import SoulseekClient
from clients.spotify_client import SpotifyClient
from config import Config
import asyncio


class PlaylistDownloader:
    def __init__(self):
        Config.validate()
        self.spotify = SpotifyClient()
        self.soulseek = SoulseekClient()
    
    async def extract_spotify_metadata(self, playlist_url: str): 
        tracks = await self.spotify.get_playlist_tracks(playlist_url)
        return tracks


    async def get_bandcamp_likes_metadata(self, cookie: str):
        try:
            process = await asyncio.create_subprocess_exec(
                'node', './bc-fetch.js', cookie,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"error while executing js script: {stderr.decode()}")
                return None
            
            result_text = stdout.decode('utf-8').strip()
            return json.loads(result_text)
            
        except FileNotFoundError:
            print("error: node.js not installed or can't find bc-fetch.js")
            return None
        except json.JSONDecodeError as e:
            print(f"json parsing error: {e}")
            print(f"received output: {result_text}")
            return None
        except Exception as e:
            print(f"unexpected error: {e}")
            return None
    
    async def sem_task(self, track, semaphore):
        async with semaphore:
            await asyncio.sleep(1)
            return await self.soulseek.search_and_download(track)
            

    async def download_playlist(self, track_list: list):
        # fix parallel tasks limit 
        semaphore = asyncio.Semaphore(2)
        try:
            await self.soulseek.connect()

            result = await asyncio.gather(*(self.sem_task(track, semaphore) for track in track_list))
            return result
            
        except Exception as e:
            print(f"download error: {e}")
            raise
        finally:
            await self.soulseek.disconnect()