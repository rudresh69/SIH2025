"""
data.py

This module handles data loading, preprocessing, scaling, and the creation of
time-series windows for forecasting models. It is designed to be reusable
and configurable.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
from typing import List, Tuple

def load_and_preprocess_data(file_path: str, feature_columns: List[str]) -> Tuple[np.ndarray, StandardScaler, np.ndarray]:
    """
    Loads data from a CSV file, selects and validates specified features,
    scales them using a StandardScaler, and returns the results.

    Args:
        file_path (str): The full path to the input CSV dataset.
        feature_columns (List[str]): A list of column names to be used as features.

    Returns:
        Tuple[np.ndarray, StandardScaler, np.ndarray]: A tuple containing:
            - The scaled feature data as a numpy array.
            - The fitted StandardScaler object.
            - The original data labels as a numpy array.
            
    Raises:
        FileNotFoundError: If the specified file_path does not exist.
        ValueError: If any of the specified feature_columns are not in the CSV.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset not found at '{file_path}'. Please generate the dataset first.")

    df = pd.read_csv(file_path)

    # --- Robustness Check: Ensure all required columns exist ---
    for col in feature_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in the dataset at {file_path}.")

    data = df[feature_columns].values

    # Initialize and fit the scaler to the selected feature data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)

    return scaled_data, scaler, df['label'].values


def create_sliding_windows(data: np.ndarray, window_size: int, horizon: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Creates sliding input-output windows from time-series data for forecasting.

    Args:
        data (np.ndarray): The time-series data (e.g., scaled features).
        window_size (int): The number of time steps in each input sequence (X).
        horizon (int): The number of future time steps to predict in the target sequence (y).

    Returns:
        Tuple[np.ndarray, np.ndarray]: A tuple containing:
            - X: The input windows of shape (num_samples, window_size, num_features).
            - y: The target windows of shape (num_samples, horizon, num_features).
    """
    X, y = [], []
    # The loop must stop early enough to leave room for a full input window AND a full target horizon
    for i in range(len(data) - window_size - horizon + 1):
        input_window = data[i:(i + window_size)]
        target_window = data[(i + window_size):(i + window_size + horizon)]
        X.append(input_window)
        y.append(target_window)

    return np.array(X), np.array(y)


def save_scaler(scaler: StandardScaler, file_path: str) -> None:
    """Saves a fitted StandardScaler object to a file using joblib."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    joblib.dump(scaler, file_path)
    print(f"Scaler saved to {file_path}")


def load_scaler(file_path: str) -> StandardScaler:
    """Loads a StandardScaler object from a file using joblib."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Scaler file not found at {file_path}")
    return joblib.load(file_path)


if __name__ == '__main__':
    # This block demonstrates how to use the functions in this module.
    # It will only run when you execute this script directly (e.g., `python data.py`).
    print("--- Data Module Demonstration ---")
    
    # Define paths relative to this script's location
    # Assumes structure is backend/ml_model/weather/data.py
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dataset_path = os.path.join(BASE_DIR, 'rockfall_dataset_refined.csv')
    
    # Define the features we want to use for this demonstration
    WEATHER_FEATURES_DEMO = [
        "rain_sensor_mmhr",
        "temperature_celsius",
        "humidity_percent"
    ]
    
    try:
        print(f"Loading data from: {dataset_path}")
        scaled_data, scaler, _ = load_and_preprocess_data(dataset_path, WEATHER_FEATURES_DEMO)
        print(f"✅ Loaded and scaled data. Shape: {scaled_data.shape}")

        X, y = create_sliding_windows(scaled_data, window_size=30, horizon=5)
        print(f"✅ Created windows. X shape: {X.shape}, y shape: {y.shape}")
        
        # Demonstrate saving and loading the scaler
        temp_scaler_path = os.path.join(os.path.dirname(__file__), 'temp_scaler_demo.pkl')
        save_scaler(scaler, temp_scaler_path)
        
        loaded_scaler = load_scaler(temp_scaler_path)
        print(f"✅ Scaler loaded successfully. Type: {type(loaded_scaler)}")
        os.remove(temp_scaler_path) # Clean up the temporary file

    except (FileNotFoundError, ValueError) as e:
        print(f"❌ ERROR: {e}")
