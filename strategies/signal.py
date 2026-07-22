import pandas as pd
import numpy as np
import joblib
import logging
import os
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from ta.volatility import AverageTrueRange


logger = logging.getLogger(__name__)


class SignalService:
    def __init__(self, model_filename="model.pkl"):
        self.model = None
        self.is_ready = False
        
        # Résolution du chemin absolu vers le modèle
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, 'models', model_filename)
        
        self._load_model()


    def _load_model(self):
        try:
            self.model = joblib.load(self.model_path)
            self.is_ready = True
            logger.info(f"Modèle ML chargé avec succès depuis {self.model_path}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle : {e}")


    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les indicateurs techniques nécessaires au modèle."""
        df_features = df.copy()
        
        # Moyennes mobiles
        df_features['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
        df_features['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
        
        # RSI
        df_features['rsi_14'] = RSIIndicator(close=df['close'], window=14).rsi()
        
        # ATR (Volatilité)
        df_features['atr_14'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range()
        
        return df_features


    def generate_signal(self, df_rates: pd.DataFrame) -> str:
        if not self.is_ready or df_rates is None or len(df_rates) < 50:
            logger.info("Signal généré: HOLD"); return "HOLD"
            
        try:
            # 1. Calcul des features
            df_features = self.calculate_features(df_rates)
            
            # 2. Récupération de la dernière bougie complète (sans les NaN)
            last_row = df_features.iloc[-1]
            features_array = pd.DataFrame([{
                'sma_20': last_row['sma_20'],
                'sma_50': last_row['sma_50'],
                'rsi_14': last_row['rsi_14'],
                'atr_14': last_row['atr_14']
            }])
            
            # Si des valeurs sont NaN (pas assez de données), on ne fait rien
            if features_array.isnull().values.any():
                logger.info("Signal généré: HOLD"); return "HOLD"
                
            # 3. Prédiction (0=HOLD, 1=BUY, 2=SELL)
            prediction = self.model.predict(features_array)[0]
            
            if prediction == 1:
                logger.info("Signal généré: BUY"); return "BUY"
            elif prediction == 2:
                logger.info("Signal généré: SELL"); return "SELL"
            else:
                logger.info("Signal généré: HOLD"); return "HOLD"
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal : {e}")
            logger.info("Signal généré: HOLD"); return "HOLD"
