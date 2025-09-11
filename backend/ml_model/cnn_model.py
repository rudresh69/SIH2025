"""
ml_model/cnn_model.py
This file defines the 1D Convolutional Neural Network (CNN) architecture
used for classifying the time-series sensor data.
"""
import torch
import torch.nn as nn

class CNNModel(nn.Module):
    """
    A flexible 1D Convolutional Neural Network for time-series classification.
    It dynamically creates the fully-connected layer to adapt to different
    input window sizes.
    """
    def __init__(self, num_features: int, num_classes: int = 2):
        """
        Args:
            num_features (int): The number of input features (e.g., number of sensors).
            num_classes (int): The number of output classes (e.g., 2 for Normal/Event).
        """
        super(CNNModel, self).__init__()

        # --- FIX ---
        # Store num_classes as an attribute so it can be accessed in the forward pass.
        self.num_classes = num_classes

        # First convolutional block
        self.conv1 = nn.Sequential(
            nn.Conv1d(in_channels=num_features, out_channels=64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.MaxPool1d(kernel_size=2, stride=2)
        )

        # Second convolutional block
        self.conv2 = nn.Sequential(
            nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.MaxPool1d(kernel_size=2, stride=2)
        )

        self.flatten = nn.Flatten()

        # The fully-connected layers will be defined dynamically in the forward pass
        # to adapt to different input window sizes.
        self.fc_layers = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for the model.
        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, window_size, num_features).
        Returns:
            torch.Tensor: Output tensor of raw logits with shape (batch_size, num_classes).
        """
        # PyTorch Conv1D expects input as (batch_size, num_features, window_size)
        x = x.permute(0, 2, 1)

        # Pass through convolutional blocks
        x = self.conv1(x)
        x = self.conv2(x)

        # Flatten the output for the fully-connected layers
        x = self.flatten(x)

        # On the first forward pass, dynamically create the FC layers
        if self.fc_layers is None:
            # Get the number of features after the conv layers have processed the input
            num_fc_features = x.shape[1]
    
            self.fc_layers = nn.Sequential(
                nn.Linear(num_fc_features, 128),
                nn.ReLU(),
                nn.Dropout(0.5),
                # --- FIX ---
                # Use the stored attribute here
                nn.Linear(128, self.num_classes)
            ).to(x.device) # IMPORTANT: Move the new layers to the correct GPU/CPU device

        # Pass through the fully-connected layers
        x = self.fc_layers(x)

        return x

