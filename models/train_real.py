import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import joblib
import os
import logging
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from ta.volatility import AverageTrueRange
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- CONFIGURATION ---
SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M15
NUM_BARS = 50000
FUTURE_BARS = 5      # Horizon de prédiction (ex: 5 bougies plus tard)
PIP_TARGET = 0.0010  # Mouvement minimum pour considérer un signal valide (10 pips)


def main():
    # 1. Connexion à MT5
    logging.info("Connexion au terminal MT5 local...")
    if not mt5.initialize():
        logging.error(f"Échec de l'initialisation de MT5: {mt5.last_error()}")
        return


    # 2. Téléchargement des données
    logging.info(f"Téléchargement de {NUM_BARS} bougies pour {SYMBOL}...")
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, NUM_BARS)
    mt5.shutdown()
    
    if rates is None or len(rates) == 0:
        logging.error("Aucune donnée récupérée.")
        return
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # 3. Ingénierie des caractéristiques (Features)
    logging.info("Calcul des indicateurs techniques...")
    df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
    df['rsi_14'] = RSIIndicator(close=df['close'], window=14).rsi()
    df['atr_14'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range()
    
    # 4. Création de la variable cible (Target Y)
    # 0 = HOLD, 1 = BUY (Prix monte > Target), 2 = SELL (Prix descend > Target)
    logging.info(f"Création des signaux cibles (Horizon: {FUTURE_BARS} bougies, Cible: {PIP_TARGET} pts)...")
    df['future_close'] = df['close'].shift(-FUTURE_BARS)
    df['price_diff'] = df['future_close'] - df['close']
    
    conditions = [
        (df['price_diff'] >= PIP_TARGET),
        (df['price_diff'] <= -PIP_TARGET)
    ]
    choices = [1, 2] # 1=BUY, 2=SELL
    df['target'] = np.select(conditions, choices, default=0) # 0=HOLD
    
    # 5. Nettoyage des données (Drop NaN)
    df = df.dropna()
    
    # 6. Séparation Features (X) et Target (Y)
    X = df[['sma_20', 'sma_50', 'rsi_14', 'atr_14']]
    y = df['target']
    
    logging.info(f"Distribution des signaux : \n{y.value_counts(normalize=True) * 100}")
    
    # Séparation Train/Test (Sans shuffle pour respecter la série temporelle)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # 7. Entraînement du modèle
    logging.info("Entraînement du modèle RandomForest...")
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    
    # 8. Évaluation rapide
    y_pred = model.predict(X_test)
    logging.info(f"Rapport de classification sur le set de test :\n{classification_report(y_test, y_pred)}")
    
    # 9. Sauvegarde
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.pkl')
    joblib.dump(model, model_path)
    logging.info(f"Modèle réel sauvegardé avec succès dans : {model_path}")
    logging.info("Le fichier model.pkl actuel a été écrasé. Le bot utilisera désormais la nouvelle intelligence.")


if __name__ == "__main__":
    main()
