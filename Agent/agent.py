"""
agent.py — Cairn agent loop

Accepts a planning area name, fires Tool 1 (SQLite burden data) and
Tool 2 (Tavily policy search) via the Claude API tool use framework,
and returns a completed four-section operational brief as a string.

The agentic loop follows the manual approach: each API call is inspected
for tool_use blocks, tools are executed via dispatch(), results are fed
back as tool_result messages, and the loop continues until Claude returns
stop_reason == "end_turn" (brief fully generated).
"""

import json
import os
import re
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup — ensures sibling imports (tools, prompts) work whether this
# module is imported by run.py at the project root or run directly.
# ---------------------------------------------------------------------------

_AGENT_DIR = Path(__file__).parent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from prompts import SYSTEM_PROMPT_V1
from tools import TOOL_SCHEMAS, dispatch

# ---------------------------------------------------------------------------
# Load environment variables from .env at project root
# ---------------------------------------------------------------------------

load_dotenv(dotenv_path=_AGENT_DIR.parent / ".env")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL = "claude-opus-4-5"

# max_tokens covers the full four-section brief; 8 192 is conservative headroom
# for even a verbose Queenstown or Bedok brief with many facility names.
MAX_TOKENS = 8192

# Safety cap on loop turns. Normal flow is three turns:
#   Turn 1 — Claude calls get_planning_area_burden()
#   Turn 2 — Claude calls search_eldercare_policy()
#   Turn 3 — Claude generates the brief (end_turn)
# Cap at 10 to surface unexpected loops without hanging indefinitely.
MAX_TURNS = 10


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

def generate_brief(planning_area: str) -> str:
    """
    Run the Cairn agentic loop and return a parsed four-section brief.

    Args:
        planning_area: Singapore planning area name, e.g. "Marine Parade".

    Returns:
        Dict with keys: burden_snapshot, formal_care_presence,
        policy_context, operational_considerations.

    Raises:
        EnvironmentError: If ANTHROPIC_API_KEY is missing from the environment.
        RuntimeError: If the loop exceeds MAX_TURNS without completing the brief.
    """

    # Step 1: Validate API key before making any calls
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file."
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Step 2: Build the initial user message.
    # Kept deliberately minimal — the system prompt governs format entirely.
    messages = [
        {
            "role": "user",
            "content": (
                f"Please produce a Cairn operational brief for the following "
                f"Singapore planning area: {planning_area}"
            ),
        }
    ]

    # Step 3: Agentic loop — iterate until the brief is complete or the
    # safety turn cap is reached.
    for turn in range(1, MAX_TURNS + 1):

        # Stream each API call for timeout safety; get_final_message() returns
        # the complete response once streaming is done. Streaming prevents HTTP
        # timeouts on the final turn when Claude generates the full brief.
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT_V1,
            tools=TOOL_SCHEMAS,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        # Step 4a: Brief is complete — extract and parse the text block.
        if response.stop_reason == "end_turn":
            brief_text = next(
                (block.text for block in response.content if block.type == "text"),
                "",
            )
            return _parse_brief(brief_text)

        # Step 4b: Claude has requested one or more tool calls.
        if response.stop_reason == "tool_use":

            # Append the full assistant response (including tool_use blocks)
            # to the message history. The API requires this before tool results
            # can be returned — omitting it causes a validation error.
            messages.append({"role": "assistant", "content": response.content})

            # Step 5: Execute each requested tool and collect the results.
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(
                        f"  [Tool call — turn {turn}] {block.name}",
                        flush=True,
                    )

                    # Dispatch to the appropriate function in tools.py.
                    result = dispatch(block.name, block.input)

                    # Tool result content must be a string. json.dumps with
                    # default=str safely serialises None, dates, and floats.
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,   # must match the tool_use id
                            "content": json.dumps(result, default=str),
                        }
                    )

            # Step 6: Return all tool results to Claude in a single user turn.
            messages.append({"role": "user", "content": tool_results})

    # Safety fallback — reached only if the loop cap fires unexpectedly.
    raise RuntimeError(
        f"Agent did not complete the brief within {MAX_TURNS} turns for "
        f"'{planning_area}'. Check that both tools are returning valid results."
    )


# ---------------------------------------------------------------------------
# Brief parser
# ---------------------------------------------------------------------------

def _parse_brief(brief_text: str) -> dict:
    """
    Split the raw brief string into its four named sections.

    The system prompt enforces these exact headers:
        ## SECTION 1: BURDEN SNAPSHOT
        ## SECTION 2: FORMAL CARE PRESENCE
        ## SECTION 3: POLICY CONTEXT
        ## SECTION 4: OPERATIONAL CONSIDERATIONS

    re.split() on this pattern produces five elements:
        [0]  text before the first header (discarded — should be empty)
        [1]  burden_snapshot content
        [2]  formal_care_presence content
        [3]  policy_context content
        [4]  operational_considerations content

    Raises:
        RuntimeError: If the brief does not contain exactly four sections.
    """
    # Match any of the four section headers; IGNORECASE for robustness
    pattern = r"##\s+SECTION\s+[1-4]:[^\n]*"
    parts = re.split(pattern, brief_text, flags=re.IGNORECASE)

    if len(parts) != 5:
        raise RuntimeError(
            f"Brief parsing failed: expected 5 segments after splitting on "
            f"section headers, got {len(parts)}. "
            f"The model may have used unexpected header formatting. "
            f"Raw brief (first 500 chars): {brief_text[:500]!r}"
        )

    return {
        "burden_snapshot": parts[1].strip(),
        "formal_care_presence": parts[2].strip(),
        "policy_context": parts[3].strip(),
        "operational_considerations": parts[4].strip(),
    }
