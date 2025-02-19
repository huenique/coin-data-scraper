from pathlib import Path

from coin_data.proxies import PROXIES

# Proxies
PROXIES_ENABLED = bool(PROXIES)

# Data directory and file pattern
PUMPFUN_DATA_DIR = Path.home() / "pumpfun_data"
PUMPFUN_RESULTS_PATTERN = "results_*.csv"
