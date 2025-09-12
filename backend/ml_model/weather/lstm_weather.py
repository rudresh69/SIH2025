"""
lstm_weather.py

This module defines the PyTorch LSTM model architecture for multi-variate
time-series weather nowcasting. It is designed to be flexible and includes
standard features like dropout for regularization.
"""
import torch
import torch.nn as nn

class LSTMForecaster(nn.Module):
    """
    A flexible LSTM model for multi-variate time-series forecasting.
    It takes a sequence of sensor readings and predicts a future sequence.
    """
    def __init__(self,
                 input_size: int,
                 hidden_size: int,
                 num_layers: int,
                 output_size: int,
                 forecast_horizon: int,
                 dropout_prob: float = 0.2):
        """
        Initializes the LSTMForecaster model.

        Args:
            input_size (int): The number of features per time step (e.g., 3 for rain, temp, humidity).
            hidden_size (int): The number of features in the hidden state of the LSTM.
            num_layers (int): The number of recurrent LSTM layers.
            output_size (int): The number of features to predict for each future time step.
            forecast_horizon (int): The number of future time steps to predict.
            dropout_prob (float): The dropout probability to apply between LSTM layers
                                  for regularization.
        """
        super().__init__()
        self.forecast_horizon = forecast_horizon
        self.output_size = output_size

        # --- LSTM Layer ---
        # `batch_first=True` means the input tensor shape will be (batch, sequence, feature).
        # Dropout is only applied if there are 2 or more LSTM layers.
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout_prob if num_layers > 1 else 0
        )
        
        # --- Output Layer ---
        # A fully connected (Linear) layer that maps the LSTM's final hidden state
        # to the desired output shape. The output shape is a flat vector containing
        # all predictions for all future steps.
        self.fc = nn.Linear(hidden_size, forecast_horizon * output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Defines the forward pass of the model.

        Args:
            x (torch.Tensor): The input tensor of shape (batch_size, window_size, input_size).

        Returns:
            torch.Tensor: The predicted output tensor of shape (batch_size, forecast_horizon, output_size).
        """
        # Input shape: (batch_size, window_size, input_size)
        
        # The LSTM returns `lstm_out` and the final `hidden_state`. We only need the output.
        # `lstm_out` contains the output of the last LSTM layer for each time step.
        # Shape of `lstm_out`: (batch_size, window_size, hidden_size)
        lstm_out, _ = self.lstm(x)
        
        # We only care about the output from the very last time step of the sequence,
        # as it contains the summarized information from the entire input window.
        # Shape of `last_step_out`: (batch_size, hidden_size)
        last_step_out = lstm_out[:, -1, :]
        
        # Pass the last step's output through the fully connected layer.
        # Shape of `output`: (batch_size, forecast_horizon * output_size)
        output = self.fc(last_step_out)

        # Reshape the flat output vector into our desired forecast format.
        # Final shape: (batch_size, forecast_horizon, output_size)
        output = output.view(-1, self.forecast_horizon, self.output_size)
        
        return output
