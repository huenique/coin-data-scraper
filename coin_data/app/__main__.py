import glob
import os

import polars as pl
import streamlit as st

# Path to CSV files
data_dir = "/home/huenique/"
file_pattern = "results_*.csv"


# Get list of available CSV files
def get_csv_files():
    return sorted(glob.glob(os.path.join(data_dir, file_pattern)))


# Load CSV data
@st.cache_data
def load_data(file_path: str) -> pl.DataFrame:
    return pl.read_csv(file_path)


def search_filter(df: pl.DataFrame, query: str) -> pl.DataFrame:
    # Convert all columns to UTF8 (string) for safe searching
    df_str = df.select(pl.all().cast(pl.Utf8))

    # Create a single concatenated column with all text data
    combined = df_str.with_columns(
        pl.concat_str(pl.all(), separator=" ").alias("combined")
    )

    # Filter based on the search query
    mask = combined["combined"].str.contains(query, literal=True)

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
st.title("Coin Data")

# Get available files
csv_files = get_csv_files()
if not csv_files:
    st.error("No CSV files found in /data/")
    st.stop()

# Dropdown to select file
selected_file = st.selectbox("Select a CSV file:", csv_files)

# Load and display data
df = load_data(selected_file)

# Search Box for general filtering
search_query = st.text_input("Search:", "")

# Market Cap Filtering: User selects `>` or `<` and enters a value
market_cap_operator = st.selectbox("Market Cap Filter:", [None, ">", "<"])
market_cap_value = st.number_input(
    "Market Cap Value:", min_value=0.0, value=0.0, step=1e6
)

# Load and filter data
df_filtered = search_filter(df, search_query)  # Apply search filter

if market_cap_operator is not None:
    df_filtered = market_cap_filter(df_filtered, market_cap_operator, market_cap_value)


# Display DataFrame
st.dataframe(df_filtered)  # type: ignore
