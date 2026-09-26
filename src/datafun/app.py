"""src/datafun/app.py - Project script.

Author: Julie Tietz
Date: 2026-09

HOW TO RUN THIS FILE:

From the VS Code menu (with only this project open in VS Code),
click "Terminal" / New Terminal to
open an integrated Terminal in the root project folder.
Paste the following command and press ENTER or RETURN
to run this file as a script:

uv run python -m datafun.app

DOMAIN:

A small business with regions, stores, and sales.

The data is stored in three related CSV files:

- one row per region
- one row per store
- one row per sale

One region can have many stores.
One store can have many sales.

EXPLORE:

Sometimes the information needed for an analysis
is stored in more than one related table.

SQL is especially useful when tables share keys
and we want to analyze information across them.

A simple Python and SQL process is:

1. LOAD the related tables.
2. INSPECT the grain and keys.
3. CREATE a SQLite database.
4. LOAD the tables into SQLite.
5. QUERY across related tables with SQL.
6. VISUALIZE the query result with Python.
7. SUMMARIZE what you found.
8. DISPLAY the visualization.

DESIGN:

Use this file to declare the data-specific choices
and the reasoning behind them,
then orchestrate the work.

SQLite comes from the Python Standard Library.
Pandas loads tabular data into SQLite
and returns SQL query results as DataFrames.
Reusable visualization functions come from eda-vizkit.

The SQL stays here because the query is an
analytical decision specific to this project.
"""

# === DECLARE IMPORTS (BRING IN FREE CODE) ===

import logging
from pathlib import Path
import sqlite3
from typing import Final

from datafun_toolkit.logger import get_logger, log_header, log_path
from eda_vizkit import save_chart
import matplotlib.pyplot as plt
import pandas as pd

# === CONFIGURE LOGGER ONCE FOR THE APPLICATION ===

LOG: logging.Logger = get_logger("P05", level="DEBUG")

# === DECLARE GLOBAL CONSTANTS ===

# Some global variables are CONSTANT.
# They do NOT change while the program runs.
# By convention, constants use UPPERCASE_WITH_UNDERSCORES.
# Final indicates that the value should not be reassigned.

# === LOCATE THE DATA FILES ===

DATA_DIR: Final[Path] = Path("data") / "retail"

REGION_FILE: Final[Path] = DATA_DIR / "region.csv"
STORE_FILE: Final[Path] = DATA_DIR / "store.csv"
SALE_FILE: Final[Path] = DATA_DIR / "sale.csv"

# === LOCATE THE SQLITE DATABASE ===

DATABASE_FILE: Final[Path] = DATA_DIR / "business.sqlite"

# === LOCATE THE CHART OUTPUT ===

CHART_DIR: Final[Path] = Path("docs") / "images"
CHART_PATH: Final[Path] = CHART_DIR / "sales-count-by-region.png"

# === DETERMINE WHAT ONE ROW REPRESENTS ===

REGION_GRAIN: Final[str] = "one business region"
STORE_GRAIN: Final[str] = "one store"
SALE_GRAIN: Final[str] = "one sale"

# === DESCRIBE THE TABLE RELATIONSHIPS ===

RELATIONSHIP_DECISION: Final[str] = r"""
The data is stored in three related tables.

One region can have many stores.
The stores table uses region_id to identify each store's region.

One store can have many sales.
The sales table uses store_id to identify each sale's store.

The shared keys connect information stored in different tables.
"""

# === DEFINE THE ANALYTICAL QUESTION ===

CUSTOM_QUERY_DECISION: Final[str] = r"""
I want to compare the number of sales in each region.
The result should have one row per region.

The information I need requires all three tables:
 - region name is in regions,
 - store name is in stores,
 - sales info is in sales.
"""

# === WRITE THE SQL QUERY ===

CUSTOM_SQL_QUERY: Final[str] = """
SELECT
    r.region_name,
    SUM(a.sale_amount) AS sales_count
FROM regions AS r
JOIN stores AS s
    ON r.region_id = s.region_id
LEFT JOIN sales AS a
    ON s.store_id = a.store_id
GROUP BY
    r.region_name
ORDER BY
    sales_count DESC;
"""

# === CHOOSE A VISUALIZATION ===

CUSTOM_CHART_DECISION: Final[str] = r"""
The query result has one numeric value
(sales count) for each region.

A bar chart works for comparing
a numeric value across named categories.

"""


# === DEFINE THE MAIN FUNCTION ===


def main() -> None:
    """Entry point when running this file as a Python script.

    This is where the instructions begin.

    Arguments: None.
    Returns: None.
    """
    log_header(LOG, "P05 - PYTHON AND SQL")

    LOG.info("===================================")
    LOG.info("START main()")
    LOG.info("===================================")

    LOG.info("-------------------------------")
    LOG.info("01. LOAD the related tables.")
    LOG.info("-------------------------------")

    log_path(LOG, "regions file", path=REGION_FILE)
    log_path(LOG, "stores file", path=STORE_FILE)
    log_path(LOG, "sales file", path=SALE_FILE)

    regions_df: pd.DataFrame = pd.read_csv(REGION_FILE)
    stores_df: pd.DataFrame = pd.read_csv(STORE_FILE)
    sales_df: pd.DataFrame = pd.read_csv(SALE_FILE)

    LOG.info("Related tables loaded successfully.")

    LOG.info("-------------------------------")
    LOG.info("02. INSPECT the grain and keys.")
    LOG.info("-------------------------------")

    LOG.info(f"Regions grain: {REGION_GRAIN}")
    LOG.info(f"Stores grain: {STORE_GRAIN}")
    LOG.info(f"Sales grain: {SALE_GRAIN}")

    LOG.info(f"Regions columns: {regions_df.columns.tolist()}")
    LOG.info(f"Stores columns: {stores_df.columns.tolist()}")
    LOG.info(f"Sales columns: {sales_df.columns.tolist()}")

    LOG.info(RELATIONSHIP_DECISION)

    LOG.info("-------------------------------")
    LOG.info("03. CREATE a SQLite database.")
    LOG.info("-------------------------------")

    log_path(LOG, "SQLite database", path=DATABASE_FILE)

    connection: sqlite3.Connection = sqlite3.connect(DATABASE_FILE)

    LOG.info("SQLite database connection created.")

    LOG.info("-------------------------------")
    LOG.info("04. LOAD the tables into SQLite.")
    LOG.info("-------------------------------")

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

    sales_df.to_sql(
        "sales",
        connection,
        if_exists="replace",
        index=False,
    )

    LOG.info("Related tables loaded into SQLite.")

    LOG.info("-------------------------------")
    LOG.info("05. QUERY across related tables with SQL.")
    LOG.info("-------------------------------")

    LOG.info(CUSTOM_QUERY_DECISION)
    LOG.info(f"\nSQL query:\n{CUSTOM_SQL_QUERY}")

    result_df: pd.DataFrame = pd.read_sql_query(
        CUSTOM_SQL_QUERY,
        connection,
    )

    LOG.info(f"\nQuery result:\n{result_df}")

    LOG.info("-------------------------------")
    LOG.info("06. VISUALIZE the query result with Python.")
    LOG.info("-------------------------------")

    LOG.info(CUSTOM_CHART_DECISION)

    sale_ax = result_df.plot.bar(
        x="region_name",
        y="sales_count",
        legend=False,
    )

    # CUSTOM: The analyst can customize the returned Matplotlib Axes object.
    sale_ax.set_title("Sales by Region")
    sale_ax.set_xlabel("Region")
    sale_ax.set_ylabel("Total Value of Sales")

    CHART_DIR.mkdir(parents=True, exist_ok=True)

    save_chart(
        sale_ax,
        CHART_PATH,
    )

    LOG.info(f"Chart saved successfully at {CHART_PATH}.")

    LOG.info("-------------------------------")
    LOG.info("07. SUMMARIZE what you found.")
    LOG.info("-------------------------------")

    # Run this app first.
    # Review the SQL result and visualization.
    # Then record your CUSTOM observations
    # in a simple multi-line raw string.

    LOG.info(r"""CUSTOM OBSERVATIONS:
    The SQL query connected information from
    the regions, stores, and sales tables.

    The result has one row per region.

    I observed that the total value of sales varies by region.

    """)

    LOG.info("-------------------------------")
    LOG.info("08. DISPLAY the visualization.")
    LOG.info("-------------------------------")

    LOG.info("In a script, call plt.show() at the end to display all charts.")
    LOG.info("Close all chart windows (with the close button) to continue.")

    plt.show()

    connection.close()

    LOG.info("===================================")
    LOG.info("END main() - Executed successfully!")
    LOG.info("===================================")


# === CONDITIONAL EXECUTION GUARD ===

# WHY: This is standard Python "boilerplate" - we copy and paste it
# into every Python script. It is a "conditional execution" guard,
# meaning: if this file is being run as a script, then execute the code
# in the main() function.

if __name__ == "__main__":
    main()
