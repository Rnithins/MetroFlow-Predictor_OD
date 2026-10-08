import sys
from pathlib import Path

ML_MODEL_DIR = Path(__file__).resolve().parents[1]
if str(ML_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(ML_MODEL_DIR))
