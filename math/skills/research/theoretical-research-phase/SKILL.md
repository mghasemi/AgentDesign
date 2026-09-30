---
name: theoretical-research-phase
description: "Use for theoretical research phases needing no computation."
version: 1.0.0
author: curator
metadata:
  hermes:
    tags: [research, theoretical, cohomology, foundations, pipeline]
    related_skills: [math-research-workflow, lightrag, vikunja, lean4]
---

# Theoretical Research Phase — Adapted Pipeline

When a research phase is purely foundational or theoretical (no computation, no numerical experiments), the standard 6-stage math-research-workflow needs adaptation.

## When to Use

- Building categorical frameworks (poset categories, functors, inverse systems)
- Constructing cohomology theories (Čech complexes, derived functors)
- Formulating exact sequences and obstruction theories
- Sheaf-theoretic restatements of existing theorems
- Homological algebra foundation-laying
- Any phase with no polynomials to factor, no SDPs to solve, no numerical experiments

Do NOT use for: computational phases (polynomial optimization, SDP hierarchy experiments, numerical validation), phases with concrete Lean4-amenable theorems ready for formal verification.

## Adapted Pipeline

### Stage 1 — Problem Decomposition (UNCHANGED)

Create Vikunja tasks as normal. Decompose into subtasks. Use `--parent-task-id` for nesting.
Verify parent-child relationships via `related_tasks.parenttask` (not `.relations`).

### Stage 2 — Literature Synthesis (DUAL-MODE QUERIES)

For theoretical work, use **two distinct LightRAG query modes**:

**Broad framing** — `--mode mix` or `--mode hybrid`, 90s timeout:
```bash
cd <lightrag-skill-dir>
LIGHTRAG_TIMEOUT=90 python3 lightrag_query_tool.py query \
  "<broad question>" --mode mix --include-references
```
Use for: "Cech cohomology for directed systems", "Mittag-Leffler condition".

**Source-grounded specifics** — `--mode local`, 60s timeout:
```bash
LIGHTRAG_TIMEOUT=60 python3 lightrag_query_tool.py query \
  "<specific theorem>" --mode local --include-references
```
Use for: "CGIK Theorem 4.2 gluing", "Bredon lim^1 construction".

**Fallback:** When LightRAG returns insufficient context, use `web_search` with specific author+theorem queries.

### Stage 3 — Computation: SKIP OR ADAPT

- **Skip entirely** when the phase is pure theory.
- **Adapt** when symbolic algebra IS needed: prefer SageMath MCP tools for single calls; use terminal `conda run -n sage python3 script.py` (with `unset CONDA_SHLVL` preamble) for multi-step scripts.

### Stage 4 — Verification: LITERATURE-VERIFY INSTEAD OF FORMAL-PROVE

- **Defer** Lean 4 verification to later phases when concrete theorems crystallize.
- **Literature-verify**: confirm each major claim against a published source (LightRAG excerpt or direct citation).
- The Reflexion Gate's "Logical Consistency" check still applies — verify definitions are well-posed, no circular reasoning.

### Stage 5 — Output: MARKDOWN PHASE DOCUMENT, NOT LATEX MANUSCRIPT

Produce a structured markdown document at `sources/phaseN_descriptive_title.md` with:
- Title, phase number, Vikunja task references
- Numbered sections corresponding to subtasks
- Display LaTeX ($$...$$) for all mathematical statements
- "References" table at the end
- "Open Questions" section feeding into the next phase

### Stage 6 — Reflexion Gate (ADAPTED CHECKS)

| Check | Theoretical Adaptation |
|-------|----------------------|
| Logical Consistency | Verify definitions well-posed; no circular reasoning |
| Notation Consistency | Cross-reference prior phase documents |
| Originality | LightRAG overlap check; attribute standard results |
| Citation Completeness | Every theorem/lemma has a named source |
| Assumption Impact | Flag compactness, Archimedean, etc. explicitly |

## Concrete Example: MomentSheaf Phase 3

Phase 3 built a cohomological framework (directed Čech complex, $\varprojlim^1$, exact sequence).

1. **Lit:** LightRAG `--mode mix` for broad cohomology context → Bredon, Roos, Scheiderer. LightRAG `--mode local` for CGIK specifics.
2. **Computation:** Skipped (pure homological algebra).
3. **Verification:** Literature-verified (Bredon Ch. I for $\varprojlim^1$, Roos 1961 for spectral sequence, CGIK for moment problem connection).
4. **Output:** `sources/phase3_cohomological_obstructions.md` (196 lines, 9 sections).
5. **Gate:** All 5 checks passed on literature-verification basis.
6. **Vikunja:** Phase 3 parent #418 + subtasks #419–#422 completed.

## Pitfalls

- **Don't force formal verification where it doesn't fit.** Cohomology isomorphisms aren't Lean-amenable without full Mathlib category theory. Literature-verification is correct.
- **Don't skip literature because "it's just foundations."** Even foundations need source-grounding.
- **LightRAG timeout:** `--mode mix`/`--mode hybrid` time out at default 20s. Set `LIGHTRAG_TIMEOUT=90` for complex queries.
- **Vikunja `tasks get` JSON:** Output format varies. Use `.get('title', d.get('data',{}).get('title','UNKNOWN'))` as defensive parse.
