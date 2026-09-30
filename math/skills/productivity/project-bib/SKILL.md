---
name: project-bib
description: "Use when creating, reading, editing, updating, validating, or syncing a local project-specific .bib fallback file, especially if Zotero sync fails or is unavailable."
---

# Project Bib Fallback

Use this skill to manage a local per-project bibliography fallback.

## Path policy
- Primary path: `.artifacts/projects/<project_slug>/references/references.bib`
- Optional mirror path: `manuscript/<project_slug>.bib`

## Commands

### Initialize project bib
```bash
python3 {baseDir}/bib_tool.py init --project-name "MathAgent: Graph Bounds"
python3 {baseDir}/bib_tool.py init --project-name "MathAgent: Graph Bounds" --sync-mirror
```

### Add entry
```bash
python3 {baseDir}/bib_tool.py add-entry --project-name "MathAgent: Graph Bounds" --entry-text '@article{smith2024graph,title={Graph bounds},author={Smith, A.},year={2024}}'
```

### Get / update / remove entry
```bash
python3 {baseDir}/bib_tool.py get-entry --project-name "MathAgent: Graph Bounds" --key smith2024graph
python3 {baseDir}/bib_tool.py update-entry --project-name "MathAgent: Graph Bounds" --key smith2024graph --entry-text '@article{smith2024graph,title={Graph bounds revised},author={Smith, A.},year={2024}}'
python3 {baseDir}/bib_tool.py remove-entry --project-name "MathAgent: Graph Bounds" --key smith2024graph
```

### Validate and sync mirror
```bash
python3 {baseDir}/bib_tool.py lint-bib --project-name "MathAgent: Graph Bounds"
python3 {baseDir}/bib_tool.py sync-mirror --project-name "MathAgent: Graph Bounds"
```

## Notes
- This skill is intended as a resilient fallback when Zotero cannot be used.
- Prefer deterministic BibTeX keys and keep entry types explicit (`@article`, `@inproceedings`, etc.).
