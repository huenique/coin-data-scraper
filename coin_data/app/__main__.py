import glob
import os
from datetime import datetime, timezone

import polars as pl
import pytz
import streamlit as st

from coin_data.config import PUMPFUN_DATA_DIR, PUMPFUN_RESULTS_PATTERN

data_dir = PUMPFUN_DATA_DIR
file_pattern = PUMPFUN_RESULTS_PATTERN


def get_csv_files():
    return sorted(glob.glob(os.path.expanduser(os.path.join(data_dir, file_pattern))))


@st.cache_data
def load_data(file_path: str) -> pl.DataFrame:
    """Loads CSV data with caching, but will be cleared on refresh."""
    df = pl.DataFrame()
    try:
        df = pl.read_csv(file_path)
    except pl.exceptions.NoDataError as e:
        st.error(f"Error loading data: {e}")
    return df


def search_filter(df: pl.DataFrame, query: str) -> pl.DataFrame:
    """Filters the dataframe based on a search query."""
    if not query.strip():
        return df
    df_str = df.with_columns(pl.all().cast(pl.Utf8).fill_null(""))
    combined = df_str.with_columns(
        pl.concat_str(pl.all(), separator=" ").alias("combined")
    )
    mask = combined["combined"].str.contains(query, literal=False, strict=False)
    return df.filter(mask)


def market_cap_filter(df: pl.DataFrame, operator: str, value: float) -> pl.DataFrame:
    """Filters the dataframe based on the market cap operator and value."""
    if operator not in [">", "<"] or "current_market_cap" not in df.columns:
        return df
    return df.filter(
        df["current_market_cap"] > value
        if operator == ">"
        else df["current_market_cap"] < value
    )


def convert_to_est(timestamp: int | float) -> str:
    """Converts a timestamp to EST timezone."""
    est = pytz.timezone("America/New_York")
    dt = (
        datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        .replace(tzinfo=pytz.utc)
        .astimezone(est)
    )
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


# Streamlit UI
st.set_page_config(layout="wide")
st.title("Coin Data")

# Get available files
csv_files = get_csv_files()
if not csv_files:
    st.error(f"No CSV files found in {PUMPFUN_DATA_DIR}")
    st.stop()

# Dropdown to select file
selected_file = st.selectbox("Select a CSV file:", csv_files)

# Load and display data
df = load_data(selected_file)

# Display number of rows
st.write(f"Total graduated tokens with metadata on pump.fun: {df.height}")  # type: ignore

# Search Box for general filtering
search_query = st.text_input("Search:", "")

# Market Cap Filtering: Combine operator and value into one row
col1, col2 = st.columns([1, 3])

with col1:
    market_cap_operator = st.selectbox(
        "Market Cap", [None, ">", "<"], key="market_cap_op"
    )

with col2:
    market_cap_value = st.number_input(
        "Value", min_value=0.0, value=0.0, step=1e6, key="market_cap_val"
    )

# Load and filter data
df_filtered = search_filter(df, search_query)

if market_cap_operator is not None:
    df_filtered = market_cap_filter(df_filtered, market_cap_operator, market_cap_value)

# Modify Image URIs to use Pinata Gateway
df_filtered = df_filtered.with_columns(
    pl.col("image_uri").str.replace(
        "https://ipfs.io/ipfs/", "https://pump.mypinata.cloud/ipfs/"
    )
)

# Append ?img-width=32 to the image URI
df_filtered = df_filtered.with_columns(
    pl.col("image_uri").map_elements(
        lambda url: f"{url}?img-width=32" if isinstance(url, str) else "",
        return_dtype=pl.Utf8,
    )
)

# Ensure image_uri contains direct image URLs
df_filtered = df_filtered.with_columns(
    pl.col("image_uri").map_elements(
        lambda url: url if isinstance(url, str) else "", return_dtype=pl.Utf8
    )
)

# Convert created_timestamp to EST
df_filtered = df_filtered.with_columns(
    pl.col("created_timestamp").map_elements(
        lambda ts: convert_to_est(ts) if isinstance(ts, (int, float)) else "",
        return_dtype=pl.Utf8,
    )
)

# Custom column headers
column_headers = {
    "name": "Token Name",
    "symbol": "Symbol",
    "mint": "Mint Address",
    "volume": "Trading Volume",
    "holder_count": "Holder Count",
    "image_uri": "Image",
    "telegram": "Telegram",
    "twitter": "Twitter",
    "website": "Website",
    "created_timestamp": "Created (EST)",
    "highest_market_cap": "Highest Market Cap ($)",
    "highest_market_cap_timestamp": "Highest Market Cap Timestamp",
    "lowest_market_cap": "Lowest Market Cap ($)",
    "lowest_market_cap_timestamp": "Lowest Market Cap Timestamp",
    "current_market_cap": "Current Market Cap ($)",
    "current_market_cap_timestamp": "Current Market Cap Timestamp",
}

# Rename columns
df_filtered = df_filtered.rename(column_headers)

# Exclude Raydium Pool column from display
display_columns = [col for col in df_filtered.columns if col.lower() != "raydium_pool"]

# Define mcap_columns list
mcap_columns = [
    "Highest Market Cap ($)",
    "Lowest Market Cap ($)",
    "Current Market Cap ($)",
]

# Use st.data_editor for proper numeric sorting
st.data_editor(
    df_filtered.select(display_columns).to_pandas(),
    column_config={
        "Image": st.column_config.ImageColumn("Image"),
        **{col: st.column_config.NumberColumn(col) for col in mcap_columns},
    },
    hide_index=True,
)
