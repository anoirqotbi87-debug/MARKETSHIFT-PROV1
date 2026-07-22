import time
import random
from datetime import datetime, timedelta


# Constantes MT5
TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_H1 = 16385


def initialize(login=None, password=None, server=None):
    """Simule une connexion réussie"""
    return True


def shutdown():
    """Simule la fermeture"""
    pass


def last_error():
    return (1, "Success")


def copy_rates_from_pos(symbol, timeframe, start_pos, count):
    """Génère un tableau de fausses bougies (OHLC)"""
    rates = []
    now = datetime.now()
    base_price = 1.1000 if 'EUR' in symbol else 150.00
    
    for i in range(count):
        # Mouvement aléatoire
        variation = random.uniform(-0.0020, 0.0020)
        close_price = base_price + variation
        
        rates.append({
            'time': int((now - timedelta(minutes=15 * (count - i))).timestamp()),
            'open': close_price - random.uniform(0, 0.0010),
            'high': close_price + random.uniform(0, 0.0020),
            'low': close_price - random.uniform(0, 0.0020),
            'close': close_price,
            'tick_volume': random.randint(100, 500),
            'spread': 2,
            'real_volume': 0
        })
        base_price = close_price
        
    return rates
