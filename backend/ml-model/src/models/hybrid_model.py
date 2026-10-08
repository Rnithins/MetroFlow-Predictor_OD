from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F


class TemporalEncoder(nn.Module):
    """
    Encodes temporal sequential flow patterns (Hour, Minute, Day, Weekend, Holiday, Festival, Season) via LSTM.
    """
    def __init__(self, input_size: int, hidden_size: int, num_layers: int = 1) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.1 if num_layers > 1 else 0.0
        )
        self.layer_norm = nn.LayerNorm(hidden_size)

    def forward(self, sequence_features: torch.Tensor) -> torch.Tensor:
        # sequence_features: [batch_size, seq_len, input_size]
        lstm_output, _ = self.lstm(sequence_features)
        last_step = lstm_output[:, -1, :]
        return self.layer_norm(last_step)


class SpatialEncoder(nn.Module):
    """
    Encodes station spatial features, connectivity graph degree, distance, and line interchange topology.
    """
    def __init__(self, input_size: int, hidden_size: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )

    def forward(self, spatial_features: torch.Tensor) -> torch.Tensor:
        # spatial_features: [batch_size, input_size]
        return self.net(spatial_features)


class ContextEncoder(nn.Module):
    """
    Encodes external contextual factors (weather, rainfall, temperature, events, cricket match, concert, traffic).
    """
    def __init__(self, input_size: int, hidden_size: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )

    def forward(self, context_features: torch.Tensor) -> torch.Tensor:
        # context_features: [batch_size, input_size]
        return self.net(context_features)


class AdaptiveFusionModule(nn.Module):
    """
    Computes dynamic attention weights across Spatial-Temporal features and Contextual features.
    Learns feature importance weights automatically during training.
    """
    def __init__(self, st_hidden_size: int, ext_hidden_size: int, fused_size: int) -> None:
        super().__init__()
        self.query_layer = nn.Linear(st_hidden_size, fused_size)
        self.st_key = nn.Linear(st_hidden_size, fused_size)
        self.ext_key = nn.Linear(ext_hidden_size, fused_size)
        self.fusion_projection = nn.Linear(st_hidden_size + ext_hidden_size, fused_size)

    def forward(self, st_emb: torch.Tensor, ext_emb: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        query = self.query_layer(st_emb)
        key_st = self.st_key(st_emb)
        key_ext = self.ext_key(ext_emb)

        score_st = torch.sum(query * key_st, dim=1, keepdim=True)
        score_ext = torch.sum(query * key_ext, dim=1, keepdim=True)

        weights = F.softmax(torch.cat([score_st, score_ext], dim=1), dim=1)
        w_st = weights[:, 0:1]
        w_ext = weights[:, 1:2]

        fused = torch.cat([st_emb * w_st, ext_emb * w_ext], dim=1)
        output = self.fusion_projection(fused)
        return output, weights


class AdaptiveFeatureFusionNetwork(nn.Module):
    """
    MetroFlowNet Core AI Model:
    Adaptive Feature Fusion Network for Origin-Destination Passenger Flow Prediction.
    Architecture:
      Input -> Temporal Encoder -> Spatial Encoder -> Context Encoder -> Adaptive Feature Fusion -> Dense Layers -> OD Prediction
    """
    def __init__(
        self,
        input_size: int = 8,
        hidden_size: int = 64,
        graph_hidden_size: int = 32,
        output_size: int = 5
    ) -> None:
        super().__init__()
        self.temporal_encoder = TemporalEncoder(input_size=input_size, hidden_size=hidden_size)
        self.spatial_encoder = SpatialEncoder(input_size=input_size, hidden_size=graph_hidden_size)
        self.context_encoder = ContextEncoder(input_size=input_size, hidden_size=graph_hidden_size)

        self.st_combine = nn.Linear(hidden_size + graph_hidden_size, hidden_size)

        self.fusion_module = AdaptiveFusionModule(
            st_hidden_size=hidden_size,
            ext_hidden_size=graph_hidden_size,
            fused_size=hidden_size
        )

        self.head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size // 2, output_size)
        )

    def forward(
        self,
        sequence_features: torch.Tensor,
        graph_features: torch.Tensor,
        external_features: torch.Tensor | None = None
    ) -> torch.Tensor:
        if external_features is None:
            external_features = sequence_features.mean(dim=1)

        temp_emb = self.temporal_encoder(sequence_features)
        spat_emb = self.spatial_encoder(graph_features)

        st_raw = torch.cat([temp_emb, spat_emb], dim=1)
        st_emb = F.relu(self.st_combine(st_raw))

        ext_emb = self.context_encoder(external_features)

        fused_emb, _ = self.fusion_module(st_emb, ext_emb)
        output = self.head(fused_emb)
        return output

    def forward_with_weights(
        self,
        sequence_features: torch.Tensor,
        graph_features: torch.Tensor,
        external_features: torch.Tensor | None = None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if external_features is None:
            external_features = sequence_features.mean(dim=1)

        temp_emb = self.temporal_encoder(sequence_features)
        spat_emb = self.spatial_encoder(graph_features)

        st_raw = torch.cat([temp_emb, spat_emb], dim=1)
        st_emb = F.relu(self.st_combine(st_raw))

        ext_emb = self.context_encoder(external_features)

        fused_emb, weights = self.fusion_module(st_emb, ext_emb)
        output = self.head(fused_emb)
        return output, weights


# Legacy aliases for backward compatibility
class SpatialTemporalEncoder(nn.Module):
    def __init__(self, input_size: int, hidden_size: int) -> None:
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, batch_first=True)
        self.spatial_layer = nn.Linear(input_size, hidden_size)

    def forward(self, sequence_features: torch.Tensor, graph_features: torch.Tensor) -> torch.Tensor:
        lstm_output, _ = self.lstm(sequence_features)
        temporal_emb = lstm_output[:, -1, :]
        spatial_emb = F.relu(self.spatial_layer(graph_features))
        return temporal_emb + spatial_emb


class ExternalFeatureEncoder(ContextEncoder):
    pass


class HybridLSTMGNN(AdaptiveFeatureFusionNetwork):
    def forward(self, sequence_features: torch.Tensor, graph_features: torch.Tensor) -> torch.Tensor:
        return super().forward(sequence_features, graph_features, graph_features)
