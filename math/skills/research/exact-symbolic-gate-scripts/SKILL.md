---
name: exact-symbolic-gate-scripts
description: "Use when writing deterministic exact-SymPy gate scripts."
version: 1.0.0
author: YOUR-USER
license: MIT
metadata:
  hermes:
    tags: [sympy, verification, deterministic, gate, math, research]
    related_skills: [sympy-mcp, sagemath-mcp, math-research-workflow, scientific-coding]
---

# Exact-Symbolic Gate Scripts

How to author the deterministic `*_gate.py` / `*_probe.py` scripts that back
mathematical claims with exact SymPy arithmetic. These scripts are the
reference-oracle artifacts that reports and claims ledgers cite; they must be
exact (no floats), deterministic (byte-identical on re-run), and auditable.

## When to Use

- Writing a script that asserts a mathematical fact over ℚ: rank of a Hankel
  or catalecticant matrix, sign of a determinant, a PSD condition, an exact
  threshold value in a parameter family.
- Any "deterministic check" whose exit code (0 = green) is the verification
  artifact a report will cite.

## Workflow

1. **Probe first.** Before encoding assertions, run a scratch `_probe_*.py` to
   establish the exact arithmetic facts — the rank, the determinant formula,
   the threshold — and print them for inspection. Delete the probe once the
   gate is green; only the gate survives.
2. **Promote to a gate.** One `chk(cond, msg)` assertion per fact, a running
   counter, `sys.exit(main())` so exit 0 = all green. Rank via
   `Matrix.rank()` over ℚ; PSD via exact principal-minor sign; never float.
3. **Make it deterministic.** Persist a log with any wall-clock timestamp
   stripped (or never written), then re-run and `sha256sum` the log. A
   byte-identical hash is what proves determinism — a timestamped log can
   never match itself, so strip it before hashing. Run the script with the
   project venv's interpreter **by path** (`<project>/.venv/bin/python
   gate.py`), not via `source <venv>/bin/activate && python gate.py`: a
   non-interactive shell may pin its own `VIRTUAL_ENV`, so `python` after
   activation can resolve to an interpreter without the gate's dependencies
   (`ModuleNotFoundError: No module named 'sympy'`). Invoking the interpreter
   directly is immune to the PATH ordering.
4. **Report the sha.** The report/ledger cites "exit 0, N checks,
   byte-identical re-run, sha256 `xxxx…`".

## Pitfalls

### f-string braces collide with LaTeX subscripts

Do not put a subscript `_{...}` or a set brace inside an f-string log or
assert message. `f"rank alpha_{2,F} = {w}"` parses `_{2,F}` as a format field
and raises `NameError: name 'F' is not defined` — the subscript reads as a
variable reference. Double the literal braces (`{{`/`}}`) or make the message
a plain (non-f) string. Scan every `chk(...)` message for braces before the
first run; this bites once per gate script that embeds indexed notation in its
labels.

### `Rational()` on a SymPy Symbol raises `TypeError`

Do not wrap coefficients in `Rational(cf)` inside a helper that must accept
symbolic input. A one-parameter family (a parameter `t`, `lam`, `eps`) makes
`cf` a Symbol, and `Rational(Symbol)` raises. Use SymPy-native operations that
auto-coerce — `cf / multinom(*mu)` or `cf * binomial(...)` — so Integer and
Symbol coefficients share one code path. Reserve `Rational`/`Integer` for
values already known to be concrete rationals, never in the hot path of a
helper the probe will later call with a symbolic parameter.

### Never float in a gate

A single `float` (e.g. `1/3` in a numeric expression, or `numpy` leakage)
silently degrades an exact assertion into an approximate one that may pass or
fail nondeterministically. Use `Rational` literals (`S(1)/3` or `Rational(1,3)`)
and assert the script imports no floating machinery. If a computed rank or
minor "looks right" but the value is a float, the check is not a proof.

### Hash the persisted file, not the gate's self-printed hash

Some gate scripts `print` a `log sha256 = …` line over their own log content.
That value can be computed over an in-memory (pre-normalization / pre-strip)
buffer and legitimately differ from the bytes finally written to disk. The
authoritative determinism check is `sha256sum <logfile>` on the file, compared
against the value a report or claims-ledger row already cites — never the
inline print. If the two disagree, the file hash is the record; re-hash the
file rather than re-running the gate to "fix" the printed value.
