# ml_model/train_cnn.py

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split

# Package-safe import
from .cnn_model import CNN1D

# -------------------------------
# Paths
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X_PATH = os.path.join(BASE_DIR, "X_windows.npy")
Y_PATH = os.path.join(BASE_DIR, "y_windows.npy")
BEST_MODEL_PATH = os.path.join(BASE_DIR, "ml_model", "best_cnn_model.pth")

# -------------------------------
# Load dataset
# -------------------------------
X = np.load(X_PATH)  # shape: (N, window_length, 8)
y = np.load(Y_PATH)  # shape: (N,)

X = torch.tensor(X, dtype=torch.float32)
y = torch.tensor(y, dtype=torch.float32).unsqueeze(1)

# -------------------------------
# Train/Val/Test split
# -------------------------------
dataset = TensorDataset(X, y)
train_size = int(0.8 * len(dataset))
val_size = int(0.1 * len(dataset))
test_size = len(dataset) - train_size - val_size
train_dataset, val_dataset, test_dataset = random_split(dataset, [train_size, val_size, test_size])

train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

# -------------------------------
# Device & Model
# -------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = CNN1D(in_channels=X.shape[2]).to(device)
criterion = nn.BCELoss()
optimizer = optim.AdamW(model.parameters(), lr=0.001)

# -------------------------------
# Training loop
# -------------------------------
num_epochs = 20
best_val_loss = float('inf')

for epoch in range(num_epochs):
    model.train()
    train_loss = 0
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        out = model(xb)
        loss = criterion(out, yb)
        loss.backward()
        optimizer.step()
        train_loss += loss.item() * xb.size(0)
    train_loss /= len(train_loader.dataset)

    model.eval()
    val_loss = 0
    with torch.no_grad():
        for xb, yb in val_loader:
            xb, yb = xb.to(device), yb.to(device)
            out = model(xb)
            loss = criterion(out, yb)
            val_loss += loss.item() * xb.size(0)
    val_loss /= len(val_loader.dataset)

    print(f"Epoch {epoch+1}/{num_epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")

    # Save best model
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), BEST_MODEL_PATH)
        print("✅ Saved Best Model")

# -------------------------------
# Test Evaluation
# -------------------------------
model.load_state_dict(torch.load(BEST_MODEL_PATH, map_location=device))
model.eval()
y_true, y_pred = [], []
with torch.no_grad():
    for xb, yb in test_loader:
        xb = xb.to(device)
        out = model(xb)
        y_pred.extend(out.cpu().numpy())
        y_true.extend(yb.numpy())

y_pred = np.array(y_pred) > 0.5
accuracy = (y_pred.flatten() == np.array(y_true).flatten()).mean()
print(f"✅ Test Accuracy: {accuracy*100:.2f}%")
