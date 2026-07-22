import pandas as pd
import joblib
import os

def run_backtest_api():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, 'models', 'model.pkl')
    data_path = os.path.join(base_dir, 'models', 'test_data.pkl')
    
    if not os.path.exists(model_path) or not os.path.exists(data_path):
        return {"error": "Modèle ou données de test introuvables. Lancez un entraînement d'abord."}

    model = joblib.load(model_path)
    df = pd.read_pickle(data_path)
    
    X_test = df[['sma_20', 'sma_50', 'rsi_14', 'atr_14']]
    df['signal'] = model.predict(X_test)
    
    balance = 10000.0
    position = None
    entry_price = 0.0
    trades = 0
    wins = 0
    
    for index, row in df.iterrows():
        if position:
            close_trade, pnl = False, 0
            if position == 'BUY' and (row['low'] <= entry_price - 0.0050 or row['high'] >= entry_price + 0.0100):
                close_trade, pnl = True, (row['close'] - entry_price) * 100000
            elif position == 'SELL' and (row['high'] >= entry_price + 0.0050 or row['low'] <= entry_price - 0.0100):
                close_trade, pnl = True, (entry_price - row['close']) * 100000
                    
            if close_trade:
                balance += pnl
                trades += 1
                if pnl > 0: wins += 1
                position = None
                
        if position is None:
            if row['signal'] == 1:
                position, entry_price = 'BUY', row['close']
            elif row['signal'] == 2:
                position, entry_price = 'SELL', row['close']

    return {
        "success": True,
        "final_balance": round(balance, 2),
        "total_trades": trades,
        "win_rate": round((wins / trades * 100), 2) if trades > 0 else 0
    }
