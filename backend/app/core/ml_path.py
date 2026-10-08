from __future__ import annotations

import sys
from pathlib import Path


def setup_ml_path() -> Path:
    current_file = Path(__file__).resolve()
    # Candidate locations for ml-model
    candidates = [
        current_file.parents[3] / "ml-model",                  # repo_root/ml-model
        current_file.parents[2] / "ml-model",                  # backend/ml-model
        current_file.parents[1] / "ml-model",                  # app/ml-model
        Path("/app/ml-model"),                                 # container root
        Path("/app/backend/ml-model"),                         # container backend
        Path.cwd() / "ml-model",                               # current working directory
        Path.cwd().parent / "ml-model",                        # cwd parent
    ]
    for c in candidates:
        if c.is_dir() and (c / "src").is_dir():
            ml_dir = str(c)
            if ml_dir not in sys.path:
                sys.path.insert(0, ml_dir)
            return c

    fallback = current_file.parents[2] / "ml-model"
    if str(fallback) not in sys.path:
        sys.path.insert(0, str(fallback))
    return fallback


# Auto-configure on import
setup_ml_path()
