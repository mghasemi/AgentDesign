---
name: lean4-goedel-agent
description: "Use when Lean 4 work is involved — formalize informal statements via Goedel-Formalizer-V2-8B, then discover proofs with the Lean toolset + Goedel-Prover-V2-8B."
metadata: {"requires": {"bins": ["python3"], "env": {}}}
---

# Lean 4 Formalization & Proof Agent (Goedel models)

Two-model pipeline via LM Studio (`http://YOUR-HOST:1234/v1`):

| Model | Role | Output |
|-------|------|--------|
| `goedel-formalizer-v2-8b` | **Statement formalization** — informal math → Lean 4 theorem declaration | Compilable declaration ending in `:= by sorry` (statement only, no proof) |
| `goedel-prover-v2-8b` | **Proof search** — goal + context → complete Lean 4 proof attempt | Full proof body; verify before accepting |

Use this skill whenever Lean 4 formal reasoning is involved. The formalizer turns informal statements into verified-well-typed declarations; the existing Lean toolset (`lean4` MCP tools, `lean4_tool.py`) then drives proof discovery, with Goedel-Prover as the heavy-lift fallback for tactic sequences the active model is not confident about.

## When to Use — Activation Criteria

**Formalization stage (goedel-formalizer)** — activate when:
- A mathematical statement needs to be turned into Lean 4 before any proving begins (new theorem, lemma from a manuscript, conjecture)
- The informal statement has ambiguous quantifiers/hypotheses and you want the standard Mathlib interpretation materialized in code
- You need a compilable `sorry` declaration as an anchor for incremental proof work

**Proof stage (goedel-prover)** — activate on ANY of:
- **Strategy doubt**: The current model's proposed proof approach is complex, novel, or unverified — i.e., the proof is more than a one-liner `simp`/`ring`/`linarith` and you are not fully confident the tactic sequence closes the goal
- **High-cost exploration**: A wrong proof strategy would waste expensive Lean compilation cycles (long files, heavy Mathlib imports, slow tactics like `nlinarith` with many hypotheses)
- **Nonstandard imports**: You need Mathlib imports/structures you are not certain exist (`import Mathlib.X.Y.Z` guesses)
- **Novel mathematics**: Formalizing a new statement (e.g., nonnegativity certificates, SOS/SONC decompositions, polynomial identities) where Mathlib may not have a ready-made lemma
- **Partial proofs**: The current model wants to leave `sorry`/`admit`/`by aesop` gaps or an unverified sketch
- **Second opinion**: A proof compiles but relies on unusual/ugly tactics — ask Goedel for a cleaner, more standard route
- **Uncertainty about correctness**: You — or the current model — are not sure the strategy is sound; Goedel's independent attempt is cheap insurance
- **Explicit user request**: The user asks to use Goedel for a Lean task

### When NOT to use

- Trivial goals already solved (e.g., built-in Mathlib lemmas like `sq_nonneg`) — Goedel may produce circular proofs
- The user's task is not about Lean 4 formalization (this skill does not apply)

## Context Budget Warning

Goedel-Prover-V2-8B has a **32K token context window**. Keep prompts lean:
- Send only the relevant Lean code snippet (not entire files)
- Include at most 1–2 prior error messages
- Omit lengthy mathematical exposition — state the goal concisely

## Usage

### Stage 1 — Formalize an informal statement (formalizer)

```bash
python3 ~/.hermes/profiles/math/skills/research/lean4-goedel-agent/scripts/goedel_agent.py \
  --model formalizer \
  --prompt "The Motzkin polynomial x^4(y-1) + y^4(x-1) + (x*y - 1)^2 is nonnegative on R^2" \
  --verify
```

Expected output: a complete Lean 4 theorem declaration with imports, ending in `:= by sorry`. **`--verify` is mandatory here** (not just for the prover): it compiles the `sorry` declaration against Mathlib and exits non-zero on failure. A non-compiling formalization means the statement was mistranslated; re-prompt with the error message as context. Only proceed to proof search once verification passes.

### Stage 2a — Proof discovery with the existing Lean toolset

Once you hold a verified `sorry` declaration, work it with the standard `lean4` skill:
- `mcp__lean4__lean4_repl` / `lean4_search` to probe goals and find Mathlib lemmas
- `mcp__lean4__lean4_prove` for first-pass automation (`simp`/`ring`/`nlinarith`/`aesop`)
- Incremental filling of the proof body, re-checking with `mcp__lean4__lean4_check` after each step

### Stage 2b — Delegate stuck goals to Goedel-Prover (prover)

When automation fails or strategy confidence is low:

```bash
python3 ~/.hermes/profiles/math/skills/research/lean4-goedel-agent/scripts/goedel_agent.py \
  --model prover \
  --prompt "Prove that for all real x, x^2 >= 0"
```

### Check a Lean goal and get tactic suggestions (prover)

```bash
python3 ~/.hermes/profiles/math/skills/research/lean4-goedel-agent/scripts/goedel_agent.py \
  --model prover \
  --prompt "What tactics can close this goal? state: ⊢ ∀ (x y : ℝ), x^2 + y^2 = 0 → x = 0 ∧ y = 0"
```

### Full proof attempt with Lean verification

The script can pipe Goedel's output through the Lean compiler to verify correctness:

```bash
python3 ~/.hermes/profiles/math/skills/research/lean4-goedel-agent/scripts/goedel_agent.py \
  --model prover \
  --prompt "Formalize and prove: The sum of two squares is zero iff both are zero" \
  --verify \
  --project-dir /home/YOUR-USER/Code/Python/positivstellensatz/VerifySection4
```

### Fallback behavior

If a Goedel model is unavailable (network error, model not loaded, timeout), the script exits with code 2 and prints a fallback message. **When this happens:** formalizer down → write the Lean declaration yourself; prover down → continue with the current model's native Lean 4 tools (`mcp__lean4__*`, `lean4_tool.py`).

## Pipeline (end-to-end)

1. **Formalize & verify** — informal statement in; run `--model formalizer --verify`. Exit 0 = verified declaration (the anchor); non-zero = mistranslation, re-prompt with the compiler error as context. Do not build on an unverified declaration.
2. **Probe** — inspect goals and search Mathlib for candidate lemmas via `mcp__lean4__lean4_repl` / `lean4_search`.
3. **Attempt locally** — fill in straightforward subgoals with standard tactics; keep the declaration compiling after each step (re-check with `lean4_check`).
4. **Delegate on failure, not by default** — if local automation closes the goal, stop. Otherwise send to Goedel-Prover (`--model prover`) with the *verified* formalized statement as `--context` plus any partial proof; frame it as a complete theorem statement (the prover generates whole proofs, not tactic suggestions). Retry discipline: Error-Feedback Loop, budget 3; if the prover loops on the crux step (repeating a failed block past timeout), do not re-run it: verify against primary sources and close the step manually.
5. **Verify delegated output** — always compile with Lean (`--verify` or `lean4_check`) before accepting anything from the prover.
6. **Statement-fidelity check** — before integrating, diff the final verified Lean statement against the original informal claim (quantifiers, hypotheses, types, strictness). Retries can silently drift the statement into something weaker or vacuous; a proof of a drifted statement is not verification. Record the verified file path in the project claims ledger.
7. **Integrate verified proof** back into your project; remove `sorry`s only when the full file compiles clean.

If Goedel's attempt also fails to compile, fall back to the current model's native Lean 4 tools and combine the best of both attempts (e.g., a correct lemma from Goedel + a closing tactic from local search).

## Retry Discipline (Error-Feedback Loop)

All retries in this pipeline follow the **Error-Feedback Loop** and **Failure
Scratchpad** sections of `math-research-workflow` (read them there; they are
binding here):

- Re-prompt the formalizer/prover with the **exact compiler error** as
  `--context`; each retry must change the approach.
- Retry budget: **3** per goal. This subsumes the earlier "one recovery
  round-trip" rule for formalizer syntax drops.
- Failed Goedel attempts on a theorem go to
  `~/.hermes/profiles/math/scratchpad/<problem-slug>/failures.md`
  (one line: strategy | exact error | next approach) — check it before
  re-attempting any theorem, especially across sessions.

## Signals That the Current Model Is Struggling (bump priority to Goedel)

- Produces tactics that error out (unknown identifier, unexpected token, unsolved goals)
- Loops on the same failed `have`/`by` block with minor variations
- Wants to `sorry` a nontrivial step
- Can't name the Mathlib lemma it needs
- Is confident in an approach that is actually circular or false (e.g., using `sq_nonneg` to prove `sq_nonneg`)

## Environment

- LM Studio endpoint: `http://YOUR-HOST:1234/v1` (OpenAI-compatible)
- Models: `goedel-formalizer-v2-8b` (statements), `goedel-prover-v2-8b` (proofs) — both 32K context, verified serving as of 2026-08-28
- Timeout: 120s per call; Max tokens: 16000 (half context); Temperature: 0.1
- Lean toolchain for verification: **v4.31.0** (installed under both `/home/YOUR-USER/.elan` and the profile home's elan — either HOME works)
- Working Mathlib project: `/home/YOUR-USER/Code/Python/positivstellensatz/VerifySection4` (mathlib rev `fabf563`, pre-built olean files in `.lake/packages/mathlib`). Pass it as `--project-dir`. The old scratch path `~/.cache/lean4_tool/Lean4MCP_scratch` **no longer exists** — the `lean4` MCP server's auto-scratch will try to re-clone Mathlib (~7 GB) if pointed at it; prefer explicit project dirs.
- Verify declarations with: `cd <project> && HOME=/home/YOUR-USER PATH="/home/YOUR-USER/.elan/bin:/usr/bin:$PATH" lake env lean /path/to/file.lean`

## Pitfalls

- **Formalizer emits statement-only** — output ends in `:= by sorry` and may over-import (`import Mathlib`, `set_option maxHeartbeats 0`). Trim imports before integrating; the declaration must compile *with* the `sorry` (a type error here means mistranslation, not a missing proof).
- **Models emit `\u0060\u0060\u0060lean4` fences** — the formalizer wraps output in ```lean4 (not ```lean) and often prefixes it with prose. The script's fence regex must match any language tag (`[A-Za-z-]*`) or extraction silently falls through to compiling the whole response, including prose (observed 2026-08-31: correct Motzkin formalization failed `--verify` for this reason; fixed). Also note lake/lean report diagnostics on **stdout** — reading only stderr makes compile failures silent.
- **Formalizer can drop the theorem name** — observed emitting `theorem (a b : ℝ) : ... := by sorry` with no identifier. If that happens, re-prompt via `--context` showing the compiler error and an example of valid syntax (`theorem <name> (<vars>) : <statement>`), naming the desired identifier explicitly. The `--verify` flag catches this automatically (exit 1).
- **Formalizer picks interpretations silently** — it resolves ambiguity by "most standard interpretation" with a comment. For manuscript-level statements, read its chosen quantifier/hypothesis structure against the source claim before accepting; re-prompt if it buried an assumption or changed types (e.g., `ℕ` vs `ℝ`, strict vs non-strict).
- **`lean4_check` needs `project_dir` for files outside a project** — checking `/tmp/foo.lean` without `project_dir` runs bare `lean` with no Mathlib search path and fails with `unknown module prefix 'Mathlib'`. Always pass `project_dir: /home/YOUR-USER/Code/Python/positivstellensatz/VerifySection4` (or place the file inside a Lake project).
- **MCP scratch is a symlink, not self-healing** — `~/.cache/lean4_tool/Lean4MCP_scratch` → `VerifySection4`. If it is deleted again, `_resolve_scratch()` in `lean4_mcp_server.py` crashes with `[Errno 2] No such file or directory: PosixPath('/home/YOUR-USER/.cache/lean4_tool')` (its recovery path runs `lake new` in the missing parent dir). Fix: recreate `mkdir -p ~/.cache/lean4_tool && ln -sfn .../VerifySection4 ~/.cache/lean4_tool/Lean4MCP_scratch`.
- **Goedel-Prover generates whole proofs** — it may not understand incremental "what tactic next?" questions well. Frame the goal as a complete theorem statement with current partial proof in `--context`.
- **Prover can loop on crux claims** — observed (2026-08-29, MomentSheaf) looping indefinitely on deep topological set-theoretic steps. If output repeats a failed block or stalls past the timeout, do not re-run it: verify against primary sources and close the step manually.
- **Mathlib version mismatch** — both models were trained on Mathlib data that may differ from installed revision (v4.31.0). Always verify output compiles; lemma names may have moved or been renamed.
- **No state persistence** — each call is independent. If you need multi-step reasoning, send the full context (imports + prior proof attempts) in one prompt.
- **Short context** — never send an entire `.lean` file. Extract only the theorem and its immediate dependencies.
