---
name: workspace-doc-hierarchy
description: "Maintain layered AGENTS.md + DOX hierarchy for research projects with Rough Ideas discipline, project switching protocols, and documentation chain traversal."
version: 1.0.0
author: YOUR-USER
license: MIT
metadata:
  hermes:
    tags: [documentation, workspace, hierarchy, rough-ideas, project-management]
---

# Workspace Documentation Hierarchy

A layered AGENTS.md + DOX pattern for research projects with multiple subprojects. Implements strict documentation traversal rules and Rough Ideas discipline to prevent citing unverified exploratory content as facts.

## When to Use

Load this skill when:
- Onboarding to a new workspace with `AGENTS.md` + `DOX.md` hierarchy
- Switching between active research projects (e.g., Mean Polynomial ↔ Differential SDP)
- Updating project documentation after adding new subprojects or files
- Reviewing Rough Ideas folder content before citing anything
- Creating new subproject folders that need their own `AGENTS.md`

## Documentation Hierarchy Pattern

### Structure
```
Root AGENTS.md                          ← workspace-level overview, active projects list, Irene API reference
├── ./positivstellensatz/AGENTS.md      ← subproject context (MP, DSDP, etc.)
│   ├── .../*.md                        ← individual subproject notes/drafts
│   └── Sources/RoughIdeas/*            ← rough drafts (NOT rigorous facts)
├── ./Irene/doc/*.rst                   ← package API documentation
└── DOX.md                              ← framework rules for the chain itself
```

### Reading Protocol (MANDATORY — read from root down)

1. **Root AGENTS.md** → workspace overview, active projects list
2. **Every AGENTS.md along the path** to your target file
3. **Nearest owning doc** → local details; parent docs control repo-wide rules

**Rule**: If a parent lists a child whose scope contains the path you're editing, read that child too before making changes.

## Rough Ideas Discipline ⚠️ CRITICAL

`Sources/RoughIdeas/` contains exploratory PDFs/drafts that may lead to breakthroughs but are **NOT** mathematically rigorous.

### Never (absolute prohibition)
- Cite or prove from Rough Ideas directly in theses, papers, or formal documents
- Treat any result from Rough Ideas as established fact
- Use Rough Ideas content without verification

### Always do instead
1. **Treat as loose guidelines / exploration seeds only**
2. Before using any result: verify through Lean4, SymPy/SageMath computation, or peer-reviewed literature search (LightRAG, arXiv)
3. If you want to cite a Rough Ideas finding in a formal document, first re-derive it independently or find published support

### Current contents (as of 2026-07)
- `Real Differential Algebraic Geometry Synthesis.pdf` — differential algebra foundations
- `Differential Algebra Positivstellensatze Research.pdf` — ADE-based Positivstellensatz synthesis  
- `draft.pdf` — Differential SDP outline with polynomial optimization applications

## Project Switching Protocol

When working across multiple subprojects:

1. **Identify active projects** from root AGENTS.md "Active Projects" section
2. **Load nearest AGENTS.md** for the current project's deeper context
3. **Keep mental context separated** — do not mix theorems, notation, or conventions between projects unless explicitly relevant
4. **Borrow only when relevant** — if a technique from Project A applies to Project B, note it but don't conflate contexts

### Creating new subprojects

```markdown
# Create: ./positivstellensatz/<project-name>/AGENTS.md

# <Project Name>

## Goal
One-sentence purpose.

## Key References
- Author et al., "Title," Journal (Year) — DOI/URL if available
- [Other relevant papers]

## Status
- Current phase: [description]
- Next action: [specific task]
- Blocking items: [if any]

## TODOs
1. [ ] Task 1
2. [ ] Task 2
```

Then update root AGENTS.md "Active Projects" section to include the new project.

## Math Notation Standards (from DOX)

| Context | Format | Example |
|---------|--------|---------|
| Standalone formulas, theorems | `$$...$$` display math | $$f(x) = \sum_{i=0}^n a_i x^i$$ |
| Inline variables, short expressions | `$...$` inline math | The polynomial $p(x)$ is nonnegative. |
| Manuscripts (`.tex`) | LaTeX with `\label{}` and `\ref{}` | Chapter 4: The SOS Cone |
| Drafts/notes (`.md`) | Markdown + LaTeX math | Use `$$` for display, `$` for inline |

## Version Control Conventions (from DOX)

- **Commit frequency**: Per meaningful change (not after days of work); commit before starting new tasks
- **Never delete code** without verification — keep deleted files in a temporary branch until confirmed
- **Commit prefixes**: 
  - `[WIP]` — work-in-progress, not ready for review
  - `[Fix: ...]` — bug fixes
  - `[Test: ...]` — test additions or changes
  - `[Chore: ...]` — documentation, linting, dependency updates

## Cross-referencing in LaTeX (from DOX)

- Use `\label{}` and `\ref{}` within `.tex` files for internal references
- Reference sections by **name** rather than numbers when possible (e.g., `Chapter 4: The SOS Cone`)
- Numbered references are acceptable only when the section name is very long or unstable

## Pitfalls

- **AGENTS.md writes are consent-gated.** Editing any `AGENTS.md` triggers a protected-file approval prompt owned by the UI. If it times out, the write is **blocked** — silence is not consent: do not retry, and do not route around it via `terminal`/`execute_code`. The correct move is to flag the unapplied edits in your handoff (list the exact locations and intended changes) and wait; a user reply of "retry" after that flag *is* the consent. Because every retry costs a round-trip, batch all pending AGENTS.md edits and keep them to as few patches as possible.
- **Forgetting to read parent AGENTS.md**: Always start from root, even if you're editing a file in a subdirectory. Parent docs may list children whose scope contains your target.
- **Citing Rough Ideas**: This is the most common and dangerous mistake. Any result from `Sources/RoughIdeas/` must be verified before use in formal documents.
- **Conflating project contexts**: When switching between Mean Polynomial and Differential SDP, do not mix notation or conventions unless explicitly noted. Each project has its own AGENTS.md with local rules.
- **Stale documentation**: Update root AGENTS.md when adding new subprojects; update subproject AGENTS.md when status changes significantly.

## References

- [DOX.md](../../DOX.md) — Framework rules for the documentation chain
- [Root AGENTS.md](../../AGENTS.md) — Workspace overview with active projects list