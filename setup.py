#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Installe les dépendances Python"""
    print("Installation des dépendances Python...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_environment():
    """Configure l'environnement"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Création du fichier .env...")
        env_file.write_text(env_example.read_text())
        print("⚠️  Veuillez éditer le fichier .env avec vos credentials!")
    
    # Créer les dossiers nécessaires
    Path("downloads").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

def check_slskd():
    """Vérifie si slskd est installé"""
    try:
        result = subprocess.run(["slskd", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ slskd trouvé: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ slskd n'est pas installé ou non trouvé dans le PATH")
    print("Installez slskd depuis: https://github.com/slskd/slskd/releases")
    return False

def main():
    print("=== Configuration du projet Spotify->Soulseek ===\n")
    
    # 1. Installer les dépendances Python
    try:
        install_requirements()
        print("✓ Dépendances Python installées\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        return 1
    
    # 2. Configuration de l'environnement
    setup_environment()
    print("✓ Environnement configuré\n")
    
    # 3. Vérifier slskd
    if not check_slskd():
        print("\n📋 Étapes suivantes:")
        print("1. Installez slskd")
        print("2. Éditez le fichier .env avec vos credentials")
        print("3. Lancez slskd: slskd --config slskd.yml")
        print("4. Exécutez: python main.py")
        return 1
    
    print("✅ Configuration terminée!")
    print("\n📋 Étapes suivantes:")
    print("1. Éditez le fichier .env avec vos credentials")
    print("2. Lancez slskd: slskd --config slskd.yml")
    print("3. Exécutez: python main.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())