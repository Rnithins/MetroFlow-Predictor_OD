
from dataclasses import dataclass


@dataclass
class ModelConfig:
    input_size: int = 8
    hidden_size: int = 64
    graph_hidden_size: int = 32
    output_size: int = 1
    sequence_length: int = 12
    learning_rate: float = 0.001
    epochs: int = 20
    model_version: str = "metroflow-baseline-regression-v2"
