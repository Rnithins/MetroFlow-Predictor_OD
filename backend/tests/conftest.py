import os
import sys
from pathlib import Path

os.environ["MONGODB_URI"] = "mongomock://localhost"
os.environ["MONGODB_DATABASE"] = "metroflow_predictor_test"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["MODEL_VERSION"] = "metroflow-baseline-regression-v2"

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
