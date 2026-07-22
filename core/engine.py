import asyncio
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    import core.mock_mt5 as mt5
    MT5_AVAILABLE = False
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, config: dict):
        self.config = config
        self._mt5_pool = ThreadPoolExecutor(max_workers=4)
        self._running = False
        self.is_paused = False  # NOUVEAU: Contrôle depuis l'API
        self._loop = None
        self.use_mt5 = False

    def start(self):
        self._running = True
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_loop, daemon=True).start()

    def pause(self):
        self.is_paused = True
        logger.info("Bot mis en PAUSE via API.")

    def resume(self):
        self.is_paused = False
        logger.info("Bot RELANCÉ via API.")

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main_loop())

    async def _main_loop(self):
        await self._init_mt5()
        while self._running:
            try:
                if not self.is_paused:
                    await self._tick()
            except Exception as e:
                logger.error(f"Erreur dans la boucle: {e}")
            await asyncio.sleep(self.config.get('tick_interval', 5))

    async def _init_mt5(self):
        def _init():
            if not MT5_AVAILABLE:
                logger.warning("Bibliothèque MetaTrader5 introuvable (Environnement Linux).")
                self.use_mt5 = False
                return False
            init_kwargs = {"login": self.config.get('login'), "password": self.config.get('password'), "server": self.config.get('server')}
            mt5_path = self.config.get('path')
            if mt5_path: init_kwargs["path"] = mt5_path
            if mt5.initialize(**init_kwargs):
                logger.info(f"Connexion MT5 établie au compte {init_kwargs['login']}.")
                self.use_mt5 = True
                return True
            else:
                logger.error(f"Échec MT5. Passage en mode dégradé.")
                self.use_mt5 = False
                return False
        return await self._loop.run_in_executor(self._mt5_pool, _init)

    async def _tick(self):
        pass

    def stop(self):
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._mt5_pool.shutdown(wait=True)
        if MT5_AVAILABLE:
            mt5.shutdown()

class PaperTradingEngine(ExecutionEngine):
    def __init__(self, config: dict, signal_service):
        super().__init__(config)
        self.signal_service = signal_service
        self.symbol = config.get('symbol', 'EURUSD')
        self.timeframe = config.get('timeframe', mt5.TIMEFRAME_M15)
        self.num_bars = config.get('num_bars', 100)
        
        self.virtual_positions = []
        self.virtual_balance = config.get('initial_balance', 10000.0)

    async def _tick(self):
        df_rates = await self._fetch_data()
        if df_rates is None or df_rates.empty:
            return

        current_price = df_rates.iloc[-1]['close']
        await self._manage_virtual_positions(current_price)

        signal = await self._loop.run_in_executor(
            None, self.signal_service.generate_signal, df_rates
        )

        if signal in ['BUY', 'SELL']:
            await self._execute_paper_trade(signal, current_price)

    async def _fetch_data(self) -> Optional[pd.DataFrame]:
        def fetch():
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, self.num_bars)
            if rates is None:
                return None
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
        return await self._loop.run_in_executor(self._mt5_pool, fetch)

    async def _execute_paper_trade(self, signal: str, price: float):
        if any(p['symbol'] == self.symbol and p['status'] == 'OPEN' for p in self.virtual_positions):
            return 

        position = {
            'id': len(self.virtual_positions) + 1,
            'symbol': self.symbol,
            'type': signal,
            'entry_price': price,
            'status': 'OPEN',
            'sl': price - 0.0050 if signal == 'BUY' else price + 0.0050,
            'tp': price + 0.0100 if signal == 'BUY' else price - 0.0100
        }
        self.virtual_positions.append(position)
        logger.info(f"PAPER TRADE OUVERT: {signal} @ {price:.5f}")

    async def _manage_virtual_positions(self, current_price: float):
        for pos in self.virtual_positions:
            if pos['status'] == 'OPEN':
                close_trade = False
                pnl = 0.0

                if pos['type'] == 'BUY':
                    if current_price <= pos['sl'] or current_price >= pos['tp']:
                        close_trade, pnl = True, current_price - pos['entry_price']
                elif pos['type'] == 'SELL':
                    if current_price >= pos['sl'] or current_price <= pos['tp']:
                        close_trade, pnl = True, pos['entry_price'] - current_price

                if close_trade:
                    pos['status'], pos['exit_price'], pos['pnl'] = 'CLOSED', current_price, pnl
                    self.virtual_balance += pnl * 100000
                    logger.info(f"TRADE FERMÉ. PnL: {pnl:.5f} | Solde: {self.virtual_balance:.2f}")
