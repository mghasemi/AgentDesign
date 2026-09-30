# MathAgent Agent Definitions

The full agent definitions extracted from the MathAgent repository
(`/home/YOUR-USER/Code/Python/MathAgent/MathAgent/.github/agents/`).

## Agent Roster

| Agent | Stage | Tools | Responsibility |
|-------|-------|-------|----------------|
| Research Orchestrator | 1, 3, 5, 6 | read, search, execute, web | Central coordination, GoA message passing, stage gates |
| Literature Synthesis | 2 | read, search, execute, web | 7-source prioritized retrieval, synthesis report |
| Scientific Coding | 3 | read, search, execute | Empirical experiments in sandbox, validation of symbolic results |
| Lean4 Assistant | 4 | read, search, execute | Formal proof engineering, lemma search, proof certificates |
| Manuscript Pipeline | 5 | read, search, execute | Three-persona LaTeX pipeline (Drafter → Enhancer → Reviewer) |
| Reflexion | 1–6 | read, search, execute | 5-check quality certification, FoT aggregation |

## Routing Policy (Stage-First)

The Research Orchestrator uses a stage-first routing matrix:

| Stage | Who runs it | Primary tasks | Routing decision |
|-------|------------|---------------|------------------|
| 1 | Orchestrator | Decompose goal, create project, init workspace | Direct orchestration via Vikunja/SiYuan |
| 2 | Literature Synthesis Agent | Knowledge gathering, synthesis, ingest | **DELEGATE** — do not run tools directly |
| 3 | Orchestrator + Scientific Coding | Symbolic + empirical validation | Orchestrator runs SymPy → SageMath → Wolfram\|Alpha directly; passes results to SciCoding |
| 4 | Lean4 Assistant | Formal proof, certificate generation | **DELEGATE** — do not run Lean4 tools directly |
| 5 | Manuscript Pipeline | Drafting, enhancing, review | **DELEGATE** — do not run LaTeX tools directly |
| 6 | Orchestrator + Reflexion | Final certification, FoT aggregation, sign-off | Direct orchestration via Reflexion agent invocation |

## Service Endpoints

| Service | Primary URL | Fallback URL |
|---------|------------|--------------|
| LightRAG | `http://YOUR-HOST:9621` | `http://YOUR-DDNS-HOST:9621` |
| SimpleRAG | `http://YOUR-HOST:7000` / `http://127.0.0.1:7000` | `http://YOUR-DDNS-HOST:7000` |
| SearXNG | `http://YOUR-HOST:5050` | — |
| ZIMI | `http://YOUR-HOST:8899` | `http://YOUR-DDNS-HOST:8899` |
| Vikunja | `http://YOUR-HOST:3456` | `http://YOUR-DDNS-HOST:3456` |
| SiYuan | configured via env | — |
| Zotero | Web API (pyzotero) | — |
| Calibre | Content server | — |

## Manuscript Pipeline Constraints (Stage 5)

From the three-persona pipeline:

- Never advance a persona gate unless the gate condition is confirmed by tool output
- Never invent citation keys — only use keys confirmed by Zotero
- Do not modify proofs in the Proofs section — proofs are owned by the Lean4 Assistant; request changes through the Reflexion Agent
- Structure template uses `amsmath, amssymb, amsthm` and must follow exact section ordering

## STITCH Framework (Scientific Coding Agent)

The Scientific Coding Agent operates under the **STITCH** framework (Sliding-memory Trajectory Inference and Task Chunking Heuristic):

- Retains only decision-critical context: experiment objectives, current hypothesis, most recent result, known failures
- Never re-runs what has already failed (checks failure log first)
- All code runs in a resource-limited sandbox (`SANDBOX_CPU_SECONDS`, `SANDBOX_MEM_MB`)
- No network access in sandbox
- After 3 failures, escalate to human with structured failure report
