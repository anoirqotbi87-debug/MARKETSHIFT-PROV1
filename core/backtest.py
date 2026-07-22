import pandas as pd
import joblib
import os
import logging


logging.basicConfig(level=logging.INFO, format='%(message)s')


def run_backtest():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, 'models', 'model.pkl')
    data_path = os.path.join(base_dir, 'models', 'test_data.pkl')
    
    if not os.path.exists(model_path) or not os.path.exists(data_path):
        logging.error("Modèle ou données de test introuvables. Lancez models/train_real.py d'abord.")
        return


    model = joblib.load(model_path)
    df = pd.read_pickle(data_path)
    
    X_test = df[['sma_20', 'sma_50', 'rsi_14', 'atr_14']]
    predictions = model.predict(X_test)
    df['signal'] = predictions
    
    balance = 10000.0
    position = None
    entry_price = 0.0
    trades = 0
    wins = 0
    
    logging.info("--- DÉBUT DU BACKTEST ---")
    logging.info(f"Période analysée : {len(df)} bougies")
    
    for index, row in df.iterrows():
        # Gestion de la position ouverte (Stop Loss et Take Profit simplifiés pour le backtest)
        if position:
            sl_dist = 0.0050
            tp_dist = 0.0100
            close_trade = False
            pnl = 0
            
            if position == 'BUY':
                if row['low'] <= entry_price - sl_dist or row['high'] >= entry_price + tp_dist:
                    close_trade = True
                    pnl = (row['close'] - entry_price) * 100000
            elif position == 'SELL':
                if row['high'] >= entry_price + sl_dist or row['low'] <= entry_price - tp_dist:
                    close_trade = True
                    pnl = (entry_price - row['close']) * 100000
                    
            if close_trade:
                balance += pnl
                trades += 1
                if pnl > 0: wins += 1
                position = None
                
        # Ouverture de position
        if position is None:
            if row['signal'] == 1:
                position = 'BUY'
                entry_price = row['close']
            elif row['signal'] == 2:
                position = 'SELL'
                entry_price = row['close']


    win_rate = (wins / trades * 100) if trades > 0 else 0
    logging.info("--- RÉSULTATS DU BACKTEST ---")
    logging.info(f"Capital Final : {balance:.2f} $")
    logging.info(f"Total Trades  : {trades}")
    logging.info(f"Win Rate      : {win_rate:.2f} %")


if __name__ == "__main__":
    run_backtest()
