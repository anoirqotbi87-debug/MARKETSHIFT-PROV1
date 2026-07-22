import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os


# 1. Génération de fausses données (Features)
np.random.seed(42)
X_dummy = pd.DataFrame({
    'sma_20': np.random.rand(1000) * 1.1,
    'sma_50': np.random.rand(1000) * 1.1,
    'rsi_14': np.random.uniform(20, 80, 1000),
    'atr_14': np.random.uniform(0.001, 0.005, 1000)
})


# 2. Génération de fausses cibles (0 = HOLD, 1 = BUY, 2 = SELL)
y_dummy = np.random.choice([0, 1, 2], size=1000, p=[0.7, 0.15, 0.15])


# 3. Entraînement du modèle
model = RandomForestClassifier(n_estimators=10, max_depth=3)
model.fit(X_dummy, y_dummy)


# 4. Sauvegarde
os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.pkl')
joblib.dump(model, model_path)
print(f"Modèle factice sauvegardé avec succès dans : {model_path}")
