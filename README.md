# Area Intelligence Agent

A planning area intelligence tool built on the Singapore Dementia Burden 
Analysis. Given a Singapore planning area name, the agent retrieves structured 
dementia burden data and synthesises a four-section operational brief covering 
demand, care infrastructure, policy context, and operational implications.

The Streamlit interface is deployed as part of the Singapore Dementia Burden 
Analysis app. Active development lives in that repo. This repo is the source 
archive for the agent logic.

- **Live app:** [singapore-dementia-analysis.streamlit.app](https://singapore-dementia-analysis.streamlit.app)  
- **Active repo:** [jermaice/singapore-dementia-analysis](https://github.com/jermaice/singapore-dementia-analysis)

---

## What this agent does

The agent receives a planning area name, executes two tool calls in sequence — 
a structured SQLite lookup for dementia burden data, and a Tavily web search 
for recent AIC/MOH policy context — and synthesises both into a one-page brief 
with four sections:

| Section | Content |
|---|---|
| Demand Snapshot | Estimated PWDs, facility count, PWDs-per-facility ratio, national comparison |
| Care Infrastructure | Facility names, geographic spread, co-location notes |
| Policy Context | Recent AIC/MOH policy and funding context for the area |
| Operational Implications | Synthesis and recommendations, each anchored to a named source |

The citation requirement in Operational Implications is enforced via the system 
prompt — every recommendation must name the specific data point or policy item 
that triggered it.

The agent logic is organised across four files in `agent/`: `agent.py` runs the 
agentic loop, `tools.py` holds the tool schemas and dispatch logic, `prompts.py` 
contains the system prompt encoding brief format and citation requirements, and 
`load_data.py` is a one-time script that builds the SQLite database from the 
source CSVs. Full product requirements are in `docs/PRD.md`.

This is a Phase 1 build designed as the first component of a three-agent system. 
The SQLite schema includes Agent 2-ready placeholder columns (`policy_tags`, 
`document_ids`) that the current agent does not populate but future agents will.

---

## Coverage and validation

The agent covers all 55 Singapore planning areas included in the dementia burden 
dataset. Five areas were used for structured validation, selected to represent 
the full range of demand and supply conditions:

| Planning Area | Est. PWDs | Facilities | Ratio |
|---|---|---|---|
| Marine Parade | 1,573 | 1 | 1,573:1 |
| Bedok | 8,197 | 12 | 683:1 |
| Bukit Timah | 2,215 | 0 | null (zero-facility test) |
| Choa Chu Kang | 3,036 | 3 | 1,012:1 |
| Queenstown | 3,591 | 4 | 898:1 |

---

## Running locally

1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file using `.env.example` as a template — add your 
   Anthropic and Tavily API keys
4. Run `python agent/load_data.py` to generate the SQLite database from 
   the source CSVs
5. Test the agent: `python run.py "Marine Parade"`

The SQLite database is generated locally and is not committed to this repo.

---

## Build sequence

1. Tool schemas defined before any code was written
2. System prompt written encoding brief format and citation requirement
3. SQLite database loaded from dementia burden CSVs with full schema
4. Agent loop and tool dispatch wired
5. Validated across five test areas in terminal output
6. Streamlit wrapper built in the active repo (see link above)
