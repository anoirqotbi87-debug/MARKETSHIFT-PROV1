from fastapi import FastAPI
from pydantic import BaseModel
# Note: La base de données n'est pas encore implémentée dans le MVP,
# je commente temporairement ces imports pour éviter des erreurs.
# from data.database import SessionLocal, Trade
from core.backtest import run_backtest_api


app = FastAPI(title="MarketShift Bot API V2")
trading_engine = None


def init_api(engine_instance):
    global trading_engine
    trading_engine = engine_instance


class Command(BaseModel):
    action: str


@app.get("/status")
def get_status():
    if not trading_engine: return {"status": "error", "message": "Engine not initialized"}
    
    # Simulation de la base de données pour le moment
    open_trades = [p for p in trading_engine.virtual_positions if p['status'] == 'OPEN']
    closed_trades = [p for p in trading_engine.virtual_positions if p['status'] == 'CLOSED']
    
    return {
        "status": "paused" if trading_engine.is_paused else "running",
        "balance": round(trading_engine.virtual_balance, 2),
        "open_positions_count": len(open_trades),
        "total_trades": len(trading_engine.virtual_positions),
        "open_positions": open_trades,
        "closed_positions": closed_trades[-10:]
    }


@app.post("/control")
def control_bot(cmd: Command):
    if not trading_engine: return {"error": "Engine offline"}
    if cmd.action == "pause":
        trading_engine.pause()
        return {"message": "Bot en pause"}
    elif cmd.action == "resume":
        trading_engine.resume()
        return {"message": "Bot relancé"}
    return {"error": "Action inconnue"}


@app.post("/backtest")
def trigger_backtest():
    result = run_backtest_api()
    return result
