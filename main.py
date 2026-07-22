import time
import logging
import threading
import uvicorn
from core.engine import PaperTradingEngine
from strategies.signal import SignalService
from api.server import app, init_api


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run_api():
    """Lance le serveur FastAPI."""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")


def main():
    config = {
        'login': 12345678,
        'password': 'password',
        'server': 'demo-server',
        'symbol': 'EURUSD',
        'tick_interval': 1,
        'initial_balance': 10000.0
    }


    # 1. Initialisation
    signal_service = SignalService()
    engine = PaperTradingEngine(config=config, signal_service=signal_service)
    
    # 2. Liaison de l'API avec le moteur
    init_api(engine)


    # 3. Démarrage du moteur de trading
    engine.start()
    logging.info("Moteur de trading démarré.")


    # 4. Démarrage de l'API dans un thread séparé
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logging.info("API démarrée sur http://127.0.0.1:8000")


    # 5. Boucle principale de maintien
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Arrêt demandé...")
        engine.stop()


if __name__ == "__main__":
    main()
