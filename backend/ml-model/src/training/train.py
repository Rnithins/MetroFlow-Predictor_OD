from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.config import ModelConfig
from src.data.od_dataset import generate_smartcard_od_dataset
from src.data.preprocessing import clean_flow_data
from src.features.engineering import build_features
from src.models.hybrid_model import AdaptiveFeatureFusionNetwork


def train_model(
    frame: pd.DataFrame | None = None,
    config: ModelConfig | None = None,
    save_checkpoint: bool = True,
    patience: int = 5
) -> dict:
    """
    Trains the MetroFlowNet Adaptive Feature Fusion Network (AFFN) with Early Stopping,
    LR Scheduler, metric evaluation (RMSE, MAE, MAPE, R²), and checkpoint saving.
    """
    cfg = config or ModelConfig()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if frame is None or frame.empty:
        frame = generate_smartcard_od_dataset(num_days=14)

    prepared = build_features(clean_flow_data(frame))
    feature_cols = [
        "passenger_count",
        "avg_dwell_minutes",
        "hour",
        "day_of_week",
        "is_weekend",
        "is_peak_hour",
        "weather_factor",
        "event_factor",
    ]

    for col in feature_cols:
        if col not in prepared.columns:
            prepared[col] = 1.0 if "factor" in col else 0.0

    features_raw = torch.tensor(prepared[feature_cols].values, dtype=torch.float32)
    targets_raw = torch.tensor(prepared["passenger_count"].values, dtype=torch.float32).unsqueeze(1)

    mean = features_raw.mean(dim=0, keepdim=True)
    std = features_raw.std(dim=0, keepdim=True) + 1e-5
    features_norm = (features_raw - mean) / std

    num_samples = len(features_norm)
    seq_len = cfg.sequence_length

    if num_samples < seq_len:
        padded_feats = torch.zeros((seq_len, len(feature_cols)))
        padded_feats[-num_samples:] = features_norm
        features_norm = padded_feats

        padded_targets = torch.zeros((seq_len, 1))
        padded_targets[-num_samples:] = targets_raw
        targets_raw = padded_targets
        num_samples = seq_len

    seq_list = []
    target_list = []
    for i in range(num_samples - seq_len + 1):
        seq_list.append(features_norm[i : i + seq_len])
        target_list.append(targets_raw[i + seq_len - 1])

    if not seq_list:
        seq_list = [features_norm[:seq_len]]
        target_list = [targets_raw[-1]]

    seq_tensor = torch.stack(seq_list).to(device)  # [B, seq_len, F]
    target_tensor = torch.stack(target_list).to(device)  # [B, 1]

    graph_tensor = seq_tensor.mean(dim=1).to(device)
    ext_tensor = seq_tensor[:, -1, :].to(device)

    model = AdaptiveFeatureFusionNetwork(
        input_size=cfg.input_size,
        hidden_size=cfg.hidden_size,
        graph_hidden_size=cfg.graph_hidden_size,
        output_size=1,
    ).to(device)

    optimizer = AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=1e-4)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
    criterion = nn.HuberLoss()

    best_loss = float("inf")
    epochs_no_improve = 0
    epoch_losses = []

    model.train()
    for epoch in range(cfg.epochs):
        optimizer.zero_grad()
        predictions = model(seq_tensor, graph_tensor, ext_tensor)
        loss = criterion(predictions, target_tensor)
        loss.backward()
        optimizer.step()

        loss_val = float(loss.item())
        epoch_losses.append(loss_val)
        scheduler.step(loss_val)

        if loss_val < best_loss - 1e-4:
            best_loss = loss_val
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                break

    model.eval()
    with torch.no_grad():
        preds_tensor, weights_tensor = model.forward_with_weights(seq_tensor, graph_tensor, ext_tensor)
        final_preds = preds_tensor.squeeze(-1).cpu().numpy()
        actuals = target_tensor.squeeze(-1).cpu().numpy()

        avg_st_weight = float(weights_tensor[:, 0].mean().item())
        avg_ext_weight = float(weights_tensor[:, 1].mean().item())

    rmse = float(mean_squared_error(actuals, final_preds) ** 0.5)
    mae = float(mean_absolute_error(actuals, final_preds))
    r2 = float(r2_score(actuals, final_preds)) if len(actuals) > 1 else 1.0

    nonzero_mask = actuals > 0
    mape = (
        float(np.mean(np.abs((actuals[nonzero_mask] - final_preds[nonzero_mask]) / actuals[nonzero_mask])) * 100)
        if np.any(nonzero_mask)
        else 0.0
    )

    checkpoint_path = ""
    if save_checkpoint:
        models_dir = Path(__file__).resolve().parent.parent.parent / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file = models_dir / "adaptive_fusion_latest.pt"
        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "config": asdict(cfg),
                "mean": mean.cpu(),
                "std": std.cpu(),
                "metrics": {"rmse": rmse, "mae": mae, "mape": mape, "r2": r2},
            },
            checkpoint_file,
        )
        checkpoint_path = str(checkpoint_file)

    return {
        "config": asdict(cfg),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mape_pct": round(mape, 2),
        "r2_score": round(r2, 4),
        "final_loss": round(epoch_losses[-1], 6) if epoch_losses else 0.0,
        "epochs_trained": len(epoch_losses),
        "attention_weights": {
            "spatial_temporal_weight": round(avg_st_weight, 4),
            "external_context_weight": round(avg_ext_weight, 4),
        },
        "num_records_trained": len(prepared),
        "device": str(device),
        "checkpoint_saved": checkpoint_path,
        "status": "completed",
    }


if __name__ == "__main__":
    result = train_model()
    print("Training Complete:", result)
