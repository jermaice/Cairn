\# Area Intelligence Agent



Planning Area Intelligence Agent — Product Requirements Document



| \*\*Status\*\* | Phase 1 complete — deployed |

| --- | --- |

| \*\*Version\*\* | 1.2 |

| \*\*Date\*\* | April 2026 |

| \*\*Author\*\* | Jermaice |

| \*\*Parent project\*\* | Singapore Dementia Burden Analysis (complete, deployed) |

| \*\*Build approach\*\* | Claude API tool use — Python, Streamlit, SQLite, Tavily |

| \*\*Scope\*\* | Phase 1 of a three-agent eldercare intelligence system |

| \*\*Live app\*\* | singapore-dementia-analysis.streamlit.app |

| \*\*Active repo\*\* | jermaice/singapore-dementia-analysis |

| \*\*Source archive\*\* | jermaice/area-intelligence-agent |



\---



\# 1. Vision



The Singapore Dementia Burden Analysis mapped where the estimated burden 

of dementia care falls across Singapore's planning areas. It answered the 

question: where should planners look?



The Area Intelligence Agent answers the next question: when you look at a 

planning area, what should you think about?



The agent is a planning area intelligence tool. Given a planning area name, 

it retrieves structured burden data from the dementia analysis, retrieves 

recent policy and funding context from AIC and MOH, and synthesises both 

into a structured one-page operational brief. The brief is designed for a 

home care operator or strategy team making decisions about where to focus 

resources and attention.



\*\*The narrative: analysis to action.\*\*



The dementia project showed where the burden is. The Area Intelligence Agent 

makes the map ask-able. That translation — from mapped insight to operational 

query — is the core value of this build.



\---



\# 2. The Larger System



Phase 1 is not a standalone tool. It is the first interface on a proprietary 

knowledge base for Singapore's eldercare landscape — a system that compounds 

with every document and data layer added.



\### The three-agent architecture



| \*\*Phase\*\* | \*\*Agent type\*\* | \*\*Example query\*\* | \*\*What it does\*\* |

| --- | --- | --- | --- |

| \*\*Agent 1 — COMPLETE\*\* | Location intelligence | Tell me about Marine Parade | Burden stats + policy context → structured brief |

| Agent 2 — NEXT | Policy intelligence | What has MOH said about home care funding in the last 18 months? | Policy document corpus → synthesised operator guidance |

| Agent 3 — LATER | Connected intelligence | Given this policy change, which planning areas are most affected? | Cross-agent reasoning across location + policy layers |



The knowledge base underpinning all three agents will eventually contain: 

dementia burden data (already built), AIC and MOH policy documents and 

circulars, parliamentary speeches and Q\&A on eldercare, academic research 

on Singapore-specific care models, and funding scheme documentation.



The schema and retrieval architecture were designed for the full three-agent 

system from day one and do not require rebuilding when Agent 2 is added.



\### Agent 2 readiness and the feedback loop



The SQLite schema includes columns explicitly reserved for Agent 2 — 

`policy\_tags` and `document\_ids` — that Agent 1 does not populate but 

Agent 2 will. These are placeholders in the schema from day one, not 

retrofits.



As Agent 1 is used, queries the agent cannot fully answer — areas where 

burden data is present but Tavily returns no relevant policy context, or 

where the operational implications are too generic to be useful — should 

be logged informally as unmet query notes. This log becomes the input 

specification for Agent 2: it tells you which gaps in the knowledge base 

are actually felt by the user, rather than gaps assumed in advance.



\*LangGraph is explicitly deferred. The complexity does not justify it for 

this build. The correct tool is the Claude API tool use framework directly. 

LangGraph is reserved for the SGX REIT agent where graph logic earns its 

place.\*



\---



\# 3. What the Agent Does — User Perspective



From the user's perspective, the interaction is simple:



\- Type a planning area name (e.g. 'Marine Parade')

\- Click a button

\- Wait approximately 15–30 seconds

\- Receive a structured one-page brief



Everything else — the database lookup, the web search, the synthesis — is 

invisible. The user interacts only with an input and an output.



\### The output brief — four sections



| \*\*Section\*\* | \*\*Content\*\* | \*\*Data source\*\* |

| --- | --- | --- |

| \*\*1. Demand Snapshot\*\* | Estimated PWDs, facility count, PWDs-per-facility ratio, national comparison | Structured data from SQLite |

| \*\*2. Care Infrastructure\*\* | Facility names, classification (VWO/Public vs Private), geographic spread, co-location notes | Structured data from SQLite |

| \*\*3. Policy Context\*\* | Recent AIC/MOH announcements, funding changes, relevant programmes — or explicit statement that no area-specific results were found | Tavily web search, synthesised by Claude |

| \*\*4. Operational Implications\*\* | Claude's reasoning, with explicit citations to the specific burden data or policy item that triggered each recommendation | Claude synthesis — every recommendation anchored to a named source |



\### Citation requirement — Operational Implications



The Operational Implications section is Claude's reasoning layer, not a 

retrieval of facts. To keep this credible to a practitioner audience, every 

recommendation must be explicitly anchored to a named source within the 

brief. The system prompt requires Claude to cite the specific data point or 

policy item that triggered each recommendation.



Acceptable citation forms: 'Given the 1,573:1 PWD-per-facility ratio in 

Marine Parade...' or 'Following the AIC announcement on home care subsidies 

(retrieved \[date])...' Unanchored recommendations are not acceptable output.



\*This requirement is enforced through the system prompt, not through 

post-processing. A brief that contains unanchored recommendations indicates 

a system prompt that needs tightening, not a data problem.\*



\### Facility classification



Section 2 (Care Infrastructure) classifies facilities in the planning area 

as VWO/Public or Private where data permits. This distinction is 

operationally meaningful: a VWO facility in the same planning area is a 

potential partner; a private operator is a potential competitor. The 

classification is stored in the SQLite schema and surfaced in the brief 

without further inference by Claude.



\*Note: facility\_classification is an empty string for all rows in the 

Phase 1 database. Classification is a known gap flagged for the next data 

update pass.\*



\---



\# 4. Architecture



\### How it works — the invisible flow



When the user submits a planning area name, the following happens in 

sequence:



\- Tool 1 fires: the agent queries SQLite for all burden statistics 

&#x20; associated with that planning area — estimated PWDs, facility count, 

&#x20; ratio, facility names, classification, and snapshot dates

\- Tool 2 fires: the agent calls Tavily with a dynamically constructed 

&#x20; query using the planning area name and Tool 1 results, targeting recent 

&#x20; AIC/MOH news and policy changes relevant to home care or dementia in 

&#x20; Singapore

\- Both tool results are passed to Claude as structured context

\- Claude synthesises the data and search results into the four-section 

&#x20; brief, with citations required in the Operational Implications section

\- The brief is returned to the user via the Streamlit interface



\### Null-state logic



Two null states are handled explicitly by the system prompt:



\- \*\*Zero-facility areas\*\* (e.g. Bukit Timah): Tool 1 returns a 

&#x20; facility\_count of 0. The system prompt instructs Claude to acknowledge 

&#x20; this explicitly in Section 2 and to frame Section 4 around the absence 

&#x20; of formal infrastructure rather than treating the area as an ordinary 

&#x20; case.

\- \*\*Zero Tavily results\*\*: If Tool 2 returns no results specific to the 

&#x20; queried planning area, the system prompt instructs Claude to state this 

&#x20; explicitly in Section 3 and to offer only national-level context, clearly 

&#x20; labelled as such. Claude does not generalise from national policy to imply 

&#x20; area-specific activity.



\*Bukit Timah was included in the validation set precisely because it tests 

both null states simultaneously: no facilities in the data layer, and likely 

no area-specific policy results from Tavily.\*



\### Data freshness



The SQLite database is a point-in-time snapshot: AIC facility data as of 

12 March 2026, SingStat population data from June 2024, WiSE 2023 prevalence 

rates. This is disclosed in every brief output via the snapshot\_date and 

population\_source\_date fields in the schema.



The refresh trigger is event-based, not time-based: when a new SingStat 

annual population release is published, or when AIC updates its service 

locator in a way that would materially change facility counts, the database 

should be reloaded. No automated sync is in place. The brief always includes 

the snapshot date so the reader can assess freshness themselves.



\### Architecture decisions



| \*\*Decision\*\* | \*\*Chosen\*\* | \*\*Rationale\*\* |

| --- | --- | --- |

| Data layer | SQLite | More extensible than CSV querying. Schema designed for the full three-agent system from day one, including Agent 2-ready columns. |

| Web search tooling | Tavily | Purpose-built for agentic retrieval. Explicit, auditable search calls. The pattern transfers directly to Agent 2 and Agent 3. |

| AI framework | Claude API tool use (direct) | Genuinely agentic — structured tool schemas, not chat wrapping. LangGraph deferred: complexity not justified for this build. |

| Output surface | Streamlit, deployed in active repo | Consistent with the dementia project. Deployable, shareable via URL. Built in jermaice/singapore-dementia-analysis after agent logic was validated in terminal. |

| Agent framework | Python | Consistent with the existing dementia pipeline. Lowest friction for extending existing work. |

| Repo architecture | Active development in jermaice/singapore-dementia-analysis; source archive in jermaice/area-intelligence-agent | Deployment simplicity won over repo purity. The live URL (singapore-dementia-analysis.streamlit.app) could not move. Active codebase follows the deployment. This decision is flagged for revisit when Agent 2 is built. |



\### SQLite schema



The schema defines the `planning\_areas` table. Columns marked Agent 2 ready 

are populated as placeholders at load time and will be used when Agent 2 is 

built. They should not be removed or renamed.



| \*\*Column\*\* | \*\*Type\*\* | \*\*Agent scope\*\* | \*\*Purpose\*\* |

| --- | --- | --- | --- |

| planning\_area | TEXT PRIMARY KEY | Agent 1 | Planning area name. Join key across all agents. |

| estimated\_pwds | INTEGER | Agent 1 | Estimated persons with dementia. Core burden metric. |

| facility\_count | INTEGER | Agent 1 | Number of formal dementia care facilities present. |

| pwds\_per\_facility | REAL | Agent 1 | Primary strain ratio. NULL where facility\_count = 0. |

| facility\_names | TEXT | Agent 1 | Comma-separated list of facility names in the planning area. |

| facility\_classification | TEXT | Agent 1 + 2 | VWO/Public or Private. Enables partner vs competitor framing in the brief. Empty string for all rows in Phase 1 — flagged for next data pass. |

| snapshot\_date | TEXT | Agent 1 + 2 | Date of the AIC facility snapshot. Used in the brief to flag data freshness. |

| population\_source\_date | TEXT | Agent 1 + 2 | Date of the SingStat population data used. June 2024 for Phase 1. |

| policy\_tags | TEXT | Agent 2 ready | Comma-separated policy programme tags (e.g. Healthier SG, CCMS). Populated when Agent 2 is built. |

| document\_ids | TEXT | Agent 2 ready | Foreign keys to a future policy\_documents table. Placeholder for Agent 2 document corpus. |

| last\_updated | TEXT | All agents | Timestamp of last row update. Supports data freshness checks. |



\*Agent 2 ready columns exist in the schema from day one. Agent 1 does not 

write to them; Agent 2 will.\*



\---



\# 5. Phase 1 Scope — What Was Delivered



\### Delivered



\- A working agent producing a correct, useful brief for all 55 Singapore 

&#x20; planning areas

\- SQLite database loaded from the dementia burden CSVs, with the full schema 

&#x20; including Agent 2-ready columns

\- Two structured tool schemas: SQLite data lookup and Tavily web search

\- A system prompt defining the agent's role, brief format, citation 

&#x20; requirements, and null-state handling

\- Streamlit interface deployed at singapore-dementia-analysis.streamlit.app 

&#x20; as the Area Intelligence Brief page



\### Explicitly out of scope for Phase 1 (unchanged)



\- Error handling for unrecognised planning area names — deferred

\- Authentication or access control

\- Agent memory across sessions

\- Automated data refresh — point-in-time snapshot, event-triggered refresh

\- Facility classification data — known gap, flagged for next data pass



\### Validation areas



Five planning areas were used for structured validation, selected to 

represent the full range of demand and supply conditions. The agent covers 

all 55 planning areas in the dataset.



| \*\*Planning Area\*\* | \*\*PWDs (est.)\*\* | \*\*Facilities\*\* | \*\*Ratio\*\* | \*\*Why included\*\* |

| --- | --- | --- | --- | --- |

| Marine Parade | 1,573 | 1 | 1,573:1 | Highest ratio in Singapore. The headline finding of the dementia project. |

| Bedok | 8,197 | 12 | 683:1 | The contrast case. Adjacent to Marine Parade. The comparison is the analytical argument made visible. |

| Bukit Timah | 2,215 | 0 | No facility | Zero-facility, significant burden. Tests both null states simultaneously. |

| Choa Chu Kang | 3,036 | 3 | 1,012:1 | Large HDB suburban estate. Representative of the operational environment home care services actually serve. |

| Queenstown | 3,591 | 4 | 898:1 | Mid-range ratio, mature estate. Tests that the agent works for ordinary cases, not just extremes. |



\---



\# 6. Build Sequence — As Executed



1\. Tool schemas defined before any code was written

2\. System prompt written encoding brief format, citation requirement, and 

&#x20;  null-state handling

3\. SQLite database loaded from dementia burden CSVs with full schema

4\. Agent loop and tool dispatch wired; tested against Marine Parade and 

&#x20;  Bedok first, then Bukit Timah for null-state validation

5\. Validated across all five areas in terminal output

6\. Streamlit wrapper built in jermaice/singapore-dementia-analysis and 

&#x20;  deployed



\---



\# 7. Skills Demonstrated



\- Claude API with structured tool use — genuinely agentic, not chat 

&#x20; wrapping. Tool schemas, tool results, multi-step reasoning.

\- RAG architecture — designing a knowledge base that stays bounded in token 

&#x20; cost as it scales. Context retrieved selectively per query, not loaded 

&#x20; wholesale.

\- SQLite schema design for extensibility — building the data layer for a 

&#x20; three-agent system, with Agent 2-ready columns from day one.

\- Tavily integration — explicit, auditable web search as an agentic tool 

&#x20; call, dynamically constructed per query.

\- System prompt engineering for agents — encoding behaviour, output format, 

&#x20; citation requirements, and edge-case handling.



\---



\# 8. Strategic Framing



\### The portfolio argument



The dementia project showed where the burden is. The Area Intelligence Agent 

makes the map ask-able. That translation — from mapped insight to operational 

query — is what a strategy or operations role requires: not just analysis, 

but the system that puts analysis in front of the people making decisions.



The real estate background is a strength to name explicitly. Location 

intelligence is what retailers and REITs use for site selection. The same 

pattern — burden surface, infrastructure overlay, operational brief — is 

being pointed at care gaps. That is cross-domain pattern recognition.



\### The compounding system argument



This is not a demo. It is the first interface on a proprietary knowledge 

layer for Singapore's ageing care sector that no off-the-shelf tool has — 

and it compounds with every document added. Not a one-off build, but a 

system with a clear architecture and a roadmap.



\### What the GitHub viewer should take away



\- This person understands how to design an agentic system before building 

&#x20; it — the architecture is deliberate, not assembled.

\- This person knows why each decision was made and can articulate the 

&#x20; tradeoffs.

\- This person builds on work they can defend — this extends real, deployed 

&#x20; analysis, not hypothetical data.

\- This person thinks in systems — Phase 1 is explicitly scoped as the first 

&#x20; agent in a three-agent architecture, with the knowledge base designed for 

&#x20; all three from day one.

\- This person has thought about failure modes — null-state logic, citation 

&#x20; requirements, and data freshness are architectural requirements, not 

&#x20; afterthoughts.



\---



\# 9. Decisions Log



| \*\*Question\*\* | \*\*Decision\*\* | \*\*Rationale\*\* |

| --- | --- | --- |

| Fifth validation planning area | Queenstown confirmed | Mid-range ratio, mature estate, tests ordinary cases. Jurong East was the runner-up. |

| Streamlit wrapper timing | Built after terminal validation | Agent logic validated first; wrapper added without changing agent code. |

| Streamlit wrapper location | Built in jermaice/singapore-dementia-analysis, not this repo | Deployment constraint — live URL could not move. Active codebase follows deployment. Flagged for revisit at Agent 2 build. |

| Brief output format | Card-style sections with CSS styling, session state persistence across pages | Native Streamlit pushed to its limits before custom injection; result is clean for portfolio deployment. |

| Facility classification | Left as empty string in Phase 1 | AIC source data does not cleanly distinguish VWO/Public vs Private. Flagged for next data pass. |

| cairn.db committed to DemP repo | Committed as deliberate exception | Streamlit Cloud cannot run load\_data.py at startup. DB is a static point-in-time snapshot by design — committing it is defensible and documented. |

| Repo architecture | jermaice/singapore-dementia-analysis as active repo; jermaice/area-intelligence-agent as source archive | Deployment simplicity won. Agent 2 build is the trigger to revisit whether a dedicated repo is warranted. |



\---



\*This document is a living reference. Update it as decisions are made and 

the architecture evolves.\*



\*Area Intelligence Agent — built on the Singapore Dementia Burden Analysis 

| April 2026\*

