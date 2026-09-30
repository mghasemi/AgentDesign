---
name: siyuan
description: "Use when working with SiYuan notes or blocks, especially when asked to search notes, search my notes, find notes, find my notes, get note content, ingest note content, open a note, retrieve a SiYuan block by id, or look up what my notes say about a topic."
---

# SiYuan Access Skill
Skill to search, read, and write notes/blocks in a running SiYuan instance.

## Critical Requirements (Pitfalls)
- **HTTP Method**: All API calls require `POST` — GET requests return 404
- **Auth Format**: Use `Authorization: Token ***` header (not Bearer)
- **Endpoint Structure**: Key endpoints are `/api/notebook/lsNotebooks`, `/api/query/sql`, `/api/system/getVersion`

## Usage
Execute the python script `siyuan_tool.py` located in the skill folder.

### Search for notes
\`\`\`bash
python3 {baseDir}/siyuan_tool.py search "your query"
\`\`\`

### Ingest note content
\`\`\`bash
python3 {baseDir}/siyuan_tool.py get "block_id"
\`\`\`

### Create a report block (workflow-compatible)
\`\`\`bash
python3 {baseDir}/siyuan_tool.py create-block \
	--title "Stage 3 Computation Report: claim" \
	--content "[report markdown]"
\`\`\`

### Create a document at explicit path
\`\`\`bash
python3 {baseDir}/siyuan_tool.py create-doc \
	--notebook "20210817205410-2kvfpfn" \
	--path "/mathagent/custom-report" \
	--markdown "# Report\n\nDetails"
\`\`\`

### Append or update a block
\`\`\`bash
python3 {baseDir}/siyuan_tool.py append-block --parent-id "20220107173950-7f9m1nb" --content "new section"
python3 {baseDir}/siyuan_tool.py update-block --id "20211230161520-querkps" --content "updated markdown"
\`\`\`

### Set block attributes
\`\`\`bash
python3 {baseDir}/siyuan_tool.py set-attrs --id "20210912214605-uhi5gco" --attrs '{"custom-stage":"3"}'
\`\`\`

## Configuration
- `SIYUAN_URL` primary endpoint
- `SIYUAN_ALT_URL` fallback endpoint
- `SIYUAN_TOKEN` API token
- Optional `SIYUAN_NOTEBOOK` default notebook id for document creation

### Where the config lives (IMPORTANT)
`siyuan_tool.py` auto-loads a `.emv` file by walking up from the skill dir. The
math profile keeps its credentials in **`productivity/siyuan/.emv`**:

```
SIYUAN_URL=http://YOUR-HOST:6806
SIYUAN_TOKEN=REPLACE_ME
SIYUAN_NOTEBOOK=REPLACE_ME   # "Cron" notebook
```

**Pitfall:** the SiYuan instance at `YOUR-HOST:6806` REQUIRES a token. Without
`SIYUAN_TOKEN`, every data endpoint (`lsNotebooks`, `/api/query/sql`,
`createDocWithMd`, …) returns `401 {"code":-1,"msg":"Auth failed [session]"}` —
only `/api/system/version` (no auth) responds. If a push suddenly starts failing
with 401, check that `.emv` still exists and the token is still valid (tokens can
be rotated in SiYuan → Settings → Interface).

**Known infra quirk:** the `delete*` filetree routes (`deleteDoc`, `deleteDocs`,
`deleteDocWithChildren`, `deleteBlock`) return an empty `200` (`text/plain`) and
do NOT actually remove the block on this instance — a reverse-proxy/gateway is
intercepting them. Read/search/create/update all work normally. To clean up a
test doc, delete it from the SiYuan UI.
