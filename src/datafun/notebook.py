# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "altair",
#     "marimo",
#     "pandas",
# ]
# ///
"""src/datafun/notebook.py - Reactive SQL explorer.

Author: Denise Case
Date: 2026-08

REQUIREMENTS:

1. Add marimo to notebooks in pyproject.toml.
2. Install the required dependencies using **uv sync**.

RUN:

Open this project folder in VS Code.
Open an integrated Terminal in the root project folder
and paste the following command.

uv run marimo run src/datafun/notebook.py

EDIT:

uv run marimo edit src/datafun/notebook.py

DOMAIN:

A small business with regions, stores, and employees.

The data is stored in three related tables.

One region can have many stores.
One store can have many employees.

EXPLORE:

Use the dropdown to select a region.

Python passes the selected value to SQL as a bound parameter.
SQL joins the related tables and returns one row per store.

The SQL query result is returned as a pandas DataFrame.
Python then visualizes the result.

Change the selected region and Marimo automatically
updates the query result and chart.

NO LOGGING:

In this notebook, we do not configure logging because a browser-based
WASM app has no persistent Python server to store log files.

FIRST: IMPORT AND APP SETUP (ALWAYS)

THEN: PLAN CELLS FIRST - I want these cells:

1. opening Markdown
2. load (related) data
3. create database for SQL
4. choose a selected region
5. run a parameterized SQL query
6. show selection
7. show df table and chart result

Note: No need to call @app.cell functions in marimo,
it triggers them automagically.
I could name them all "_", but I choose to
give them internal function names starting with "_"
so I can organize my thinking and my app.
"""

# === 0: DECLARE IMPORTS AND CREATE APP ===

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


with app.setup:
    from pathlib import Path
    import sqlite3
    import sys

    import altair as alt
    import marimo as mo
    import pandas as pd

    notebook_location = mo.notebook_location()
    if notebook_location is None:
        raise RuntimeError("Unable to determine notebook location.")

    NOTEBOOK_LOCATION = Path(notebook_location)

    DATA_DIR = NOTEBOOK_LOCATION.parents[1] / "data" / "retail"
    PUBLIC_DIR = NOTEBOOK_LOCATION / "public"

    REGION_FILENAME = "region.csv"
    STORE_FILENAME = "store.csv"
    EMPLOYEE_FILENAME = "employee.csv"

    def load_csv_for_notebook(
        *,
        local_path: Path,
        public_path: Path,
    ) -> pd.DataFrame:
        """Load a CSV locally or in a deployed WASM app."""
        if sys.platform == "emscripten":
            from pyodide.http import open_url

            return pd.read_csv(open_url(str(public_path)))

        if not local_path.is_file():
            raise FileNotFoundError(f"Required data file not found: {local_path}")

        return pd.read_csv(local_path)


@app.cell
def _title():
    # === INTRODUCE THE EXPLORER ===

    mo.md(r"""
    # Reactive Related Data Analysis

    Explore related data interactively.
    The data has two one-to-many relationships: **region:store:employee.**
    How to use: Choose a region.
    SQL will join the related tables andreturn the result to Python.
    | [Project Source](https://github.com/denisecase/datafun-05-sql/blob/main/src/datafun/notebook.py)
    | [Project Docs](https://denisecase.github.io/datafun-05-sql/)
    ---
    """)
    return


@app.cell
def _load_data():
    # === LOAD THE RELATED DATA ===

    # When running as a browser-based WASM app,
    # read the CSV files from the public folder.
    #
    # When running locally,
    # read the CSV files from data/retail.

    regions_df = load_csv_for_notebook(
        local_path=DATA_DIR / REGION_FILENAME,
        public_path=PUBLIC_DIR / REGION_FILENAME,
    )

    stores_df = load_csv_for_notebook(
        local_path=DATA_DIR / STORE_FILENAME,
        public_path=PUBLIC_DIR / STORE_FILENAME,
    )

    employees_df = load_csv_for_notebook(
        local_path=DATA_DIR / EMPLOYEE_FILENAME,
        public_path=PUBLIC_DIR / EMPLOYEE_FILENAME,
    )

    # Return the dataframes in the order expected by the next cell.
    return employees_df, regions_df, stores_df


@app.cell
def _create_database(employees_df, regions_df, stores_df):
    # === CREATE AN IN-MEMORY SQLITE DATABASE ===

    connection = sqlite3.connect(":memory:")

    regions_df.to_sql(
        "regions",
        connection,
        if_exists="replace",
        index=False,
    )

    stores_df.to_sql(
        "stores",
        connection,
        if_exists="replace",
        index=False,
    )

    employees_df.to_sql(
        "employees",
        connection,
        if_exists="replace",
        index=False,
    )

    # Last value returned is the number of records in the last table.
    # Instead, show a message using mo.md() in Markdown for this cell.

    mo.md("Database connected and tables loaded.")

    # Return the connection as a one-element tuple
    # to make it available to other cells.
    return (connection,)


@app.cell
def _choose_region(regions_df):
    # === CHOOSE A REGION ===

    region_names = sorted(regions_df["region_name"].tolist())

    region_dropdown = mo.ui.dropdown(
        options=region_names,
        value=region_names[0],
        label="Choose a region",
    )

    # Display it.
    region_dropdown

    # Return it as a tuple.
    return (region_dropdown,)


@app.cell
def _run_query(connection, region_dropdown):
    # === RUN A PARAMETERIZED SQL QUERY ===

    sql_query = """
    SELECT
        r.region_name,
        s.store_name,
        COUNT(e.employee_id) AS employee_count
    FROM regions AS r
    JOIN stores AS s
        ON r.region_id = s.region_id
    LEFT JOIN employees AS e
        ON s.store_id = e.store_id
    WHERE r.region_name = ?
    GROUP BY
        r.region_name,
        s.store_name
    ORDER BY
        employee_count DESC;
    """

    # The question mark is a placeholder.
    # The selected region is passed separately
    # to SQLite as a bound parameter.

    result_df = pd.read_sql_query(
        sql_query,
        connection,
        params=[region_dropdown.value],
    )

    # Return the result dataframe and the SQL query for inspection.
    return result_df, sql_query


@app.cell
def _show_selection(region_dropdown):
    # === USE MARKDOWN TO SHOW THE CURRENT ANALYTICAL CHOICE ===

    mo.md(
        f"""
        ## Employees by Store

        Selected region: **{region_dropdown.value}**
        (passed to SQL as a bound parameter).
        """
    )


@app.cell
def _show_df_table_and_chart(region_dropdown, result_df):
    # === DISPLAY THE SQL QUERY RESULT ===

    # Display the result dataframe and chart
    # side by side (in a horizontal hstack).

    employee_chart = (
        alt.Chart(result_df)
        .mark_bar()
        .encode(  # ty: ignore[unresolved-attribute]
            x=alt.X("store_name:N", title="Store", sort="-y"),
            y=alt.Y("employee_count:Q", title="Number of Employees"),
        )
        .properties(
            title=f"Employees by Store - {region_dropdown.value}",
            width="container",
        )
    )

    # Display vertical (stacked) layout of a list of items.
    # first the df table, then the chart.
    mo.vstack(
        [
            result_df,
            employee_chart,
        ]
    )


if __name__ == "__main__":
    app.run()
