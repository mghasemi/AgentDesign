# Wiki Linting Pitfalls — Session Notes (2026-07-29)

## YAML Frontmatter Gotchas Encountered

### 1. Closing `---` breaks PyYAML

```python
# WRONG — includes closing --- as document separator
fm = yaml.safe_load(stripped[3:end+3])  # ComposerError!

# RIGHT — strip before parsing
fm_block = stripped[3:end].rstrip()
fm = yaml.safe_load(fm_block)
```

### 2. YAML coerces dates to `datetime.date`

The string `2026-07-29` in YAML becomes a `datetime.date` object. Validating with `datetime.strptime()` fails because the input is already a date, not a string.

Fix: accept `(datetime, date)` types.

### 3. Leading blank lines before `---`

`write_file` sometimes produces a blank line before the opening `---`. Always `lstrip()` the content first.

## VitePress-Specific

- Dead links reported as `Found dead link ./path in file ...` — always Markdown-style `[text](file.md)`, never `[[wikilinks]]`
- The `concepts/index.md` and `comparisons/index.md` files use Markdown links — common source of dead-link errors after file renames
- Chunk-size warning is cosmetic, ignore it
- Clean run: zero errors from both Python linter AND VitePress build

## Repair Pattern

When lint finds issues:
1. Batch-read all broken files in parallel
2. Classify: frontmatter missing vs wrong vs filename vs broken link
3. Fix via `patch` (frontmatter) or `mv` (rename)
4. Update SCHEMA.md taxonomy before using new tags
5. Update index.md
6. Re-run both phases to confirm zero errors
7. Log to log.md

## Linter Script Location

`/home/YOUR-USER/Code/wiki/scripts/lint_wiki.py` — created during this session. Runs against wiki root at `/home/YOUR-USER/Code/wiki/`.
