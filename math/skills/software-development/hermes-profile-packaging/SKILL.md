---
name: hermes-profile-packaging
description: "Use when packaging a sanitized, shareable profile pack."
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [packaging, sanitization, secrets, profiles, distribution]
    related_skills: [workspace-doc-hierarchy, latex-manuscript]
related_skills: [workspace-doc-hierarchy, latex-manuscript]
---

# Hermes Profile Packaging

Use when a profile (or any config tree holding credentials, endpoints and machine paths) must
become something another machine can install: a sanitized pack that keeps the structure and
loses every secret, endpoint and local path. The deliverable is a folder that can be copied
into place and a document that describes it without leaking the machine it came from.

## When to Use

- "Make these profiles copy-pasteable / ready to use"
- Scrubbing a configuration tree before sharing, publishing or handing to another operator
- De-localizing a design/report document (removing machine measurements) that ships with the pack
- Reviewing whether an existing pack still leaks (verification pass, see below)

## When Not to Use

- Installing or configuring Hermes itself — use the `hermes-agent` skill.
- Authoring a skill's SKILL.md — use `hermes-agent-skill-authoring`.
- Compiling the LaTeX document — use `latex-manuscript`.

## Workflow

1. **Decide what ships vs what is runtime state.** Keep the profile skeleton — `config.yaml`,
   `.env`, `profile.yaml`, `SOUL.md`, `skills/`, `plugins/`, `scripts/`, `cron/jobs.json`,
   `memories/`, `desktop-plugins/`, `hooks/`. Exclude per-session and per-machine state:
   `state.db*`, `sessions/`, `logs/`, caches, sandbox `home/`, `vault/`, `telemetry/`,
   `backups/`, `auth.json`, `*.lock`, `scratchpad/`, `sandboxes/`, `plans/`. Exclude the loader,
   curator and telemetry bookkeeping that sits *inside* `skills/` **by exact filename** —
   `.usage.json`, `.bundled_manifest`, `.curator_state`, `.curator_suppressed`,
   `.curator_ledger.jsonl`. Neither a directory rule nor a suffix filter catches them (`.usage.json`
   ends in `.json`), so a naive walk ships one machine's usage counters and curator ledger along
   with the skill trees. The concrete list and rationale:
   `references/exclusion-and-scrub-rules.md`.
2. **Build with a script, never by hand.** A re-runnable builder makes the pack auditable and
   re-derivable after the source profile changes. Walk the source tree, prune excluded dirs,
   copy files, then run the scrub pass over text files in place.
3. **Preserve empty directories.** `os.walk` yields only directories that (transitively) contain
   files, so empty category shells silently vanish from the pack and its structure no longer
   matches the source. Inside the walk, after pruning excluded dirs,
   `os.makedirs(dst, exist_ok=True)` for every `dirpath` — do not rely on file copies to create
   the tree.
4. **Scrub with two passes, not one.** (a) *Key-driven literals*: read the live `.env`/config,
   collect the actual secret values, and assert each is absent from the pack — this catches
   values a pattern list would not name. (b) *Pattern table*: IPs, DDNS hosts, `/home/<user>`,
   token prefixes (`tk_`, `sk-`, `hf_`, `ghp_`, `eyJ`), emails, username, GitHub handle.
   A pattern-only pass misses unlisted secrets; a literal-only pass misses values quoted in prose
   (a token or notebook id pasted into a skill doc).
5. **Replace, do not blank.** Credential files keep their KEY names with `REPLACE_ME` values
   (`KEY=REPLACE_ME`) so the structure stays readable and the next operator knows what to fill;
   hosts become `YOUR-HOST`, paths `YOUR-USER`, handles `YOUR-GITHUB`. Blanking a file hides the
   design; deleting the file hides the capability.
6. **Verify all five checks** before committing (see Verification).
7. **Ship a per-pack `README.md`**: the install command (`cp -r math/ ~/.hermes/profiles/math/`),
   the placeholder list, and a one-liner that greps for unfilled placeholders.
8. **De-localize the companion document** (see below).

## Scrub policy: three tiers

- **Scrub** — credentials, tokens, endpoints, hostnames, IPs, ports, absolute local paths,
  usernames (ssh/docker `user@host`, `username:` fields), author metadata, GitHub handles,
  author IDs, personal names in non-citation prose.
- **Keep verbatim — bibliographic citations.** Published references are public; rewriting
  `Author-Author-Author (2014)` into `YOUR-SURNAME-...` corrupts the literature content of the
  skills. Scrub identity *fields*, never citations.
- **Keep verbatim — skill and plugin NAMES.** Other files reference them by name; renaming one
  breaks the tree. Note this explicitly in the pack README so a reader knows the retention is
  deliberate. Public SaaS API URLs and timeout/mode values are not secrets either.

## Verification (run all five)

1. **Literal leak** — every collected source literal absent from both packs (byte scan, not grep).
2. **Pattern scan** — zero residual files for each pattern in the table.
3. **Credential-file scan** — for every `.env`/`.emv` in the pack, print each non-empty value that
   is not a placeholder. The survivors must all be benign (timeouts, public URLs, mode strings);
   anything else is an unreviewed secret.
4. **Config parse** — `yaml.safe_load` every `config.yaml`; no blank keys in `.env`.
5. **Structure parity** — diff top-level dirs and skill-dir counts against the live profile. The
   only permitted differences are the intentionally excluded runtime entries plus the pack README.

Also run `git check-ignore -v` on representative pack files before committing: a repo
`.gitignore` (`*.log`, `*.aux`) can silently drop files from inside skill trees, so confirm the
staged file count instead of trusting `git add -A`.

## Keeping the pack out of version control

- **An ignore rule does not untrack.** A file already in the index stays there until
  `git rm --cached <files>`, which keeps it on disk and drops it from the repository; ship the rule
  and the removal in one change. Keep the exclusion list in the builder *and* in `.gitignore` — the
  ignore protects the repository, the builder protects the artifact, and a rebuild otherwise
  reintroduces exactly what was just untracked.
- **Verify three ways.** `git check-ignore -q <path>` on the runtime paths (expect ignored); the
  same command on the design paths — the compiled deliverable, the `.tex`, the `.env`/`.emv`
  credential templates, `cron/jobs.json`, the scripts (expect *not* ignored); and
  `git ls-files -i -c --exclude-standard`, which must print nothing, since any hit is a tracked file
  the new rule just orphaned.
- **Never add a blanket pattern that catches a deliverable.** When the compiled PDF, the extracted
  JSON or an inventory is what ships, a `*.pdf`/`*.json` rule would ignore the deliverable itself.
  List the runtime files explicitly and state in a comment in the ignore file that the deliverable
  is tracked on purpose.
- **Test a builder rule change against a temp destination**, not by rebuilding in place:
  `copy_profile(src, tempfile.mkdtemp())`, then assert the excluded names are absent and the design
  files present. A rebuild in place mixes an unrelated full-tree diff into a one-line rule change.

## De-localizing the document that ships with the pack

A design document that quotes the machine is not distributable. Remove: sizes (`5.9 GB`), session
counts, timestamps and merge dates, config version numbers, hostnames/IPs/DDNS, absolute home
paths, and raw file/directory entry counts. **Keep design-level counts** that describe the
artifact (number of servers, skill categories, tools per server) — a table with no counts left is
not a design document. State the placeholder policy in a redaction note.

Verify on both surfaces: grep the `.tex` **and** the extracted PDF text (`pdftotext -layout`), since
prose rewritten in a later pass can reintroduce a removed pattern. The author line is document
metadata, not leaked profile data — leave it unless the user asks, and flag the choice in the
handoff. Keep the project's own derived artifacts (extracted JSON, inventories) sanitized with the
same rule set: shipping the folder while `data/` still holds local endpoints defeats the scrub.

## Pitfalls

- **Empty directories vanish.** The single most common structure-fidelity defect; see step 3.
- **A pattern list is not a leak check.** Both passes are required (step 4); each misses what the
  other catches. The residual scan must run on bytes, and over the packs *and* the project's data
  artifacts.
- **Do not blanket-replace a URL.** Replacing `http://host:3456/path` wholesale with `REPLACE_ME`
  destroys the shape; scrub the host and port and keep the scheme and path so the config still
  reads.
- **Excluding a directory the document advertises.** If the doc names a scratchpad, sandbox home
  or plans directory that the pack omits, say so in the pack README — otherwise the pack looks
  incomplete rather than deliberately minimal.
- **A suffix filter is not an exclusion list.** The bookkeeping files live inside `skills/` and one
  of them (`.usage.json`) ends in `.json`, so directory pruning and suffix rules both pass them
  through. Exclude them by exact name in the builder *and* in the ignore file.
- **Re-run the builder after every rule change.** Rules live in one place; hand-editing a pack
  makes the next rebuild silently revert the hand edit.
- **Table and figure polish in the shipped document** — the `latex-manuscript` skill's
table-overflow reference and the table-column-spec section of `math-article-revision` carry the
overfull-triage and professional-column recipes.
