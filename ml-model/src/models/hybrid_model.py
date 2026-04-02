from __future__ import annotations

import torch
from torch import nn


class GraphEncoder(nn.Module):
    def __init__(self, input_size: int, hidden_size: int) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
        )

    def forward(self, graph_features: torch.Tensor) -> torch.Tensor:
        return self.layers(graph_features)


class HybridLSTMGNN(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, graph_hidden_size: int, output_size: int) -> None:
        super().__init__()
        self.temporal_encoder = nn.LSTM(input_size=input_size, hidden_size=hidden_size, batch_first=True)
        self.graph_encoder = GraphEncoder(input_size=input_size, hidden_size=graph_hidden_size)
        self.head = nn.Sequential(
            nn.Linear(hidden_size + graph_hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size),
        )

    def forward(self, sequence_features: torch.Tensor, graph_features: torch.Tensor) -> torch.Tensor:
        lstm_output, _ = self.temporal_encoder(sequence_features)
        temporal_state = lstm_output[:, -1, :]
        graph_state = self.graph_encoder(graph_features)
        return self.head(torch.cat([temporal_state, graph_state], dim=1))
