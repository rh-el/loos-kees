import os
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
load_dotenv()

class Config:
    # Soulseek credentials
    SOULSEEK_USERNAME = os.getenv('SOULSEEK_USERNAME')
    SOULSEEK_PASSWORD = os.getenv('SOULSEEK_PASSWORD')
    
    # Spotify API
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # slskd settings
    SLSKD_HOST = os.getenv('SLSKD_HOST', 'localhost')
    SLSKD_PORT = int(os.getenv('SLSKD_PORT', 5030))
    SLSKD_API_KEY = os.getenv('SLSKD_API_KEY')
    SLSKD_USERNAME = os.getenv('SLSKD_USERNAME', 'admin')
    SLSKD_PASSWORD = os.getenv('SLSKD_PASSWORD')
    
    # Download settings
    DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', './downloads'))
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', 3))
    AUDIO_FORMATS = os.getenv('AUDIO_FORMATS', 'mp3,flac,m4a').split(',')
    MIN_BITRATE = int(os.getenv('MIN_BITRATE', 192))
    
    # Validation
    @classmethod
    def validate(cls):
        required_vars = [
            'SOULSEEK_USERNAME',
            'SOULSEEK_PASSWORD',
            'SLSKD_PASSWORD'
        ]
        
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Créer le dossier de téléchargement
        cls.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        return True