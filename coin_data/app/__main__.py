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

# Search Box
search_query = st.text_input("Search:", "")

# Filter the dataframe based on search
if search_query:
    df = search_filter(df, search_query)

# Display DataFrame
st.dataframe(df)  # type: ignore
