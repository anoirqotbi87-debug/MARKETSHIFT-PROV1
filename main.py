import time
import logging
import threading
import uvicorn
import os
from dotenv import load_dotenv


from core.engine import PaperTradingEngine
from strategies.signal import SignalService
from api.server import app, init_api


# 1. Chargement des variables d'environnement
load_dotenv()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")


def get_broker_credentials():
    """Récupère les identifiants du broker actif défini dans le .env"""
    active_broker = os.getenv("ACTIVE_BROKER", "").upper()
    
    if not active_broker:
        logging.error("Aucun ACTIVE_BROKER défini dans le .env")
        return None, None, None


    # Extraction dynamique selon le broker actif (ex: XM_LOGIN ou EXNESS_LOGIN)
    login_str = os.getenv(f"{active_broker}_LOGIN")
    password = os.getenv(f"{active_broker}_PASSWORD", "")
    server = os.getenv(f"{active_broker}_SERVER", "")
    
    login = int(login_str) if login_str and login_str.isdigit() else 0
    
    return login, password, server


def main():
    # 2. Configuration MT5 dynamique
    login, password, server = get_broker_credentials()
    
    if not login or not password:
        logging.warning("Identifiants MT5 invalides ou manquants. Vérifiez votre .env.")


    # 3. Paramètres globaux du bot
    simulation_mode = os.getenv("SIMULATION_MODE", "true").lower() == "true"
    max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 0.05))
    
    config = {
        'login': login,
        'password': password,
        'server': server,
        'path': os.getenv("MT5_PATH", ""),
        'symbol': os.getenv("BOT_SYMBOL", "EURUSD"),
        'tick_interval': 5,
        'initial_balance': 10000.0,
        'simulation_mode': simulation_mode,
        'max_daily_loss': max_daily_loss
    }


    logging.info(f"Démarrage avec le broker: {os.getenv('ACTIVE_BROKER', 'NON_DEFINI').upper()}")
    logging.info(f"Mode Simulation: {'ACTIF' if simulation_mode else 'INACTIF'}")


    # 4. Initialisation des composants
    signal_service = SignalService()
    engine = PaperTradingEngine(config=config, signal_service=signal_service)
    
    init_api(engine)
    
    # 5. Démarrage du moteur
    engine.start()


    # 6. Démarrage de l'API dans un thread séparé
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logging.info("API (Dashboard) démarrée sur http://127.0.0.1:8000")


    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Arrêt demandé par l'utilisateur...")
        engine.stop()


if __name__ == "__main__":
    main()
