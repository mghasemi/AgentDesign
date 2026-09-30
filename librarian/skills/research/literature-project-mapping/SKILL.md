---
name: literature-project-mapping
description: "Use when linking wiki papers to research projects."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, literature, wiki, vikunja, project-planning, citation-verification]
    category: research
    related_skills: [llm-wiki, vikunja, math-research-workflow, arxiv, grounded-citations]
---

# Literature → Project Connection Mapping

Turn a newly ingested paper into actionable connections for an active research
project: locate it in the wiki, map its concepts onto the project's manuscript/
source documents at THEOREM level, verify metadata, encode the connection into
the Vikunja plan, and cross-link the wiki page. Executed end-to-end for
Cimprič–Kuhlmann–Scheiderer 2008 → MomentSheaf (2026-09-01); same shape has
served symmetric-algebras → MomentSheaf and jet/prolongation → DSDP.

## When to Use

- User asks to "check the concepts related to X in project Y" / "find the
  connections" / "see if there are relations in the wiki"
- A paper was just ingested into the wiki and needs linking to an active
  project (MomentSheaf, Mean Polynomial, DSDP, …)
- User asks to "update the plan" / "update the tasks" with the found relations
- User asks whether a paper/note is "worth combining into project X or should be a
  separate project"

## First decision: combine vs. separate project

Before mapping a paper/note onto an active project, classify it — the
"combine or separate?" question is answered HERE, before touching any file.

- **Combine** when the material is the *same mathematical family* and maps at
  theorem level onto an existing numbered result (a corollary/remark-level
  sharpening, complementary not competing). For a submission-ready manuscript
  this means POSITIONING ONLY: a bibliography entry + `classical · attributed`
  remarks + a claims-ledger entry, ZERO new theory (standing rule: no new
  theory before submission).
- **Separate project** when the material sits on an *orthogonal axis* (e.g.
  analytic quasi-analyticity vs. geometric inverse-limit) or is exploratory
  seed material that would need a new mechanism or a new section.

Deliver the verdict as a table (material → recommendation → confidence) before
editing anything; run the workflow below only for the "combine" branch.

## Workflow

1. **Orient in the wiki** (llm-wiki skill): read `SCHEMA.md`, relevant
   `index.md` rows, recent `log.md`, then the entity page + raw source of the
   paper. `search_files` the wiki for the paper's title/author to find the
   entity page.
2. **Map the project's relevant concepts**: read the project's manuscript
   section (e.g. MomentSheaf §7 Galois Descent) AND its phase source
   (`sources/phase5_galois_theory.md`) AND recent disposition reports.
   Search the `.tex` for the section labels; read the open-problems section
   (e.g. `sec:open`). Identify the theorems the paper could inform.
3. **Verify citation metadata FIRST** (never from memory): arXiv API via
   https (quirks below), Crossref, or Semantic Scholar. Confirm the wiki
   entity's metadata matches.
4. **Derive theorem-level connections, not topical overlap**: for each
   connection state the exact theorem pair (e.g. MomentSheaf Thm 7.6(1)
   `P(K) ≅ P'(K')^G` vs CKS Thm 4.1 `Q(T^G) = Q(T)^G`), the shared
   mechanism (averaging/trace), the hypothesis parallel, AND the structural
   difference ("X is NOT Y-descent"). A connection without a named theorem
   on both sides is a note, not a connection.
5. **Encode into Vikunja**: create a dedicated literature task under the
   project's correspondence umbrella (MomentSheaf: child of #712, labels
   `literature,manuscript`), containing the full connection analysis + the
   PLANNED manuscript actions (staged, not executed — each future edit needs
   the project's style pass + claims-ledger update). Update the open
   subtasks the connection feeds (e.g. Track C open-problem formulation,
   final audit checklist) by APPENDING to their descriptions.
6. **Verify Vikunja writes** (see pitfalls) and cross-link the wiki: add a
   "Connections to <Project>" section to the paper's entity page, bump
   `updated`, append `log.md`. No new page needed for the project itself
   (it lives in the repo).

## Pitfalls

### Vikunja `tasks list` paginates at 50 — never conclude absence from a list
`tasks list --project-id N` returns at most 50 tasks (oldest IDs first).
Observed 2026-09-01: project 27's list ended at #716 while #717–#727 existed.
`min/max` over returned ids is NOT the project's full range. Check existence
with `tasks get <id>` directly; when enumerating print `len(data)` and fetch
high-ID tasks individually.

### Vikunja parent-child verification is done from the PARENT side
A child's own object shows `related_tasks.parenttask: []` — the field is
populated only on the parent (it lists the parent's children). After
`tasks create --parent-task-id P`, verify with
`tasks get P` → `related_tasks.parenttask[].id` contains the new id. Empty
list on the child does NOT mean the link failed.

### arXiv API metadata verification (export.arxiv.org)
- Use `https://` only — plain `http` returns an empty/unparsable response and
  is security-flagged.
- Do NOT pipe `curl | python3` — the security scanner flags
  downloaded-content-to-interpreter. Write to a temp file first
  (`curl -sL "https://export.arxiv.org/api/query?id_list=<id>" -o /tmp/p.xml`),
  then parse in a separate command.
- In the Atom feed the FIRST `<title>` is the feed echo ("arXiv Query: …"),
  not the paper title — take the entry title (second/last `<title>`), authors
  from `<name>` elements, date from `<published>`.

### Update description, don't overwrite
Vikunja `tasks update` REPLACES the description. When adding an anchor to an
open task, fetch the current description first, append, then update.

### Same-author-group ≠ same paper
A fixed author group (e.g. Infusino–Kuhlmann–Kuna–Michalski) publishes a
series of closely-titled moment-problem papers. "Already cited" does NOT mean
"this is the paper already cited". Diff arXiv IDs/DOIs: the projective-limit
paper (arXiv:1906.01691, IEOT 94 2022) is distinct from the
intrinsic-characterization paper (arXiv:2204.05630, IMRN 2023). Cite the new
one as a separate `\bibitem` keyed by year and state the distinction explicitly
in the remark + claims ledger.

### Crossref DOI verification (companion to the arXiv query)
For a paper with a DOI, confirm the journal metadata from the primary source:
`curl -sL "https://api.crossref.org/works/<DOI>" -o /tmp/x.json` then read
`message.title`, `message.volume/issue/page`, `message.author[].family/given`,
`message['container-title']`. Pairs with the arXiv query for the arXiv ID and
author list.

### LLM/chat-generated notes are exploration seeds, not sources
A PDF that is an LLM conversation (Q&A turn structure, "ChatGPT can make
mistakes" footer, ad-blocker artifacts) is Rough-Ideas-class material: the
mathematics may be real, but it is never a citable source. Do not fold its
claims into a manuscript; at most seed a separate project from its framing.

## Support Files

- `references/momentsheaf-galois-cks.md` — MomentSheaf §7 theorem map, Vikunja
  #27 correspondence structure, CKS 2008 six-connection analysis (2026-09-01).
  Example of the theorem-level output this workflow should produce.
