# ml_model/cnn_model.py
import torch
import torch.nn as nn

class CNN1D(nn.Module):
    def __init__(self, in_channels=8):
        super(CNN1D, self).__init__()
        self.conv1 = nn.Conv1d(in_channels, 64, kernel_size=7, padding=3)
        self.bn1 = nn.BatchNorm1d(64)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=5, stride=2, padding=2)
        self.bn2 = nn.BatchNorm1d(128)
        self.conv3 = nn.Conv1d(128, 256, kernel_size=5, stride=2, padding=2)
        self.bn3 = nn.BatchNorm1d(256)
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(256, 256)
        self.dropout = nn.Dropout(0.2)
        self.out = nn.Linear(256, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = x.permute(0, 2, 1)
        x = nn.ReLU()(self.bn1(self.conv1(x)))
        x = nn.ReLU()(self.bn2(self.conv2(x)))
        x = nn.ReLU()(self.bn3(self.conv3(x)))
        x = self.global_pool(x).squeeze(-1)
        x = nn.ReLU()(self.fc1(x))
        x = self.dropout(x)
        x = self.sigmoid(self.out(x))
        return x
