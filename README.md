# Cairn — Planning Area Intelligence Agent

**Parent project:** [Singapore Dementia Burden Analysis](https://github.com/clairvyn/singapore-dementia-analysis-)  
**Live dashboard:** [singapore-dementia-analysis.streamlit.app](https://singapore-dementia-analysis.streamlit.app)  
**Status:** Pre-build — architecture decided, implementation in progress

\---

## What This Is

The Singapore Dementia Burden Analysis mapped where the estimated burden of dementia care falls across Singapore's 55 planning areas. It answered: *where should planners look?*

Cairn answers the next question: *when you look at a planning area, what should you think about?*

Cairn is a planning area intelligence agent. Given a planning area name, it:

1. Retrieves structured burden data from the Singapore Dementia Burden Analysis
2. Searches for recent AIC and MOH policy and funding context via Tavily
3. Synthesises both into a structured one-page operational brief

The brief is designed for anyone making decisions about where to focus home care resources — operators, strategists, planners.

\---

## The Output

Every query produces a four-section brief:

|Section|Content|Source|
|-|-|-|
|**Burden Snapshot**|Estimated PWDs, facility count, PWDs-per-facility ratio, national comparison|Structured data — SQLite|
|**Formal Care Presence**|Facility names, classification (VWO/Public vs Private), geographic notes|Structured data — SQLite|
|**Policy Context**|Recent AIC/MOH announcements, funding changes, relevant programmes|Tavily web search, synthesised by Claude|
|**Operational Considerations**|Claude's reasoning, with explicit citations to the specific data or policy item triggering each point|Claude synthesis — every recommendation anchored to a named source|

The citation requirement in Operational Considerations is enforced through the system prompt, not post-processing. Unanchored recommendations are not acceptable output.

\---

## Architecture

Cairn uses the Claude API tool use framework directly — two structured tools, one system prompt, one synthesis step.

```
User query (planning area name)
        │
        ├── Tool 1: SQLite lookup → burden stats, facility data
        │
        └── Tool 2: Tavily search → recent AIC/MOH context
                │
                └── Claude synthesis → four-section brief
```

**Why this architecture:**

* **Tool use over chat wrapping.** Structured tool schemas give explicit, auditable retrieval. The agent knows what it retrieved and why — that traceability matters when the output is used for operational decisions.
* **SQLite over CSV querying.** The schema is designed for a three-agent system from day one, with columns reserved for future agents that Cairn does not yet use. Migration cost is low; rebuilding the schema later would not be.
* **Tavily over Claude's built-in search.** Explicit, controllable search calls that transfer cleanly to future agents. The pattern is consistent across the system.
* **LangGraph deferred.** The complexity is not justified here. LangGraph is reserved for the SGX REIT agent where graph-based logic earns its place.

\---

## Null-State Handling

Two edge cases are encoded in the system prompt, not left to Claude's defaults:

* **Zero-facility areas** (e.g. Bukit Timah, est. 2,215 PWDs, zero facilities): The agent acknowledges the absence explicitly in Section 2 and frames Section 4 around the implications of no formal infrastructure, rather than treating it as an ordinary case.
* **Zero Tavily results**: Section 3 states explicitly that no area-specific results were found and offers only national-level context, clearly labelled as such. Claude does not generalise from national policy to imply area-specific activity.

Bukit Timah is one of the five test areas precisely because it triggers both null states simultaneously.

\---

## Data Sources

|Dataset|Description|Date|
|-|-|-|
|SingStat June 2024|Resident population by planning area and 5-year age band|June 2024|
|WiSE 2023 prevalence rates|Singapore-specific dementia prevalence by age band (60–74: 3.0%, 75–84: 18.2%, 85+: 48.6%)|2023|
|AIC service locator snapshot|148 formal dementia care facilities geocoded to planning areas|12 March 2026|
|URA Master Plan 2019 GeoJSON|Planning area boundary definitions|2019|

All data is a point-in-time snapshot. Snapshot dates are disclosed in every brief output. Refresh is event-triggered, not time-based.

\---

## The Five Test Areas

|Planning Area|Est. PWDs|Facilities|Ratio|Why included|
|-|-|-|-|-|
|Marine Parade|1,573|1|1,573:1|Highest strain ratio in Singapore. The headline finding of the parent project.|
|Bedok|8,197|12|683:1|The contrast case. Adjacent to Marine Parade. The comparison is the analytical argument made visible.|
|Bukit Timah|2,215|0|—|Zero-facility, significant burden. Tests both null states.|
|Choa Chu Kang|3,036|3|1,012:1|Large HDB suburban estate. Representative of the actual operational environment.|
|Queenstown|3,591|4|898:1|Mid-range ratio, mature estate. Tests that the agent works for ordinary cases, not just extremes.|

\---

## The Larger System

Cairn Phase 1 is the first interface on a proprietary knowledge base for Singapore's eldercare landscape. The system is designed for three agents:

|Phase|Agent|Example query|What it does|
|-|-|-|-|
|**Now**|Location intelligence (Cairn)|*Tell me about Marine Parade*|Burden stats + policy context → structured brief|
|Next|Policy intelligence|*What has MOH said about home care funding in the last 18 months?*|Policy document corpus → synthesised operator guidance|
|Later|Connected intelligence|*Given this policy change, which planning areas are most affected?*|Cross-agent reasoning across location + policy layers|

The SQLite schema includes columns reserved for Agent 2 (`policy\_tags`, `document\_ids`) that Cairn does not use but that the next agent will populate. These are architectural placeholders, not retrofits.

\---

## Repo Structure

```
cairn/
├── agent/
│   ├── agent.py          # Main agent loop — tool orchestration and Claude synthesis
│   ├── tools.py          # Tool 1: SQLite lookup. Tool 2: Tavily search. Tool schemas.
│   └── prompts.py        # System prompt and brief format definition
├── data/
│   └── cairn.db          # SQLite database (not committed — load from source CSV)
├── docs/
│   └── PRD.md            # Full product requirements document
├── tests/
│   └── test\_agent.py     # Brief validation across five test areas
├── app.py                # Streamlit wrapper (Phase 2)
├── load\_data.py          # One-time migration: dementia CSV → SQLite
├── requirements.txt
├── .env.example
└── README.md
```

\---

## Stack

|Layer|Choice|Rationale|
|-|-|-|
|AI|Claude API (tool use)|Structured tool schemas, not chat wrapping. Explicit, auditable retrieval.|
|Web search|Tavily|Purpose-built for agentic retrieval. Controllable and transferable across agents.|
|Data|SQLite via `sqlite3`|Schema designed for three-agent extensibility from day one.|
|UI|Streamlit (Phase 2)|Consistent with parent project. Deployable and shareable via URL.|
|Language|Python|Consistent with the dementia analysis pipeline. Lowest friction extension.|

\---

## Setup

```bash
git clone https://github.com/jermaice/cairn.git
cd cairn
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your keys:

```
ANTHROPIC\_API\_KEY=your\_key\_here
TAVILY\_API\_KEY=your\_key\_here
```

Load the data (one-time):

```bash
python load\_data.py
```

Run the agent:

```bash
python -m agent.agent "Marine Parade"
```

\---

## Limitations and Honest Caveats

This agent inherits the limitations of its parent dataset. The most important:

* **FDW informal care is invisible.** Roughly 50% of dementia caregiving households in Singapore employ a foreign domestic worker as primary caregiver. These do not appear in the AIC data. A planning area with zero formal facilities may have substantial informal care coverage.
* **Capacity is unknown.** Facility presence is used as a locational proxy, not a capacity measure. Two areas with the same facility count may have very different effective coverage.
* **Tavily results are not verified.** Policy context retrieved via web search is synthesised by Claude but not independently fact-checked. The brief discloses retrieval dates.

\---

## Related Work

* [Singapore Dementia Burden Analysis](https://github.com/clairvyn/singapore-dementia-analysis-) — the parent project that produced the burden data Cairn queries
* SGX REIT Intelligence Agent *(in development)* — LangGraph-based agent extracting structured metrics from REIT PDF disclosures

