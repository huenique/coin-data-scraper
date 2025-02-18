import glob
import os

import polars as pl
import streamlit as st

from coin_data.common import PUMPFUN_DATA_DIR, PUMPFUN_RESULTS_PATTERN

data_dir = PUMPFUN_DATA_DIR
file_pattern = PUMPFUN_RESULTS_PATTERN


def get_csv_files():
    return sorted(glob.glob(os.path.expanduser(os.path.join(data_dir, file_pattern))))


@st.cache_data
def load_data(file_path: str) -> pl.DataFrame:
    return pl.read_csv(file_path)


def search_filter(df: pl.DataFrame, query: str) -> pl.DataFrame:
    # If query is empty, return the full DataFrame
    if not query.strip():
        return df

    # Convert all columns to UTF8 (string) for safe searching, replacing nulls with empty strings
    df_str = df.with_columns(pl.all().cast(pl.Utf8).fill_null(""))

    # Create a single concatenated column with all text data
    combined = df_str.with_columns(
        pl.concat_str(pl.all(), separator=" ").alias("combined")
    )

    # Filter based on the search query (case-insensitive)
    mask = combined["combined"].str.contains(query, literal=True, strict=False)

    # Apply the mask to the original DataFrame (not `combined`)
    return df.filter(mask)


def market_cap_filter(df: pl.DataFrame, operator: str, value: float) -> pl.DataFrame:
    if operator not in [">", "<"] or "current_market_cap" not in df.columns:
        return df  # Return unfiltered if no valid operator or column missing

    if operator == ">":
        return df.filter(df["current_market_cap"] > value)
    elif operator == "<":
        return df.filter(df["current_market_cap"] < value)

    return df


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
st.write(f"Number of rows: {df.height}")  # type: ignore

# Search Box for general filtering
search_query = st.text_input("Search:", "")

# Market Cap Filtering: Combine operator and value into one row
col1, col2 = st.columns([1, 3])  # Adjust column widths as needed

with col1:
    market_cap_operator = st.selectbox(
        "Market Cap", [None, ">", "<"], key="market_cap_op"
    )

with col2:
    market_cap_value = st.number_input(
        "Value", min_value=0.0, value=0.0, step=1e6, key="market_cap_val"
    )

# Load and filter data
df_filtered = search_filter(df, search_query)  # Apply search filter

if market_cap_operator is not None:
    df_filtered = market_cap_filter(df_filtered, market_cap_operator, market_cap_value)

# Display filtered DataFrame
st.dataframe(df_filtered)  # type: ignore
