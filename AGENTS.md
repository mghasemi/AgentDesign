# AGENTS.md — AgentDesign Project

## Goal

Document the complete design architecture of the **math** and **librarian** Hermes profiles,
their shared tool stack, designated skills for general math-related projects, MCP servers,
plugins, and end-to-end workflow. Produce a reusable design document that serves as
both a project architecture record and a template for creating new math-focused Hermes
profiles.

## Status

Active — Phase I (exploration) complete, Phase II (documentation) in progress.

## Working Directory

```
/home/mehdi/Code/Professional/AgentDesign/
```

## Key References

| Resource | Path |
|---|---|
| LaTeX template | `/home/mehdi/Code/Professional/Proposal/Template/Template.tex` |
| Math profile config | `~/.hermes/profiles/math/config.yaml` |
| Librarian profile config | `~/.hermes/profiles/librarian/config.yaml` |
| Math-research-workflow skill | `~/.hermes/profiles/math/skills/research/math-research-workflow/SKILL.md` |
| MCP CLI adapter | `~/.hermes/profiles/math/scripts/mcp_cli_adapter.py` |
| Profile data (extracted) | `data/profile_comparison.json` |

## Folder Structure

```
AgentDesign/
├── AGENTS.md              ← this file
├── README.md              ← project overview + build instructions
├── agent_design.tex       ← main LaTeX documentation (uses cpistuff/cpi template)
├── data/                  ← extracted configuration data
│   ├── profile_comparison.json
│   └── env_var_diff.json
├── figures/               ← diagrams (SVG → PDF for LaTeX)
│   ├── layer_architecture.svg
│   ├── profile_comparison.svg
│   ├── mcp_bridge.svg
│   ├── tool_stack_map.svg
│   └── abstraction_pipeline.svg
└── references/            ← reference documentation
    ├── profile_descriptions.md
    └── skill_inventory.md
```

## LaTeX Compilation

```bash
cd /home/mehdi/Code/Professional/AgentDesign/
latexmk -pdf agent_design.tex
```

Uses the `cpistuff/cpi` style package from the Proposal Template directory.
