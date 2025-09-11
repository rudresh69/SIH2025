"""
ml_model/train_cnn.py
This script handles the complete training pipeline for the 1D CNN model.
It loads the generated dataset, preprocesses it by scaling and creating
time-series windows, splits it into training and testing sets, trains the model,
and saves the best-performing version.
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

# Add the parent directory to the path to allow package-safe imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Assuming your model class is named CNNModel as in previous suggestions
from ml_model.cnn_model import CNNModel

# --- CONFIGURATION ---
DATASET_PATH = os.path.join(BASE_DIR, "rockfall_dataset_refined.csv")
BEST_MODEL_PATH = os.path.join(BASE_DIR, "ml_model", "best_cnn_model.pth")
WINDOW_SIZE = 50      # The number of time steps in each sample (sequence length)
BATCH_SIZE = 64
EPOCHS = 15
LEARNING_RATE = 0.001
TEST_SPLIT_SIZE = 0.2

def create_windows(X: np.ndarray, y: np.ndarray, window_size: int):
    """
    Creates overlapping windows from time-series data.
    """
    X_windows, y_windows = [], []
    # Ensure we don't go out of bounds
    for i in range(len(X) - window_size):
        X_windows.append(X[i:i + window_size])
        # The label for a window is the label at the end of that window
        y_windows.append(y[i + window_size - 1])
    return np.array(X_windows), np.array(y_windows)

def train_model():
    """
    Main function to orchestrate the model training pipeline.
    """
    print("Starting model training process...")

    # 1. Load Data
    print(f"Loading data from {DATASET_PATH}...")
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Error: Dataset not found at '{DATASET_PATH}'.")
        print("Please run the 'dataset/rockfall_dataset_pipeline.py' script first.")
        return

    df = pd.read_csv(DATASET_PATH)

    # Define the feature columns to be used for training
    feature_columns = [
        "accelerometer", "geophone", "seismometer", "moisture_sensor", "piezometer",
        "crack_sensor", "inclinometer", "extensometer", "rain_sensor_mmhr",
        "temperature_celsius", "humidity_percent"
    ]
    
    # Verify that all required columns exist in the DataFrame
    for col in feature_columns + ['label']:
        if col not in df.columns:
            print(f"❌ Error: Column '{col}' not found in the dataset!")
            return

    X = df[feature_columns].values
    y = df['label'].values
    NUM_FEATURES = X.shape[1]
    print(f"✅ Data loaded successfully with {NUM_FEATURES} features.")

    # 2. Preprocess Data
    print("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"Creating time-series windows of size {WINDOW_SIZE}...")
    X_windows, y_windows = create_windows(X_scaled, y, WINDOW_SIZE)
    print(f"Created {len(X_windows)} windows.")
    
    # 3. Split Data
    print(f"Splitting data into training and testing sets ({1-TEST_SPLIT_SIZE:.0%}/{TEST_SPLIT_SIZE:.0%})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_windows, y_windows, test_size=TEST_SPLIT_SIZE, random_state=42, stratify=y_windows
    )

    # 4. Create PyTorch DataLoaders
    train_data = TensorDataset(torch.from_numpy(X_train).float(), torch.from_numpy(y_train).long())
    test_data = TensorDataset(torch.from_numpy(X_test).float(), torch.from_numpy(y_test).long())
    
    train_loader = DataLoader(train_data, shuffle=True, batch_size=BATCH_SIZE)
    test_loader = DataLoader(test_data, batch_size=BATCH_SIZE)

    # 5. Initialize Model, Loss, and Optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Pass the number of features to the model constructor
    model = CNNModel(num_features=NUM_FEATURES, num_classes=2).to(device)
    
    # Use CrossEntropyLoss for multi-class classification (it handles softmax internally)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # 6. Training Loop
    print(f"Training for {EPOCHS} epochs...")
    best_test_acc = 0.0
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

        # Evaluation on test set after each epoch
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        test_accuracy = 100 * correct / total
        print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {train_loss/len(train_loader):.4f}, Test Accuracy: {test_accuracy:.2f}%")

        # Save the model if it has the best accuracy so far
        if test_accuracy > best_test_acc:
            best_test_acc = test_accuracy
            torch.save(model.state_dict(), BEST_MODEL_PATH)
            print(f"✅ New best model saved with accuracy: {best_test_acc:.2f}%")

    print("\n✅ Training complete.")
    print(f"Best model saved to {BEST_MODEL_PATH} with accuracy {best_test_acc:.2f}%")

if __name__ == '__main__':
    train_model()
