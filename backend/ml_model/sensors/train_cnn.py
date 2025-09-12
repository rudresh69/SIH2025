"""
ml_model/sensors/train_cnn.py
Training pipeline for the 1D CNN rockfall prediction model.

This file is updated to work with the new project folder structure.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
import os
import sys
import joblib

# --- [CHANGE 1] PATH SETUP ---
# The BASE_DIR now points to the root 'backend' folder by going up three levels.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# --- [CHANGE 2] MODEL IMPORT ---
# Use a relative import to get the CNNModel class from the cnn_model.py
# file located in this same directory.
from .cnn_model import CNNModel

# --- [CHANGE 3] CONFIGURATION & PATHS ---
# Paths are now correctly constructed from the new BASE_DIR to find the dataset
# and save the model/scaler artifacts in their new location.
DATASET_PATH = os.path.join(BASE_DIR, "rockfall_dataset_refined.csv")
BEST_MODEL_PATH = os.path.join(BASE_DIR, "ml_model", "sensors", "best_cnn_model.pth")
SCALER_PATH = os.path.join(BASE_DIR, "ml_model", "sensors", "scaler.pkl")
WINDOW_SIZE = 50
BATCH_SIZE = 64
EPOCHS = 15
LEARNING_RATE = 0.001
TEST_SPLIT_SIZE = 0.2

def create_windows(X: np.ndarray, y: np.ndarray, window_size: int):
    """Converts a flat time-series array into a dataset of sliding windows."""
    X_windows, y_windows = [], []
    for i in range(len(X) - window_size):
        X_windows.append(X[i:i + window_size])
        # The label for a window is the label of the last data point in that window
        y_windows.append(y[i + window_size - 1])
    return np.array(X_windows), np.array(y_windows)

def train_model():
    """Main function to load data, preprocess, train the model, and save artifacts."""
    print("🚀 Starting model training pipeline...")

    if not os.path.exists(DATASET_PATH):
        print(f"❌ Dataset not found at '{DATASET_PATH}'.")
        print("Please run the dataset generation script first: python dataset/rockfall_dataset_pipeline.py")
        return

    df = pd.read_csv(DATASET_PATH)

    feature_columns = [
        "accelerometer", "geophone", "seismometer", "moisture_sensor", "piezometer",
        "crack_sensor", "inclinometer", "extensometer", "rain_sensor_mmhr",
        "temperature_celsius", "humidity_percent"
    ]

    X = df[feature_columns].values
    y = df["label"].values
    NUM_FEATURES = X.shape[1]
    print(f"✅ Data loaded successfully with {NUM_FEATURES} features.")

    # --- Preprocessing ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Save the fitted scaler for use in the live API
    os.makedirs(os.path.dirname(SCALER_PATH), exist_ok=True) # Ensure directory exists
    joblib.dump(scaler, SCALER_PATH)
    print(f"✅ Scaler saved to {SCALER_PATH}")

    X_windows, y_windows = create_windows(X_scaled, y, WINDOW_SIZE)
    print(f"✅ Created {len(X_windows)} time-series windows of size {WINDOW_SIZE}.")

    # --- Train/Test Split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X_windows, y_windows, test_size=TEST_SPLIT_SIZE, random_state=42, stratify=y_windows
    )

    train_data = TensorDataset(torch.from_numpy(X_train).float(), torch.from_numpy(y_train).long())
    test_data = TensorDataset(torch.from_numpy(X_test).float(), torch.from_numpy(y_test).long())
    train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=BATCH_SIZE)
    print("✅ Data split and prepared for training.")

    # --- Model Setup ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🧠 Using device: {device}")

    model = CNNModel(num_features=NUM_FEATURES, num_classes=2).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    best_test_acc = 0.0

    # --- Training Loop ---
    print("⏳ Starting training loop...")
    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0.0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # --- Evaluation ---
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        test_acc = 100 * correct / total
        print(f"Epoch {epoch+1:02d}/{EPOCHS} | Loss: {train_loss/len(train_loader):.4f} | Test Accuracy: {test_acc:.2f}%")

        if test_acc > best_test_acc:
            best_test_acc = test_acc
            torch.save(model.state_dict(), BEST_MODEL_PATH)
            print(f"   -> 🎉 New best model saved with accuracy: {best_test_acc:.2f}%")

    print("\n✅ Training complete.")
    print(f"🏆 Best model saved to: {BEST_MODEL_PATH}")
    print(f"🔧 Scaler saved to: {SCALER_PATH}")

if __name__ == "__main__":
    train_model()
