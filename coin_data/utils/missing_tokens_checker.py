import polars as pl

from coin_data import logger

activities_path = ""
results_path = ""

activities_df = pl.read_csv(activities_path)
results_df = pl.read_csv(results_path)

# Extract unique token addresses from both datasets
activities_tokens = set(activities_df["TokenAddress"].to_list())
results_tokens = set(results_df["mint"].to_list())

# Find missing tokens
missing_tokens = activities_tokens - results_tokens

logger.info(f"Missing tokens: {missing_tokens}")
