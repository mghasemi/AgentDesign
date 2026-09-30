# Skill Inventory — math vs librarian (extracted 2026-09-29)

Per-profile SKILL.md count: **math=57**, **librarian=57**; union=**59** (only-in-math: `irene-rewrite-dev`, `research/exact-symbolic-gate-scripts`; only-in-librarian: `productivity/calibre-library-ingestion`, `productivity/djvu-to-pdf`).

Status legend: **E** enabled · **D** disabled via `skills.disabled` (in profile tree) · **d** disabled name matches a *bundled-pool* skill (`~/.hermes/skills/`, 103 skills) not present in the profile tree · **P** phantom — no matching skill directory anywhere · **−** absent from this profile.

## `(top-level)`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `differential-sdp` | E | D |
| `ghasemi-latex-style` | E | E |
| `hermes-plugin-management` | E | E |
| `irene-rewrite-dev` | E | - |
| `semantic-scholar` | E | E |
| `workspace-doc-hierarchy` | E | D |

## `autonomous-ai-agents`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `autonomous-ai-agents/dynamic-workflow` | E | E |
| `autonomous-ai-agents/hermes-agent` | E | E |
| `autonomous-ai-agents/merge-reconciler` | D | D |

## `devops`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `devops/sdlc-review` | E | D |

## `github`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `github/github-auth` | D | D |
| `github/github-repo-management` | E | D |

## `mlops`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `mlops/dsdp-extension-workflow` | E | D |
| `mlops/inference/llama-cpp` | D | D |
| `mlops/lmstudio-configuration` | E | E |
| `mlops/pocketbase` | E | E |

## `productivity`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `productivity/calibre` | D | D |
| `productivity/calibre-library-ingestion` | - | E |
| `productivity/djvu-to-pdf` | - | E |
| `productivity/latex-manuscript` | E | E |
| `productivity/ocr-and-documents` | E | E |
| `productivity/project-bib` | E | D |
| `productivity/session-librarian` | E | D |
| `productivity/siyuan` | E | E |
| `productivity/vikunja` | E | E |
| `productivity/zotero` | E | E |

## `research`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `research/academic-research-hub` | E | E |
| `research/agent-tool-diagnostics` | E | E |
| `research/arxiv` | E | E |
| `research/exact-symbolic-gate-scripts` | E | - |
| `research/grounded-citations` | E | E |
| `research/hermes-tool-edge-cases` | E | E |
| `research/lean4` | E | D |
| `research/lean4-goedel-agent` | E | D |
| `research/lightrag` | E | E |
| `research/literature-project-mapping` | E | E |
| `research/llm-wiki` | E | E |
| `research/math-article-revision` | E | E |
| `research/math-research-workflow` | E | E |
| `research/mathematical-research` | E | E |
| `research/research-paper-writing` | E | E |
| `research/rss-feeds` | D | D |
| `research/sagemath-mcp` | E | D |
| `research/scientific-coding` | E | D |
| `research/searxng` | E | E |
| `research/sympy-mcp` | E | D |
| `research/theoretical-research-phase` | E | E |
| `research/wiki-maintenance` | E | E |
| `research/wiki-pipeline` | E | E |
| `research/wolfram-alpha` | E | E |
| `research/zimi` | E | E |

## `social-media`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `social-media/reddit-reading` | D | E |

## `software-development`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `software-development/github` | E | D |
| `software-development/hermes-agent-skill-authoring` | E | E |
| `software-development/hermes-desktop-troubleshooting` | E | E |
| `software-development/inspecting-hermes-desktop-dom` | E | D |
| `software-development/plan` | E | E |
| `software-development/subagent-driven-development` | E | E |

## `web`

| Skill (path relative to `skills/`) | math | librarian |
|---|:-:|:-:|
| `web/blocked-page-recovery` | E | E |

## `skills.disabled` audit


### math (12 entries)

| Name | Resolution |
|---|---|
| `calibre` | **⚠ PHANTOM** |
| `docx` | pool |
| `dogfood` | pool |
| `github-auth` | pool |
| `llama-cpp` | pool |
| `merge-reconciler` | pool |
| `node-inspect-debugger` | pool |
| `opencode` | pool |
| `powerpoint` | pool |
| `reddit-reading` | pool |
| `rss-feeds` | pool |
| `test-driven-development` | pool |

### librarian (28 entries)

| Name | Resolution |
|---|---|
| `calibre` | **⚠ PHANTOM** |
| `context-budget-audit` | **⚠ PHANTOM** |
| `differential-sdp` | **⚠ PHANTOM** |
| `docx` | pool |
| `dogfood` | pool |
| `dsdp-extension-workflow` | **⚠ PHANTOM** |
| `github` | in-tree |
| `github-auth` | pool |
| `github-repo-management` | pool |
| `inspecting-hermes-desktop-dom` | pool |
| `irene-rewrite-dev` | **⚠ PHANTOM** |
| `lean4` | **⚠ PHANTOM** |
| `lean4-goedel-agent` | **⚠ PHANTOM** |
| `llama-cpp` | pool |
| `local-model-delegation` | **⚠ PHANTOM** |
| `merge-reconciler` | pool |
| `node-inspect-debugger` | pool |
| `opencode` | pool |
| `powerpoint` | pool |
| `project-bib` | pool |
| `rss-feeds` | pool |
| `sagemath-mcp` | **⚠ PHANTOM** |
| `scientific-coding` | pool |
| `sdlc-review` | pool |
| `session-librarian` | pool |
| `sympy-mcp` | **⚠ PHANTOM** |
| `test-driven-development` | pool |
| `workspace-doc-hierarchy` | **⚠ PHANTOM** |