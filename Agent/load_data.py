"""
load_data.py — Cairn data loader

Reads the two source CSVs, aggregates facility data by planning area,
joins to demand estimates, computes the PWD-to-facility strain ratio,
and writes the result to data/cairn.db as the `planning_areas` table.

Run from the project root:
    python Agent/load_data.py
"""

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths — resolved relative to project root regardless of working directory
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
DEMAND_CSV = PROJECT_ROOT / "data" / "demand_surface.csv"
FACILITIES_CSV = PROJECT_ROOT / "data" / "facilities_with_planning_area.csv"
DB_PATH = PROJECT_ROOT / "data" / "cairn.db"

# ---------------------------------------------------------------------------
# Data freshness constants — update these when source data is refreshed
# AIC facility snapshot: 12 March 2026
# SingStat population data: June 2024 (WiSE 2023 prevalence rates applied)
# ---------------------------------------------------------------------------

SNAPSHOT_DATE = "2026-03-12"
POPULATION_SOURCE_DATE = "2024-06"

# ---------------------------------------------------------------------------
# Step 1: Load source CSVs
# ---------------------------------------------------------------------------

print("Loading source CSVs...")

demand = pd.read_csv(DEMAND_CSV)
# Expected columns: PLN_AREA_N, pwd_estimate
print(f"  demand_surface.csv   — {len(demand)} rows")

facilities = pd.read_csv(FACILITIES_CSV)
# Expected columns: facility_id, facility_name, PLN_AREA_N, (others)
print(f"  facilities_with_planning_area.csv — {len(facilities)} rows")

# ---------------------------------------------------------------------------
# Step 2: Aggregate facilities by planning area
# Produces facility_count (integer) and facility_names (comma-separated str)
# ---------------------------------------------------------------------------

print("Aggregating facilities by planning area...")

facility_agg = (
    facilities
    .groupby("PLN_AREA_N", as_index=False)
    .agg(
        facility_count=("facility_name", "count"),
        facility_names=("facility_name", lambda names: ", ".join(sorted(names))),
    )
)

# ---------------------------------------------------------------------------
# Step 3: Left-join demand onto facility aggregation
# Using a left join so planning areas with zero facilities are preserved.
# After the merge, fill NaN facility counts (areas with no matching rows in
# the facility CSV) with 0, and fill facility_names NaN with empty string.
# ---------------------------------------------------------------------------

print("Joining demand data to facility aggregation...")

merged = demand.merge(facility_agg, on="PLN_AREA_N", how="left")
merged["facility_count"] = merged["facility_count"].fillna(0).astype(int)
merged["facility_names"] = merged["facility_names"].fillna("")

# ---------------------------------------------------------------------------
# Step 4: Compute PWD-to-facility ratio
# Null (None/NaN) where facility_count is 0 — no division by zero.
# ---------------------------------------------------------------------------

print("Computing PWD-to-facility ratio...")

merged["pwds_per_facility"] = merged.apply(
    lambda row: row["pwd_estimate"] / row["facility_count"]
    if row["facility_count"] > 0
    else None,
    axis=1,
)

# ---------------------------------------------------------------------------
# Step 5: Rename columns and add metadata / placeholder columns
# Column names match the schema defined in the PRD (Section 4) and
# queried by tools.py. Agent 2-ready columns are empty strings for now.
# ---------------------------------------------------------------------------

print("Structuring final table...")

output = pd.DataFrame(
    {
        "planning_area": merged["PLN_AREA_N"],
        "estimated_pwds": merged["pwd_estimate"].astype(int),
        "facility_count": merged["facility_count"],
        "pwds_per_facility": merged["pwds_per_facility"],
        "facility_names": merged["facility_names"],
        "facility_classification": "",       # to be classified at load step
        "snapshot_date": SNAPSHOT_DATE,
        "population_source_date": POPULATION_SOURCE_DATE,
        "policy_tags": "",                   # Agent 2 ready — do not remove
        "document_ids": "",                  # Agent 2 ready — do not remove
        "last_updated": date.today().isoformat(),
    }
)

# ---------------------------------------------------------------------------
# Step 6: Write to SQLite
# Drops and recreates the table on each run so the script is idempotent.
# ---------------------------------------------------------------------------

print(f"Writing to {DB_PATH}...")

conn = sqlite3.connect(DB_PATH)
try:
    output.to_sql("planning_areas", conn, if_exists="replace", index=False)
    conn.commit()
finally:
    conn.close()

# ---------------------------------------------------------------------------
# Step 7: Confirm load
# ---------------------------------------------------------------------------

print("\nLoad complete.")
print(f"  Rows written : {len(output)}")
print(f"  Columns      : {', '.join(output.columns.tolist())}")
print(f"  Database     : {DB_PATH}")
