import glob
import json
import os
from datetime import date, datetime, timezone
from typing import Union

import altair as alt
import polars as pl
import pytz
import streamlit as st

from coin_data.config import PUMPFUN_DATA_DIR, PUMPFUN_RESULTS_PATTERN

data_dir = PUMPFUN_DATA_DIR
file_pattern = PUMPFUN_RESULTS_PATTERN


def get_csv_files():
    return sorted(glob.glob(os.path.expanduser(os.path.join(data_dir, file_pattern))))


@st.cache_data  # type: ignore
def load_data(file_path: str) -> pl.DataFrame:
    """Loads CSV data with caching, but will be cleared on refresh."""
    df = pl.DataFrame()
    try:
        df = pl.read_csv(file_path)
    except pl.exceptions.NoDataError as e:
        st.error(f"Error loading data: {e}")
    return df


@st.cache_data  # type: ignore
def build_graduated_tokens_data() -> pl.DataFrame:
    """Return a Polars DataFrame with columns:
    date, daily_count, cumulative_count
    """
    files = get_csv_files()
    data: list[dict[str, date | int]] = []

    for f in files:
        # Extract date from filename: "results_YYYY-MM-DD.csv"
        file_date_str = os.path.basename(f).replace("results_", "").replace(".csv", "")
        # Convert string to a date object
        file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()

        # Load the CSV
        df_f = load_data(f)
        daily_count = df_f.height  # number of rows

        data.append({"date": file_date, "daily_count": daily_count})

    # Build a Polars DataFrame and sort by date
    df_chart = pl.DataFrame(data).sort("date")

    # Compute the cumulative sum of daily_count
    df_chart = df_chart.with_columns(
        (pl.col("daily_count").cum_sum()).alias("cumulative_count")
    )

    return df_chart


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
    """Converts a timestamp to EST timezone in 12-hour format."""
    est = pytz.timezone("America/New_York")
    dt = (
        datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        .replace(tzinfo=pytz.utc)
        .astimezone(est)
    )
    return dt.strftime("%B %d, %Y %I:%M %p %Z")


# Streamlit UI
st.set_page_config(layout="wide")
st.title("Coin Data")

# Button to manually refresh the data
if st.button("Refresh Data"):
    st.cache_data.clear()  # Clear cached data

    # Clear session state to reset UI elements
    for key in st.session_state.keys():
        del st.session_state[key]

    st.rerun()


# Get available files
csv_files = get_csv_files()
if not csv_files:
    st.error(f"No CSV files found in {PUMPFUN_DATA_DIR}")
    st.stop()

# Ensure "selected_file" exists in session state
if "selected_file" not in st.session_state:
    st.session_state["selected_file"] = (
        csv_files[0] if csv_files else None
    )  # Default to first file

# Dropdown to select file (resets properly)
selected_file = st.selectbox("Select a CSV file:", csv_files, key="selected_file")

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

# Append ?img-width=128&img-height=128 to the image URI
df_filtered = df_filtered.with_columns(
    pl.col("image_uri").map_elements(
        lambda url: (
            f"{url}?img-width=258&img-height=258" if isinstance(url, str) else ""
        ),
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
    "volume": "24H Trading Volume ($)",
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

# Define the Neo BullX URL format
neo_bullx_url_template = "https://neo.bullx.io/terminal?chainId=1399811149&address="

# Identify the correct mint column name dynamically
mint_col_name = None
for col in df_filtered.columns:
    if "mint" in col.lower():  # Detects variations like "Mint Address" or "mint"
        mint_col_name = col
        break

if mint_col_name:
    df_filtered = df_filtered.with_columns(
        (neo_bullx_url_template + pl.col(mint_col_name)).alias("Mint Address")
    )
else:
    st.error("Error: Mint Address column not found in DataFrame.")
    st.stop()

# Identify the correct mint column name dynamically
mint_col_name = None
for col in df_filtered.columns:
    if "mint" in col.lower():  # Detects variations like "Mint Address" or "mint"
        mint_col_name = col
        break

st.data_editor(
    df_filtered.select(display_columns).to_pandas(),
    column_config={
        "Mint Address": st.column_config.LinkColumn(
            "Mint Address",
        ),
        "Image": st.column_config.ImageColumn("Image"),
        "Telegram": st.column_config.LinkColumn("Telegram", width="medium"),
        "Twitter": st.column_config.LinkColumn("Twitter", width="medium"),
        "Website": st.column_config.LinkColumn("Website", width="medium"),
        **{col: st.column_config.NumberColumn(col) for col in mcap_columns},
    },
    hide_index=True,
)


def load_ai_report(selected_file: str):
    """Loads AI-generated market analysis from JSON matching the selected CSV file date."""
    report_date = (
        os.path.basename(selected_file).replace("results_", "").replace(".csv", "")
    )
    report_path = os.path.join(
        PUMPFUN_DATA_DIR, "reports", f"report_{report_date}.json"
    )
    try:
        with open(report_path, "r") as file:
            return json.load(file)
    except Exception as _e:
        return None


# AI Market Analysis Drawer
ai_report = load_ai_report(selected_file)


def format_value(value: Union[str, dict[str, str], list[str]]) -> str:
    """Convert values into a readable format."""
    if isinstance(value, dict):
        return str(value)  # Convert dictionaries to strings
    elif isinstance(value, list):
        return ", ".join(map(str, value))  # Flatten lists into comma-separated strings
    return str(value)


def display_table(
    title: str, data: Union[dict[str, str], list[str], list[dict[str, str]], str]
):
    """Display nested dictionary data in a table format using Polars."""
    st.subheader(title)

    if isinstance(data, dict):
        df = pl.DataFrame(
            {"Key": list(data.keys()), title: [format_value(v) for v in data.values()]},
            schema={"Key": str, title: str},
        )
        st.dataframe(df)  # type: ignore
    elif isinstance(data, list):
        if data and isinstance(data[0], dict):
            # Flatten the list of dictionaries into a proper DataFrame
            df = pl.DataFrame(
                [
                    {k: format_value(v) for k, v in item.items()}
                    for item in data
                    if isinstance(item, dict)
                ]
            )
            st.dataframe(df)  # type: ignore
        else:
            df = pl.DataFrame(
                {title: [format_value(item) for item in data]}, schema={title: str}
            )
            st.dataframe(df)  # type: ignore
    else:
        df = pl.DataFrame({title: [format_value(data)]}, schema={title: str})
        st.dataframe(df)  # type: ignore


if "ai_report" in locals():
    with st.sidebar.expander("📊 AI Market Analysis", expanded=False):
        if not ai_report:
            st.warning("No AI report found for this date.")
        else:
            # Display Text Summary as a paragraph
            if "summary" in ai_report:
                st.subheader("Summary")
                st.write(ai_report["summary"])  # type: ignore

            # Display other sections as tables
            for key, value in ai_report.items():
                if key != "summary":  # Skip text summary for table rendering
                    display_table(key.replace("_", " ").title(), value)
else:
    st.warning("No AI report found for this date.")

# Build daily/cumulative data
df_chart = build_graduated_tokens_data()

# Convert to Pandas for Altair
df_chart_pd = df_chart.to_pandas()

# Create a bar chart for daily counts
bars = (
    alt.Chart(df_chart_pd)  # type: ignore
    .mark_bar(color="steelblue")
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("daily_count:Q", title="Daily Graduated Tokens"),
    )
)

# Create a line chart for the cumulative counts
line = (
    alt.Chart(df_chart_pd)# type: ignore
    .mark_line(color="red")
    .encode(
        x="date:T",
        y=alt.Y("cumulative_count:Q", title="Cumulative Graduated Tokens"),
    )
)

# Layer the bar and line charts together, using independent y-scales
combined_chart = (
    alt.layer(bars, line)# type: ignore
    .resolve_scale(y="independent")
    .properties(width="container", height=400)
)

st.subheader("Daily & Cumulative Graduated Tokens")
st.altair_chart(combined_chart, use_container_width=True)
