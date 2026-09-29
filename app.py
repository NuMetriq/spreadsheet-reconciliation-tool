import csv
import tempfile
from pathlib import Path
from zipfile import BadZipFile

import streamlit as st
from openpyxl.utils.exceptions import InvalidFileException

from src.reconcile import (
    parse_tolerance,
    read_table,
    reconcile,
    summarize_results,
    write_report,
)


def read_uploaded_table(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / f"uploaded{extension}"
        file_path.write_bytes(uploaded_file.getvalue())

        return read_table(file_path)


def create_report_bytes(results: list[dict[str, str]]) -> bytes:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "reconciliation.csv"
        write_report(results, output_path)

        return output_path.read_bytes()


st.set_page_config(
    page_title="Spreadsheet Reconciliation",
    layout="wide",
)

st.title("Spreadsheet Reconciliation")
st.write(
    "Compare two files to find matching records, changed values, "
    "and records missing from either file."
)

source_column, target_column = st.columns(2)

with source_column:
    source_file = st.file_uploader(
        "Source file",
        type=["csv", "xlsx"],
        key="source_upload",
    )

with target_column:
    target_file = st.file_uploader(
        "Target file",
        type=["csv", "xlsx"],
        key="target_upload",
    )

if source_file is None or target_file is None:
    st.info("Upload a source file and a target file to begin.")
    st.stop()

try:
    source_rows = read_uploaded_table(source_file)
    target_rows = read_uploaded_table(target_file)
except (ValueError, OSError, csv.Error, BadZipFile, InvalidFileException) as error:
    st.error(f"Could not read the files: {error}")
    st.stop()

source_preview, target_preview = st.columns(2)

with source_preview:
    st.subheader("Source preview")
    st.caption(f"{len(source_rows)} records")
    st.dataframe(source_rows[:5], hide_index=True)

with target_preview:
    st.subheader("Target preview")
    st.caption(f"{len(target_rows)} records")
    st.dataframe(target_rows[:5], hide_index=True)

if not source_rows or not target_rows:
    st.warning(
        "The interface currently requires at least one data record "
        "in each file."
    )
    st.stop()

source_headers = list(source_rows[0])
target_headers = set(target_rows[0])

common_columns = [
    column
    for column in source_headers
    if column in target_headers
]

if not common_columns:
    st.error("The files have no column names in common.")
    st.stop()

st.subheader("Comparison settings")
st.caption("Only columns present in both files are available.")

key_column = st.selectbox(
    "Record ID column",
    options=common_columns,
    help="Choose a column containing a unique, nonblank ID for each record.",
)

available_comparison_columns = [
    column
    for column in common_columns
    if column != key_column
]

comparison_columns = st.multiselect(
    "Columns to compare",
    options=available_comparison_columns,
    default=available_comparison_columns,
)

if not comparison_columns:
    st.info("Select at least one column to compare.")
    st.stop()

numeric_columns = st.multiselect(
    "Numeric columns",
    options=comparison_columns,
    help="Compare these columns as numbers rather than exact text.",
)

tolerance_text = st.text_input(
    "Numeric tolerance",
    value="0",
    disabled=not numeric_columns,
    help=(
        "Maximum absolute difference allowed for numeric columns. "
        "Use 0 for exact comparison or, for example, 0.01 for one cent."
    ),
)

if st.button("Reconcile", type="primary"):
    try:
        numeric_tolerance = parse_tolerance(
            tolerance_text if numeric_columns else "0"
        )

        results = reconcile(
            source_rows,
            target_rows,
            key_column=key_column,
            comparison_columns=comparison_columns,
            numeric_columns=numeric_columns,
            numeric_tolerance=numeric_tolerance,
        )
    except ValueError as error:
        st.error(f"Could not reconcile the files: {error}")
        st.stop()

    summary = summarize_results(results)

    st.subheader("Summary")
    st.write("Matched records:", summary["matched"])
    st.write("Changed records:", summary["changed"])
    st.write("Source-only records:", summary["source_only"])
    st.write("Target-only records:", summary["target_only"])

    st.subheader("Reconciliation results")
    st.caption(
        "Matched means the selected fields agree under your comparison "
        "rules. Changed records have one row per differing field."
    )
    st.dataframe(results, hide_index=True)
    
    try:
        report_bytes = create_report_bytes(results)
    except (ValueError, OSError, csv.Error) as error:
        st.error(f"Could not create the report: {error}")
        st.stop()

    st.download_button(
        "Download CSV report",
        data=report_bytes,
        file_name="reconciliation.csv",
        mime="text/csv",
        on_click="ignore",
    )