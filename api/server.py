from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any


app = FastAPI(title="MarketShift Bot API")


# Variable globale pour stocker la référence au moteur
trading_engine = None


def init_api(engine_instance):
    global trading_engine
    trading_engine = engine_instance


@app.get("/status")
def get_status():
    if not trading_engine:
        return {"status": "error", "message": "Engine not initialized"}
    
    open_positions = [p for p in trading_engine.virtual_positions if p['status'] == 'OPEN']
    closed_positions = [p for p in trading_engine.virtual_positions if p['status'] == 'CLOSED']
    
    return {
        "status": "running",
        "balance": trading_engine.virtual_balance,
        "open_positions_count": len(open_positions),
        "total_trades": len(trading_engine.virtual_positions),
        "open_positions": open_positions,
        "closed_positions": closed_positions[-10:] # Les 10 derniers trades fermés
    }
