#!/usr/bin/env python3
"""
goedel_agent.py — Call Goedel models via LM Studio for Lean 4 formalization and proof exploration.

Models:
    goedel-formalizer-v2-8b   — turns informal mathematical statements into Lean 4 theorem declarations
                                (statement-only; no proof body)
    goedel-prover-v2-8b       — attempts complete Lean 4 proofs of given goals

Usage:
    # Formalize an informal statement into a Lean theorem declaration:
    python3 goedel_agent.py --model formalizer \
      --prompt "The Motzkin polynomial x^4(y-1) + y^4(x-1) + (x*y - 1)^2 is nonnegative on R^2"

    # Attempt a proof of an existing Lean goal:
    python3 goedel_agent.py --model prover \
      --prompt "Prove that for all real x, x^2 >= 0"

    # Verify output against the Lean compiler (works for BOTH models):
    python3 goedel_agent.py --model formalizer --prompt "..." --verify
      # type-checks the sorry declaration (the statement anchor)
    python3 goedel_agent.py --model prover --prompt "..." --verify \
      --project-dir /home/YOUR-USER/Code/Python/positivstellensatz/VerifySection4

Exit codes:
    0 — Goedel responded successfully (output printed to stdout)
    1 — Lean verification failed (Goedel's output did not compile)
    2 — Goedel unavailable, fall back to current model
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import subprocess
import tempfile
import os

# ── Configuration ────────────────────────────────────────────────────────────
LM_STUDIO_URL = "http://YOUR-HOST:1234/v1/chat/completions"
MODELS = {
    "formalizer": "goedel-formalizer-v2-8b",   # statement formalization (informal -> Lean decl)
    "prover": "goedel-prover-v2-8b",           # proof search (goal + context -> full proof)
}
DEFAULT_MODEL = "prover"
TIMEOUT = 120          # seconds — proof generation can be slow
MAX_TOKENS = 16000     # half of 32K context, leaves room for system + input
TEMPERATURE = 0.1      # low temp for deterministic output

PROFILE_HOME = "/home/YOUR-USER/.hermes/profiles/math/home"
# Working Mathlib project: pre-built mathlib v4.31.0 oleans under .lake/packages/mathlib.
# (The old ~/.cache/lean4_tool/Lean4MCP_scratch no longer exists — do not point here.)
SCRATCH_PROJECT = "/home/YOUR-USER/Code/Python/positivstellensatz/VerifySection4"

SYSTEM_PROMPTS = {
    "formalizer": """You are Goedel-Formalizer-V2-8B, a model specialized in translating informal mathematical statements into Lean 4.
Given an informal statement, respond with:
1. The necessary `import` statements (prefer minimal but sufficient Mathlib imports)
2. A complete Lean 4 theorem/lemma declaration stating the result precisely — variables, quantifiers, and types fully specified
3. Do NOT write a proof body. End the declaration with `:= by sorry`.

Requirements:
- Use standard Mathlib type aliases (`ℝ`, `ℕ`, `ℤ`, `Finset`, etc.)
- State assumptions explicitly in the theorem signature (e.g., `(h : 0 ≤ x)`) or as hypotheses, never bury them in prose
- If the informal statement is ambiguous, choose the most standard interpretation and state it in a one-line comment above the declaration
- Always output valid Lean 4 syntax that can be compiled""",

    "prover": """You are Goedel-Prover-V2-8B, a model specialized in formal theorem proving with Lean 4 and Mathlib.
The user will give you a mathematical goal or Lean code snippet. Respond with:
1. The necessary `import` statements
2. A complete Lean 4 proof using `Mathlib`
3. Use standard Mathlib tactics (ring, nlinarith, linarith, aesop, apply, rw, simp)

Keep proofs concise. If a goal cannot be proven directly, explain why and suggest an approach.
Always output valid Lean 4 syntax that can be compiled.""",
}


def call_goedel(prompt: str, context: str = "", model_key: str = DEFAULT_MODEL) -> str:
    """Send prompt to the requested Goedel model via LM Studio OpenAI-compatible API."""

    if model_key not in MODELS:
        print(f"[GOEDEL ERROR] Unknown model key '{model_key}'. Choose from: {', '.join(MODELS)}", file=sys.stderr)
        sys.exit(2)
    model = MODELS[model_key]
    system_prompt = SYSTEM_PROMPTS[model_key]

    messages = [{"role": "system", "content": system_prompt}]

    user_content = ""
    if context:
        user_content += f"Context (imports/setup):\n```lean\n{context}\n```\n\n"
    user_content += f"Goal:\n{prompt}"

    messages.append({"role": "user", "content": user_content})

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        LM_STUDIO_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            return content.strip()
    except urllib.error.URLError as e:
        print(f"[GOEDEL ERROR] Cannot reach LM Studio: {e.reason}", file=sys.stderr)
        print("[FALLBACK] Use the current model's native Lean 4 tools instead.", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError:
        print("[GOEDEL ERROR] Invalid JSON response from LM Studio", file=sys.stderr)
        print("[FALLBACK] Use the current model's native Lean 4 tools instead.", file=sys.stderr)
        sys.exit(2)
    except KeyError as e:
        print(f"[GOEDEL ERROR] Unexpected response format: missing {e}", file=sys.stderr)
        print("[FALLBACK] Use the current model's native Lean 4 tools instead.", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"[GOEDEL ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        print("[FALLBACK] Use the current model's native Lean 4 tools instead.", file=sys.stderr)
        sys.exit(2)


def verify_lean(code: str, project_dir: str = None) -> bool:
    """Compile Lean code through `lake env lean` to check correctness."""

    if not project_dir:
        project_dir = SCRATCH_PROJECT

    # Write code to a temp file
    with tempfile.NamedTemporaryFile(suffix=".lean", mode="w", delete=False, dir="/tmp") as f:
        f.write(code)
        tmp_path = f.name

    try:
        env = os.environ.copy()
        env["HOME"] = PROFILE_HOME
        env["PATH"] = f"{PROFILE_HOME}/.elan/bin:/usr/bin:{env.get('PATH', '')}"

        result = subprocess.run(
            ["lake", "env", "lean", tmp_path],
            capture_output=True, text=True, timeout=300,
            cwd=project_dir, env=env,
        )

        os.unlink(tmp_path)

        if result.returncode == 0:
            print("\n[VERIFY] ✓ Lean compilation successful", file=sys.stderr)
            return True
        else:
            # lake/lean report errors and warnings on STDOUT, not stderr —
            # reading only stderr produced silent failures (observed 2026-08-31).
            combined = (result.stdout or "") + "\n" + (result.stderr or "")
            lines = [l for l in combined.strip().split('\n') if l.strip()]
            errors = [l for l in lines if 'error' in l.lower() or 'warning' in l.lower()]
            print(f"\n[VERIFY] ✗ Lean compilation failed", file=sys.stderr)
            for line in (errors or lines)[:10]:  # limit output; fall back to raw
                print(f"  {line}", file=sys.stderr)
            return False

    except FileNotFoundError:
        print("[VERIFY] 'lake' not found — skipping verification", file=sys.stderr)
        return None  # inconclusive
    except subprocess.TimeoutExpired:
        print("[VERIFY] Lean compilation timed out (300s)", file=sys.stderr)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return False


def extract_lean_code(response: str) -> str:
    """Extract Lean code blocks from Goedel's response."""
    import re

    # Look for fenced code blocks. The models emit ```lean, ```lean4, or bare
    # fences inconsistently — match any language tag (observed: formalizer emits
    # ```lean4, which the old r'```(?:lean)?\n' regex missed entirely).
    blocks = re.findall(r'```[A-Za-z0-9]*\s*\n(.*?)```', response, re.DOTALL)
    if blocks:
        return '\n\n'.join(blocks)

    # No fenced block found. If the response mixes prose and Lean code, keep
    # only lines from the first Lean command keyword onward (previously the
    # whole response — including prose preamble — was compiled verbatim).
    stripped = response.strip()
    lean_starters = ('import ', 'open ', 'set_option', 'theorem', 'lemma',
                     'example', 'def ', 'section', 'namespace')
    lines = stripped.split('\n')
    start = next((i for i, l in enumerate(lines) if l.lstrip().startswith(lean_starters)), None)
    if start is not None:
        return '\n'.join(lines[start:]).strip()

    return response


def main():
    parser = argparse.ArgumentParser(
        description="Call Goedel models (formalizer/prover) via LM Studio for Lean 4 work"
    )
    parser.add_argument("--prompt", required=True, help="The informal statement or the mathematical goal")
    parser.add_argument("--model", choices=list(MODELS.keys()), default=DEFAULT_MODEL,
                        help=f"Which Goedel model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--context", default="", help="Lean imports/setup code to include as context")
    parser.add_argument("--verify", action="store_true",
                        help="Compile Goedel's output with the Lean compiler "
                             "(works for both models; formalizer mode type-checks the sorry declaration)")
    parser.add_argument("--project-dir", default=SCRATCH_PROJECT, help=f"Mathlib project dir (default: {SCRATCH_PROJECT})")

    args = parser.parse_args()

    print(f"[GOEDEL] Querying {MODELS[args.model]} ({args.model} mode)...", file=sys.stderr)
    response = call_goedel(args.prompt, args.context, model_key=args.model)

    # Print Goedel's full response
    print("\n" + "=" * 60)
    print(f"GOEDEL RESPONSE ({args.model})")
    print("=" * 60 + "\n")
    print(response)

    if args.verify:
        code = extract_lean_code(response)
        ok = verify_lean(code, args.project_dir)
        if ok is False:
            sys.exit(1)
        elif ok is None:
            print("\n[VERIFY] Inconclusive — manually check the output", file=sys.stderr)


if __name__ == "__main__":
    main()
