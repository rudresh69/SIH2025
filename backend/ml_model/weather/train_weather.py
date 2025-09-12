"""
train_weather.py

This script serves as the complete training pipeline for the LSTM-based
weather nowcasting model. It handles data loading, preprocessing, model training,
and the saving of the final model and data scaler artifacts.
"""

import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import numpy as np
import random
import logging

# --- PATH SETUP ---
# Ensures that local modules (like data.py) can be imported correctly.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# --- LOCAL MODULE IMPORTS ---
from ml_model.weather.data import load_and_preprocess_data, create_sliding_windows, save_scaler
from ml_model.weather.lstm_weather import LSTMForecaster

# ===================================================================
# 1. CENTRALIZED CONFIGURATION ⚙️
# All important parameters are defined in this single dictionary for easy access and modification.
# ===================================================================
CONFIG = {
    "dataset_path": os.path.join(BASE_DIR, "rockfall_dataset_refined.csv"),
    "model_dir": os.path.join(BASE_DIR, "ml_model", "weather"),
    "model_name": "best_weather_model.pth",
    "scaler_name": "weather_scaler.pkl",
    "features": [
        "rain_sensor_mmhr",
        "temperature_celsius",
        "humidity_percent"
    ],
    "hyperparameters": {
        "window_size": 30,
        "forecast_horizon": 5,
        "batch_size": 64,
        "epochs": 20,
        "learning_rate": 0.001,
        "test_split_size": 0.2,
        "lstm_hidden_size": 64,
        "lstm_num_layers": 2,
        "dropout_prob": 0.2
    }
}

# ===================================================================
# 2. SETUP LOGGING AND REPRODUCIBILITY 📝
# Using logging is better than print() for tracking progress.
# Setting seeds ensures that training is reproducible.
# ===================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s"
)

def set_seed(seed_value=42):
    """Sets the seed for reproducibility across all relevant libraries."""
    random.seed(seed_value)
    np.random.seed(seed_value)
    torch.manual_seed(seed_value)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed_value)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

set_seed()

def train_model():
    """Main function to orchestrate the model training pipeline."""
    hp = CONFIG["hyperparameters"]
    NUM_FEATURES = len(CONFIG["features"])

    logging.info("🚀 Starting weather nowcasting model training pipeline...")
    os.makedirs(CONFIG["model_dir"], exist_ok=True)

    # 1. Load and Preprocess Data
    try:
        logging.info(f"Loading data from {CONFIG['dataset_path']}...")
        scaled_data, scaler, _ = load_and_preprocess_data(CONFIG["dataset_path"], CONFIG["features"])
        logging.info(f"✅ Data loaded successfully. Shape: {scaled_data.shape}")
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"❌ {e}")
        return

    # 2. Create Time-Series Windows
    logging.info(f"Creating sliding windows (input_size={hp['window_size']}, horizon={hp['forecast_horizon']})...")
    X_windows, y_windows = create_sliding_windows(scaled_data, hp["window_size"], hp["forecast_horizon"])
    logging.info(f"✅ Created {len(X_windows)} windows.")

    # 3. Split Data (shuffle=False is important for time-series validation)
    logging.info("Splitting data into training and testing sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_windows, y_windows, test_size=hp["test_split_size"], random_state=42, shuffle=False
    )

    # 4. Create PyTorch DataLoaders
    train_data = TensorDataset(torch.from_numpy(X_train).float(), torch.from_numpy(y_train).float())
    test_data = TensorDataset(torch.from_numpy(X_test).float(), torch.from_numpy(y_test).float())
    train_loader = DataLoader(train_data, shuffle=True, batch_size=hp["batch_size"])
    test_loader = DataLoader(test_data, shuffle=False, batch_size=hp["batch_size"])

    # 5. Initialize Model, Loss, and Optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Using device: {device}")
    
    model = LSTMForecaster(
        input_size=NUM_FEATURES,
        output_size=NUM_FEATURES,
        hidden_size=hp["lstm_hidden_size"],
        num_layers=hp["lstm_num_layers"],
        forecast_horizon=hp["forecast_horizon"],
        dropout_prob=hp["dropout_prob"]
    ).to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=hp["learning_rate"])

    # 6. Training Loop
    logging.info(f"Starting training for {hp['epochs']} epochs...")
    best_loss = float('inf')
    
    for epoch in range(hp["epochs"]):
        model.train()
        train_loss = 0.0
        for inputs, targets in tqdm(train_loader, desc=f"Epoch {epoch+1}/{hp['epochs']} (Training)"):
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        # --- Evaluation on test set ---
        model.eval()
        test_loss = 0.0
        with torch.no_grad():
            for inputs, targets in test_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                test_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        avg_test_loss = test_loss / len(test_loader)
        logging.info(f"Epoch {epoch+1}/{hp['epochs']}, Train Loss: {avg_train_loss:.6f}, Test Loss: {avg_test_loss:.6f}")

        # Save the model if it has the best test loss so far
        if avg_test_loss < best_loss:
            best_loss = avg_test_loss
            torch.save(model.state_dict(), os.path.join(CONFIG["model_dir"], CONFIG["model_name"]))
            save_scaler(scaler, os.path.join(CONFIG["model_dir"], CONFIG["scaler_name"]))
            logging.info(f"✅ New best model and scaler saved with Test Loss: {best_loss:.6f}")

    logging.info("\n✅ Training complete.")
    logging.info(f"Best model saved to {os.path.join(CONFIG['model_dir'], CONFIG['model_name'])}")
    logging.info(f"Scaler saved to {os.path.join(CONFIG['model_dir'], CONFIG['scaler_name'])}")

if __name__ == '__main__':
    train_model()
