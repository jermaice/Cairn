import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

# Resolve DB path relative to project root regardless of working directory
DB_PATH = Path(__file__).parent.parent / "data" / "cairn.db"

# ---------------------------------------------------------------------------
# Tool schemas — passed directly to the Claude API as the `tools` parameter
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "get_planning_area_burden",
        "description": (
            "Look up dementia burden and eldercare facility data for a Singapore "
            "planning area. Returns estimated persons with dementia (PWDs), facility "
            "count, facility names, the PWD-to-facility strain ratio, and data "
            "freshness dates. Returns a not-found message if the planning area is "
            "absent from the database. pwds_per_facility is null when facility_count "
            "is zero."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "planning_area": {
                    "type": "string",
                    "description": (
                        "The Singapore planning area name to query, e.g. "
                        "'Marine Parade', 'Bedok', 'Bukit Timah'."
                    ),
                }
            },
            "required": ["planning_area"],
        },
    },
    {
        "name": "search_eldercare_policy",
        "description": (
            "Search the web for recent Singapore eldercare policy, AIC or MOH "
            "announcements, home care funding changes, and dementia-related "
            "programmes. Returns a list of results each containing a title, URL, "
            "and content snippet."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search query targeting Singapore eldercare or dementia "
                        "policy, e.g. 'AIC home care funding 2025 Singapore'."
                    ),
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return. Defaults to 5.",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def get_planning_area_burden(planning_area: str) -> dict:
    """
    Query cairn.db for burden and facility data for the given planning area.

    Returns a dict with keys:
        planning_area, estimated_pwds, facility_count, facility_names,
        pwds_per_facility, snapshot_date, population_source_date

    Returns a dict with a single 'error' key if the area is not found.
    pwds_per_facility is None (null) when facility_count is 0.
    """
    if not DB_PATH.exists():
        return {"error": f"Database not found at {DB_PATH}. Run the data load script first."}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            """
            SELECT
                planning_area,
                estimated_pwds,
                facility_count,
                facility_names,
                pwds_per_facility,
                snapshot_date,
                population_source_date
            FROM planning_areas
            WHERE LOWER(planning_area) = LOWER(?)
            """,
            (planning_area.strip(),),
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        return {
            "error": (
                f"Planning area '{planning_area}' was not found in the database. "
                "Check the spelling or confirm the area is included in the Phase 1 dataset."
            )
        }

    facility_count = row["facility_count"]
    pwds_per_facility = row["pwds_per_facility"] if facility_count > 0 else None

    return {
        "planning_area": row["planning_area"],
        "estimated_pwds": row["estimated_pwds"],
        "facility_count": facility_count,
        "facility_names": row["facility_names"],
        "pwds_per_facility": pwds_per_facility,
        "snapshot_date": row["snapshot_date"],
        "population_source_date": row["population_source_date"],
    }


def search_eldercare_policy(query: str, num_results: int = 5) -> list[dict]:
    """
    Call the Tavily search API for recent Singapore eldercare policy results.

    Returns a list of dicts, each with keys: title, url, content.
    Returns a list with a single error dict if the API key is missing or the
    call fails.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return [{"error": "TAVILY_API_KEY is not set. Add it to your .env file."}]

    client = TavilyClient(api_key=api_key)

    response = client.search(
        query=query,
        max_results=num_results,
        search_depth="advanced",
        include_answer=False,
    )

    results = []
    for item in response.get("results", []):
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
        )

    return results


# ---------------------------------------------------------------------------
# Dispatcher — routes a tool_use block from the Claude API to the right fn
# ---------------------------------------------------------------------------

def dispatch(tool_name: str, tool_input: dict):
    """
    Execute the named tool with the given input dict.
    Called by agent.py when Claude returns a tool_use content block.
    """
    if tool_name == "get_planning_area_burden":
        return get_planning_area_burden(**tool_input)
    if tool_name == "search_eldercare_policy":
        return search_eldercare_policy(**tool_input)
    return {"error": f"Unknown tool: '{tool_name}'"}
