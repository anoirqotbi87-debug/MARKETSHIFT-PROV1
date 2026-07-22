import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import joblib
import os
import logging
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from ta.volatility import AverageTrueRange
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- CONFIGURATION ---
ACTIVE_BROKER = os.getenv("ACTIVE_BROKER", "").upper()
LOGIN = int(os.getenv(f"{ACTIVE_BROKER}_LOGIN", 0))
PASSWORD = os.getenv(f"{ACTIVE_BROKER}_PASSWORD", "")
SERVER = os.getenv(f"{ACTIVE_BROKER}_SERVER", "")
PATH = os.getenv("MT5_PATH", "")
SYMBOL = os.getenv("BOT_SYMBOL", "EURUSD")


TIMEFRAME = mt5.TIMEFRAME_M15
NUM_BARS = 50000
FUTURE_BARS = 5
PIP_TARGET = 0.0010


def main():
    logging.info("Connexion à MT5 pour récupération des données...")
    init_kwargs = {"login": LOGIN, "password": PASSWORD, "server": SERVER}
    if PATH: init_kwargs["path"] = PATH
        
    if not mt5.initialize(**init_kwargs):
        logging.error(f"Échec MT5: {mt5.last_error()}")
        return


    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, NUM_BARS)
    mt5.shutdown()
    
    if rates is None or len(rates) == 0:
        return
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    logging.info("Ingénierie des features (XGBoost)...")
    df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
    df['rsi_14'] = RSIIndicator(close=df['close'], window=14).rsi()
    df['atr_14'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range()
    
    df['future_close'] = df['close'].shift(-FUTURE_BARS)
    df['price_diff'] = df['future_close'] - df['close']
    
    conditions = [(df['price_diff'] >= PIP_TARGET), (df['price_diff'] <= -PIP_TARGET)]
    df['target'] = np.select(conditions, [1, 2], default=0)
    
    df = df.dropna()
    
    X = df[['sma_20', 'sma_50', 'rsi_14', 'atr_14']]
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    logging.info("Entraînement du modèle XGBoost Classifier...")
    # Paramètres adaptés pour les séries temporelles
    model = XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='multi:softprob',
        random_state=42
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    logging.info(f"Rapport de classification XGBoost :\n{classification_report(y_test, y_pred)}")
    
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.pkl')
    joblib.dump(model, model_path)
    
    # Sauvegarde des données de test pour le backtester
    df_test = df.iloc[len(X_train):].copy()
    test_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data.pkl')
    df_test.to_pickle(test_data_path)
    
    logging.info("Nouveau modèle XGBoost et données de test sauvegardés.")


if __name__ == "__main__":
    main()
