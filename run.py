"""
run.py — Cairn entry point

Thin CLI wrapper around the agent loop. Accepts a planning area name
as a command line argument, calls generate_brief(), and prints the
returned brief to the terminal.

Usage:
    python run.py "Marine Parade"
    python run.py "Bukit Timah"
    python run.py "Bedok"
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — add the Agent directory so that `from agent import` resolves
# correctly when run.py is called from the project root.
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).parent / "Agent"))

from agent import generate_brief


def main() -> None:
    """Parse CLI arguments, run the agent, and print the brief."""

    # Step 1: Validate that a planning area argument was supplied.
    if len(sys.argv) < 2:
        print("Usage:   python run.py \"Planning Area Name\"")
        print("Example: python run.py \"Marine Parade\"")
        sys.exit(1)

    # Step 2: Read the planning area from the first positional argument.
    # sys.argv[1] is the raw string — quoted or unquoted by the shell.
    planning_area = sys.argv[1].strip()

    if not planning_area:
        print("Error: planning area name cannot be empty.")
        sys.exit(1)

    # Step 3: Print a brief status header so the user knows work is in progress.
    # Tool call progress is printed inside agent.py as each tool fires.
    print(f"\nCairn — Planning Area Brief")
    print(f"Area: {planning_area}")
    print("-" * 60)

    # Step 4: Run the agent loop. This call blocks until the brief is complete.
    try:
        brief = generate_brief(planning_area)
    except EnvironmentError as e:
        print(f"\nConfiguration error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nAgent error: {e}")
        sys.exit(1)

    # Step 5: Print the completed brief.
    print()
    print(brief)
    print()


if __name__ == "__main__":
    main()
