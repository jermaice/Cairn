# Cairn — Product Requirements Document

**Version:** 1.1  
**Status:** Pre-build — decisions locked, ready to build  
**Date:** April 2026  
**Author:** C  
**Parent project:** Singapore Dementia Burden Analysis (complete, deployed)  
**Build approach:** Claude API tool use — Python, Streamlit, SQLite, Tavily  
**Scope:** Phase 1 of a three-agent eldercare intelligence system

---

## 1. Vision

The Singapore Dementia Burden Analysis mapped where the estimated burden of dementia care falls across Singapore's planning areas. It answered the question: where should planners look?

Cairn answers the next question: when you look at a planning area, what should you think about?

Cairn is a planning area intelligence agent. Given a planning area name, it retrieves structured burden data from the dementia analysis, retrieves recent policy and funding context from AIC and MOH, and synthesises both into a structured one-page operational brief. The brief is designed for a home care operator or strategy team making decisions about where to focus resources and attention.

**The narrative: analysis to action.**

The dementia project showed where the burden is. Cairn makes the map ask-able. That translation — from mapped insight to operational query — is the core value of this build.

---

## 2. The Larger System

Cairn Phase 1 is not a standalone demo. It is the first interface on a proprietary knowledge base for Singapore's eldercare landscape — a system that compounds with every document and data layer added.

### The three-agent architecture

| Phase | Agent type | Example query | What it does |
|---|---|---|---|
| **Agent 1 — NOW** | Location intelligence | *Tell me about Marine Parade* | Burden stats + policy context → structured brief |
| Agent 2 — NEXT | Policy intelligence | *What has MOH said about home care funding in the last 18 months?* | Policy document corpus → synthesised operator guidance |
| Agent 3 — LATER | Connected intelligence | *Given this policy change, which planning areas are most affected?* | Cross-agent reasoning across location + policy layers |

The knowledge base underpinning all three agents will eventually contain: dementia burden data (already built), AIC and MOH policy documents and circulars, parliamentary speeches and Q&A on eldercare, academic research on Singapore-specific care models, and funding scheme documentation.

Build the knowledge base with the full three-agent system in mind from day one. The schema and retrieval architecture must not require rebuilding when Agent 2 is added.

### Agent 2 readiness and the feedback loop

The SQLite schema (see Section 4) includes columns explicitly reserved for Agent 2 — `policy_tags` and `document_ids` — that Agent 1 does not use but that Agent 2 will populate. These are placeholders in the schema from day one, not retrofits.

As Agent 1 is used, queries the agent cannot fully answer should be logged informally as 'unmet query' notes. This log becomes the input specification for Agent 2: it tells you which gaps in the knowledge base are actually felt by the user, rather than gaps assumed in advance.

*LangGraph is explicitly deferred. The complexity does not justify it for this build. The correct tool is the Claude API tool use framework directly. LangGraph is reserved for the SGX REIT agent where graph logic earns its place.*

---

## 3. What Cairn Does — User Perspective

From the user's perspective, Cairn is simple:

- Type a planning area name (e.g. `Marine Parade`)
- Click a button (Streamlit) or run a command (terminal)
- Wait approximately 15–30 seconds
- Receive a structured one-page brief

Everything else — the database lookup, the web search, the synthesis — is invisible.

### The output brief — four sections

| Section | Content | Data source |
|---|---|---|
| **1. Burden Snapshot** | Estimated PWDs, facility count, PWDs-per-facility ratio, national comparison | Structured data from SQLite |
| **2. Formal Care Presence** | Facility names, classification (VWO/Public vs Private), geographic spread, co-location notes | Structured data from SQLite |
| **3. Policy Context** | Recent AIC/MOH announcements, funding changes, relevant programmes — or explicit statement that no area-specific results were found | Tavily web search, synthesised by Claude |
| **4. Operational Considerations** | Claude's reasoning, with explicit citations to the specific burden data or policy item that triggered each recommendation | Claude synthesis — every recommendation anchored to a named source |

### Citation requirement — Operational Considerations

The Operational Considerations section is Claude's reasoning layer, not a retrieval of facts. Every recommendation must be explicitly anchored to a named source within the brief. The system prompt will require Claude to cite the specific data point or policy item that triggered each operational recommendation.

Acceptable citation forms: *'Given the 1,573:1 PWD-per-facility ratio in Marine Parade...'* or *'Following the AIC announcement on home care subsidies (retrieved [date])...'* Unanchored recommendations are not acceptable output.

This requirement is enforced through the system prompt, not through post-processing. A brief that contains unanchored operational recommendations indicates a system prompt that needs tightening, not a data problem.

### Facility classification

Section 2 will classify facilities as VWO/Public or Private where data permits. This distinction is operationally meaningful: a VWO facility in the same planning area is a potential partner; a private operator is a potential competitor. Classification is stored in SQLite and surfaced in the brief without further inference by Claude.

---

## 4. Architecture

### How it works — the invisible flow

When the user submits a planning area name, the following happens in sequence:

1. **Tool 1 fires:** the agent queries SQLite for all burden statistics associated with that planning area — estimated PWDs, facility count, ratio, facility names, classification, and snapshot dates
2. **Tool 2 fires:** the agent calls Tavily with a query targeting recent AIC/MOH news and policy changes relevant to home care or dementia in Singapore
3. Both tool results are passed to Claude as structured context
4. Claude synthesises the data and search results into the four-section brief, with citations required in Operational Considerations
5. The brief is returned to the user — terminal output in Phase 1, Streamlit interface once agent logic is validated

### Null-state logic

Two null states must be handled explicitly by the system prompt, not left to Claude's defaults:

- **Zero-facility areas** (e.g. Bukit Timah): Tool 1 returns a `facility_count` of 0. The system prompt must instruct Claude to acknowledge this explicitly in Section 2 and to frame Section 4 around the absence of formal infrastructure rather than treating the area as an ordinary case.
- **Zero Tavily results:** If Tool 2 returns no results specific to the queried planning area, the system prompt must instruct Claude to state this explicitly in Section 3 — *'No recent AIC/MOH announcements specific to [area] were found'* — and to offer only national-level context, clearly labelled as such. Claude must not generalise from national policy to imply area-specific activity.

*Bukit Timah is included in the five test areas precisely because it tests both null states simultaneously. If the agent handles Bukit Timah correctly, it handles every edge case.*

### Data freshness

The SQLite database for Phase 1 is a point-in-time snapshot: AIC facility data as of 12 March 2026, SingStat population data from June 2024, WiSE 2023 prevalence rates. This is disclosed in every brief output via the `snapshot_date` and `population_source_date` fields in the schema.

The refresh trigger is event-based, not time-based: when a new SingStat annual population release is published, or when AIC updates its service locator in a way that would materially change facility counts, the database should be reloaded.

### Architecture decisions

| Decision | Chosen | Rationale |
|---|---|---|
| Data layer | **SQLite** | More extensible than CSV querying. Schema designed for the full three-agent system from day one, including Agent 2-ready columns. |
| Web search tooling | **Tavily** | Purpose-built for agentic retrieval. Explicit, auditable search calls. The pattern transfers directly to Agent 2 and Agent 3. Claude's built-in search is less controllable and does not generalise cleanly. |
| AI framework | **Claude API tool use (direct)** | Genuinely agentic — structured tool schemas, not chat wrapping. LangGraph deferred: complexity not justified for this build. |
| Output surface (Phase 1) | **Terminal output** | Ship the agent logic and validate brief quality before building UI. Terminal first is the correct build sequence. |
| Output surface (Phase 2) | **Streamlit** | Consistent with the dementia project. Deployable, shareable via URL. Added after agent logic is validated. |
| Agent language | **Python** | Consistent with the existing dementia pipeline. Lowest friction for extending existing work. |

### SQLite schema

The schema defines the `planning_areas` table. Columns marked *Agent 2 ready* are populated as placeholders at load time and will be used when Agent 2 is built. They should not be removed or renamed.

| Column | Type | Agent scope | Purpose |
|---|---|---|---|
| `planning_area` | TEXT PRIMARY KEY | Agent 1 | Planning area name. Join key across all agents. |
| `estimated_pwds` | INTEGER | Agent 1 | Estimated persons with dementia. Core burden metric. |
| `facility_count` | INTEGER | Agent 1 | Number of formal dementia care facilities present. |
| `pwds_per_facility` | REAL | Agent 1 | Primary strain ratio. NULL where facility_count = 0. |
| `facility_names` | TEXT | Agent 1 | Comma-separated list of facility names in the planning area. |
| `facility_classification` | TEXT | Agent 1 + 2 | VWO/Public or Private. Enables partner vs competitor framing. |
| `snapshot_date` | TEXT | Agent 1 + 2 | Date of the AIC facility snapshot. Disclosed in every brief. |
| `population_source_date` | TEXT | Agent 1 + 2 | Date of the SingStat population data. June 2024 for Phase 1. |
| `policy_tags` | TEXT | **Agent 2 ready** | Comma-separated policy programme tags. Populated when Agent 2 is built. |
| `document_ids` | TEXT | **Agent 2 ready** | Foreign keys to a future `policy_documents` table. Placeholder for Agent 2. |
| `last_updated` | TEXT | All agents | Timestamp of last row update. Supports data freshness checks. |

---

## 5. Phase 1 Scope

### What Phase 1 delivers

- A working agent that produces a correct, useful brief for five specified planning areas
- SQLite database loaded from the existing dementia burden CSV, with the full schema including Agent 2-ready columns
- Two structured tool schemas: SQLite data lookup and Tavily web search
- A system prompt defining the agent's role, knowledge, brief format, citation requirements, and null-state handling
- Terminal output of the brief
- Clean, documented Python code suitable for a GitHub portfolio

### What Phase 1 explicitly does not include

- Coverage of all 55 planning areas — demo quality, not production
- A Streamlit UI — that is Phase 2
- Error handling for unrecognised planning area names — deferred
- Authentication or access control
- Agent memory across sessions
- Automated data refresh — point-in-time snapshot, event-triggered refresh

### The five test planning areas

| Planning Area | PWDs (est.) | Facilities | Ratio | Why included |
|---|---|---|---|---|
| **Marine Parade** | 1,573 | 1 | 1,573:1 | Highest ratio in Singapore. The headline finding of the dementia project. Non-negotiable inclusion. |
| **Bedok** | 8,197 | 12 | 683:1 | The contrast case. Adjacent to Marine Parade. The comparison is the analytical argument made visible. |
| **Bukit Timah** | 2,215 | 0 | No facility | Zero-facility, significant burden. Primary test for null-state logic. |
| **Choa Chu Kang** | 3,036 | 3 | 1,012:1 | Large HDB suburban estate. Representative of the actual operational environment. |
| **Queenstown** | 3,591 | 4 | 898:1 | Mid-range ratio, mature estate. Tests that the agent works for ordinary cases, not just extremes. |

*Jurong East (2,101 PWDs, 2 facilities, 1,050:1) is the runner-up for the fifth slot. Confirm final selection at build start against the full dataset.*

---

## 6. Build Sequence

Build in this order. Do not move to the next step until the current one is working.

**Step 1 — Define tool schemas**  
Write the two tool schemas before any code. Tool 1: SQLite data lookup. Tool 2: Tavily web search. Each schema defines the tool name, description, and input parameters. This is the architectural contract everything else is built around.

**Step 2 — Write the system prompt**  
Define what the agent knows, what it is doing, and what a good brief looks like. The system prompt must encode: the four-section brief format, the citation requirement for Operational Considerations, and the null-state handling rules for zero-facility areas and zero Tavily results. This is the most important single piece of the agent. Write it before wiring up the tools.

**Step 3 — Load SQLite from CSV**  
Migrate the existing dementia burden CSV into SQLite using the full schema defined in Section 4. Populate the `snapshot_date` and `population_source_date` fields. Leave Agent 2-ready columns as empty strings or NULL. Classify facilities as VWO/Public or Private where data permits.

**Step 4 — Wire tool calls and test**  
Connect Tool 1 against SQLite. Connect Tool 2 against Tavily. Test against Marine Parade and Bedok first — the contrast case is the fastest way to verify the agent is reasoning correctly. Then test Bukit Timah to validate null-state handling before proceeding.

**Step 5 — Validate across all five areas**  
Run the agent across all five test areas. Each brief should be useful and distinct. Check that: Operational Considerations cite named sources, Section 3 explicitly states when no area-specific Tavily results were found, and Bukit Timah's brief handles the zero-facility state without hallucinating formal infrastructure.

**Step 6 — Streamlit wrapper**  
Once brief quality is validated in terminal, build the Streamlit interface. The agent logic does not change. The wrapper provides an input box, a button, and a formatted display of the four-section brief.

---

## 7. Skills Being Built

- Claude API with structured tool use — genuinely agentic, not chat wrapping. Tool schemas, tool results, multi-step reasoning.
- RAG architecture — designing a knowledge base that stays bounded in token cost as it scales. Context retrieved selectively per query, not loaded wholesale.
- SQLite schema design for extensibility — building the data layer for a three-agent system, with Agent 2-ready columns from day one.
- Tavily integration — explicit, auditable web search as an agentic tool call.
- System prompt engineering for agents — encoding behaviour, output format, citation requirements, and edge-case handling in the system prompt.

---

## 8. Open Questions

| Open question | Resolution trigger | Current thinking |
|---|---|---|
| **Fifth planning area (TBD)** | Resolve at build start | Jurong East (2,101 PWDs, 2 facilities, 1,050:1) is the runner-up. Confirm against final data. |
| **Streamlit wrapper build timing** | After agent logic validated | Build terminal output first. Streamlit added once brief quality confirmed across all five areas. |
| **Brief output format for Streamlit** | Decide at UI build stage | Structured sections with clear typography. May include a map pin for planning area location. |
| **Facility classification data** | At SQLite load step | Classify AIC facilities as VWO/Public or Private from available data. Partial classification acceptable for Phase 1. |

---

## 9. What the GitHub Viewer Should Think

- This person understands how to design an agentic system before building it — the architecture is deliberate, not assembled.
- This person knows why each decision was made — data layer, search tooling, framework — and can articulate the tradeoffs.
- This person builds on work they can defend — Cairn extends real, deployed analysis, not hypothetical data.
- This person thinks in systems — Phase 1 is explicitly scoped as the first agent in a three-agent architecture, with the knowledge base designed for all three from day one.
- This person has thought about failure modes — null-state logic, citation requirements, and data freshness are architectural requirements, not afterthoughts.

---

*Cairn — built on the Singapore Dementia Burden Analysis | April 2026*
