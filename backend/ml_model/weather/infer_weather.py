import os
import torch
import numpy as np
import joblib

# --- [CHANGE 1] IMPORT THE SHARED CONFIG AND MODEL ---
# Import from the training script to ensure all parameters are identical.
from .train_weather import CONFIG 
from .lstm_weather import LSTMForecaster

# --- [CHANGE 2] USE THE CENTRALIZED CONFIGURATION ---
# All paths and parameters are now sourced from the single CONFIG dictionary.
BASE_DIR = CONFIG["model_dir"]
MODEL_PATH = os.path.join(BASE_DIR, CONFIG["model_name"])
SCALER_PATH = os.path.join(BASE_DIR, CONFIG["scaler_name"])
WEATHER_FEATURES = CONFIG["features"]
WEATHER_WINDOW_SIZE = CONFIG["hyperparameters"]["window_size"]
FORECAST_STEPS = CONFIG["hyperparameters"]["forecast_horizon"]

class WeatherForecaster:
    """
    A class to load the trained weather LSTM model and make forecasts.
    This version is corrected to use the centralized CONFIG for consistency.
    """
    def __init__(self):
        self.model = None
        self.scaler = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_ready = False
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads the saved model and scaler from disk."""
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            try:
                self.scaler = joblib.load(SCALER_PATH)

                # --- [FIX] INITIALIZE MODEL WITH FULL PARAMETERS FROM CONFIG ---
                hp = CONFIG["hyperparameters"]
                self.model = LSTMForecaster(
                    input_size=len(WEATHER_FEATURES),
                    hidden_size=hp["lstm_hidden_size"],
                    num_layers=hp["lstm_num_layers"],
                    output_size=len(WEATHER_FEATURES),
                    forecast_horizon=hp["forecast_horizon"],
                    dropout_prob=hp["dropout_prob"]
                )
                # -----------------------------------------------------------
                
                self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
                self.model.to(self.device)
                self.model.eval()
                
                self.is_ready = True
                print("✅ Weather Forecaster loaded successfully.")

            except Exception as e:
                print(f"❌ Error loading weather model artifacts: {e}")
        else:
            self.is_ready = False

    def forecast_from_window(self, window_data: np.ndarray) -> np.ndarray:
        """Takes a window of recent sensor data and returns a forecast."""
        if not self.is_ready:
            raise RuntimeError("Weather forecaster is not ready. Model or scaler not loaded.")

        scaled_window = self.scaler.transform(window_data)
        input_tensor = torch.tensor(scaled_window, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            prediction_scaled = self.model(input_tensor)
        
        prediction_unscaled = self.scaler.inverse_transform(prediction_scaled.cpu().numpy()[0])
        
        return prediction_unscaled

