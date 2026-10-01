# Exclusion and Scrub Rules

Concrete lists behind the packaging workflow. Adjust per profile; the *categories* are the durable
part, the names are examples.

## Exclude (per-session / per-machine state)

| Entry | Why |
|---|---|
| `state.db`, `state.db-shm`, `state.db-wal`, `state.db.*.lock`, retired WALs | runtime database + locks |
| `sessions/`, `logs/`, `hook_outputs/`, `gateway-starts.log` | conversation and process history |
| `cache/`, `*_cache.json`, `*_cache.etag`, `models_dev_cache*` | provider/model caches |
| `home/` (sandbox), `sandboxes/` | machine-local toolchain state (GBs) |
| `vault/`, `auth.json`, `auth.lock`, `honcho.json*` | credential stores — never ship |
| `telemetry/`, `backups/`, `state-snapshots/` | operational residue |
| `scratchpad/`, `plans/`, `pending/`, `tmp/`, `workspace/` | in-flight working state |
| `*.lock`, `*.bak*`, `config.yaml.backup` | locks and editor backups |
| `.usage.json`, `.bundled_manifest`, `.curator_state`, `.curator_suppressed`, `.curator_ledger.jsonl` | loader / curator / telemetry bookkeeping that lives *inside* `skills/` — per-installation state. Match by exact filename: `.usage.json` ends in `.json`, so a suffix filter passes it |

Keep: `config.yaml`, `.env`, `profile.yaml`, `SOUL.md`, `skills/`, `plugins/`, `scripts/`,
`cron/jobs.json`, `memories/`, `desktop-plugins/`, `hooks/`. Copy `cron/jobs.json` only — the job
output directory is state. Keep the credential files (`.env`, `.emv`) as key-preserving templates:
they document which keys each component needs, which is design information, not a leak.

## Scrub patterns

Apply in this order (specific before general), and never let a later rule re-introduce an earlier
value.

| Pattern | Placeholder |
|---|---|
| literal secret values collected from the live `.env`/config | `REPLACE_ME` (key-preserving) |
| `tk_[0-9a-f]{16,}`, `sk-[A-Za-z0-9_-]{16,}`, `hf_[A-Za-z0-9]{20,}`, `gh[pousr]_[A-Za-z0-9]{20,}` | `REPLACE_ME` |
| `eyJ...` JWT triplets | `REPLACE_ME` |
| `192.168.x.x`, private ranges | `YOUR-HOST` |
| DDNS hostname | `YOUR-DDNS-HOST` |
| `/home/<user>` | `/home/YOUR-USER` |
| `user@host` (ssh/docker), `user:user` (ownership) | `YOUR-USER@...` / `YOUR-USER:YOUR-USER` |
| `username:` / `author:` metadata fields | `YOUR-USER` |
| GitHub handle in repo URLs | `YOUR-GITHUB` |
| API author/profile ids (`author --id YOUR-S2-AUTHOR-ID`) | `YOUR-ID` |
| emails | `YOUR-EMAIL` |

Explicitly **not** scrubbed: bibliographic citations, skill/plugin names, public SaaS URLs,
timeouts and mode values.

## Verification snippets

```python
# 1. literal leak (byte scan — grep misses binary/encoding cases)
for v in source_literals:
    assert v.encode('latin-1', 'ignore') not in open(fp, 'rb').read()

# 3. credential-file scan: survivors must be benign
for fp in pack.rglob('.env') | pack.rglob('.emv'):
    for k, v in (l.split('=', 1) for l in fp.read_text().splitlines() if '=' in l):
        if v.strip() and not re.search(r'REPLACE_ME|YOUR-', v):
            report(k, v)          # every line here needs a human verdict

# 5. structure parity
assert sorted(live_top) - sorted(pack_top) == set(EXCLUDED)
assert len(live_skill_dirs) == len(pack_skill_dirs)
```

For the document: `pdftotext -layout out.pdf - | grep -E '<removed patterns>'` must be empty —
checking the `.tex` alone misses text reintroduced by a later prose pass.

## Version-control hygiene

Excluding a file is two operations, and the ignore rule is the smaller one: a file already in the
index is untracked only by `git rm --cached <files>` (which leaves it on disk). Run all three checks
before committing.

```python
# nothing tracked may be ignored — any hit is a file your new rule just orphaned
assert subprocess.run(['git', 'ls-files', '-i', '-c', '--exclude-standard'],
                      capture_output=True, text=True).stdout.strip() == ''

# the deliverable stays tracked (no blanket *.pdf / *.json rule)
tracked = subprocess.run(['git', 'ls-files'], capture_output=True, text=True).stdout
assert 'out.pdf' in tracked

# per-path polarity: runtime ignored, design kept
for path, expect in [('pack/state.db', True), ('pack/skills/.usage.json', True),
                     ('pack/.env', False), ('pack/cron/jobs.json', False)]:
    assert subprocess.run(['git', 'check-ignore', '-q', path]).returncode == (0 if expect else 1)
```

Test a change to the builder's exclusion list by copying to a temp destination
(`copy_profile(src, tempfile.mkdtemp())`) and asserting the excluded names are absent and the design
files present — never by rebuilding in place, which buries a one-line rule change in a full-tree diff.
