import os
import sys
from pathlib import Path


API_DIR = Path(__file__).resolve().parent / "fitguard-api"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from run import app


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "10000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
