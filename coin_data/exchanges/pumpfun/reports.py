import concurrent.futures
import glob
import json
import os
import re

import openai
import polars as pl

from coin_data.logging import logger

DATA_DIR = os.path.expanduser("~/pumpfun_data/")
TEMPLATE_PATH = "coin_data/report_template.md"
OUTPUT_DIR = os.path.expanduser("~/pumpfun_data/reports/")
MODEL_NAME = "gpt-4o-mini"
MAX_WORKERS = 8  # Adjust based on system resources

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(TEMPLATE_PATH, "r", encoding="utf-8") as file:
    REPORT_TEMPLATE = file.read()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def read_csv_to_markdown(csv_path: str) -> str:
    """
    Reads a CSV file using Polars and converts it into a Markdown table.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        str: CSV data formatted as a Markdown table.
    """
    df = pl.read_csv(csv_path)
    return df.to_pandas().to_markdown(index=False)


def clean_json_output(output: str) -> str:
    """
    Cleans up the AI-generated JSON output by removing Markdown code block formatting.

    Args:
        output (str): Raw AI response containing JSON.

    Returns:
        str: Cleaned JSON string.
    """
    # Remove all Markdown-style code block markers (```json, ```python, ```)
    output = re.sub(r"^```[\w\s]*\n?", "", output.strip())  # Remove leading ```
    output = re.sub(r"\n?```$", "", output.strip())  # Remove trailing ```

    # Trim whitespace and ensure valid JSON format
    return output.strip()


def generate_report(data_markdown: str, template: str) -> str | None:
    """
    Generates a market report using GPT-4o-mini.

    Args:
        data_markdown (str): CSV data formatted as a Markdown table.
        template (str): The report template with placeholders.

    Returns:
        str: Cleaned JSON output or None if an error occurs.
    """
    try:
        prompt = template.replace("{{DATA}}", data_markdown)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI that generates structured market analysis reports in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        raw_output = response.choices[0].message.content
        if not raw_output:
            logger.error("AI returned empty output.")
            return None

        return clean_json_output(raw_output)

    except openai.APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None


def process_csv_file(csv_file: str) -> dict[str, str]:
    """
    Processes a single CSV file and generates a cleaned market report in JSON format.

    Args:
        csv_file (str): Path to the CSV file.

    Returns:
        dict: Status of the processing and the generated report file path.
    """
    try:
        logger.info(f"Processing CSV file: {csv_file}")
        data_markdown = read_csv_to_markdown(csv_file)

        logger.info(f"Generating report for {csv_file}...")
        report_content = generate_report(data_markdown, REPORT_TEMPLATE)
        if not report_content:
            logger.error(f"Failed to generate report for {csv_file}.")
            return {
                "status": "error",
                "message": f"Failed to generate report for {csv_file}",
            }

        # Convert cleaned string to actual JSON for validation
        try:
            json_data = json.loads(report_content)  # Ensures it's valid JSON
        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON output for {csv_file}: {str(e)}\nRaw Output: {report_content}"
            )

            # Attempt to auto-repair simple JSON errors (if minor)
            try:
                fixed_content = report_content.replace("\n", "").replace("\t", "")
                json_data = json.loads(fixed_content)
                logger.warning(f"Auto-fixed minor JSON issue in {csv_file}")
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "AI returned invalid JSON format",
                }

        report_filename = (
            os.path.basename(csv_file)
            .replace("results_", "report_")
            .replace(".csv", ".json")
        )
        report_path = os.path.join(OUTPUT_DIR, report_filename)

        with open(report_path, "w", encoding="utf-8") as report_file:
            json.dump(
                json_data, report_file, indent=4
            )  # Save as properly formatted JSON

        logger.info(f"Report generated and saved to: {report_path}")
        return {"status": "success", "report_path": report_path}

    except Exception as e:
        logger.error(f"Error processing CSV file {csv_file}: {str(e)}")
        return {"status": "error", "message": str(e)}


def generate_reports() -> list[dict[str, str]]:
    """
    Processes all CSV files matching `results_*.csv` and generates reports using multithreading.

    Returns:
        list: A list of dictionaries containing report generation statuses.
    """
    csv_files = glob.glob(os.path.join(DATA_DIR, "results_*.csv"))

    if not csv_files:
        return [{"status": "error", "message": "No CSV files found."}]

    results: list[dict[str, str]] = []

    max_workers = min(MAX_WORKERS, (os.cpu_count() or 1) * 2)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_csv = {
            executor.submit(process_csv_file, csv): csv for csv in csv_files
        }

        for future in concurrent.futures.as_completed(future_to_csv):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error in report generation: {str(e)}")
                results.append({"status": "error", "message": str(e)})

    return results


def process_single_csv(csv_file: str) -> dict[str, str]:
    """
    Public API function to process a single CSV file.

    Args:
        csv_file (str): Path to the CSV file.

    Returns:
        dict: Status of the processing and the generated report file path.
    """
    if not os.path.exists(csv_file):
        return {"status": "error", "message": f"File not found: {csv_file}"}

    return process_csv_file(csv_file)


# Smoke test: Run this script standalone
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        logger.info(f"Processing single CSV file: {csv_file}")
        result = process_single_csv(csv_file)
        logger.info(result)
    else:
        logger.info("Starting market report generation...")
        results = generate_reports()
        if not results or (len(results) == 1 and results[0]["status"] == "error"):
            logger.info("No reports generated.")
        else:
            logger.info("Reports generated successfully:")
            for result in results:
                logger.info(result)

        logger.info("Done.")
