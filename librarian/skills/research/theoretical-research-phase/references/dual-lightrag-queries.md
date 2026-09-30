# Dual LightRAG Query Pattern for Theoretical Research

When researching a theoretical framework that needs both broad context and specific source verification, use two complementary LightRAG query modes.

## Mode 1: Broad Context (mix or hybrid)

**Purpose:** Get the landscape — what's known, what theorems exist, what references are canonical.

```bash
cd /home/YOUR-USER/.hermes/profiles/math/skills/research/lightrag-query
LIGHTRAG_TIMEOUT=90 python3 lightrag_query_tool.py query \
  "Cech cohomology for directed systems, lim^1 derived functor for inverse limits, \
   Mittag-Leffler condition, Roos spectral sequence, cohomological obstructions" \
  --mode mix --include-references
```

**Characteristics:**
- Returns 10+ references with broad coverage
- Good for: discovering canonical texts (Bredon, Weibel), finding adjacent topics
- Timeout: 90s needed (default 20s is insufficient)
- Best when the query contains multiple related concepts

**Alternative:** `--mode hybrid` for when you want both graph-traversal and vector-search results merged.

## Mode 2: Source-Grounded Specifics (local)

**Purpose:** Verify a specific theorem, definition, or claim against the literature.

```bash
LIGHTRAG_TIMEOUT=60 python3 lightrag_query_tool.py query \
  "CGIK truncated moment problem, inverse limit of representing measures, \
   subcofinal family, K-frame condition, Theorem 4.2 gluing" \
  --mode local --include-references
```

**Characteristics:**
- Returns fewer references (5-7) but higher relevance
- Good for: confirming theorem statements, checking that a claim appears in the source
- Timeout: 60s usually sufficient
- Best for queries about a single paper or theorem family

## When LightRAG Returns Insufficient Context

Some niche results (obscure lemmas, specific corollaries, older papers) may not be indexed in LightRAG. Fall back to:

```python
web_search("Roos 1961 'Sur les foncteurs dérivés de lim'")
web_search("Bredon Sheaf Theory lim^1 Mittag-Leffler")
```

Then use `web_extract` on PDF URLs to get the full text.

## Concrete Example: MomentSheaf Phase 3

| Query Mode | Question | Result |
|------------|----------|--------|
| `--mode mix` | "Cech cohomology, lim^1, Mittag-Leffler, Roos spectral sequence" | Returned Bredon (Sheaf Theory), Scheiderer (Real/Etale Cohomology), Kashiwara (Categories and Sheaves), Delfs (Homology of Locally Semialgebraic) |
| `--mode local` | "CGIK Theorem 4.2, subcofinal K-frame, representing measures, inverse limit" | Returned Michalski (IMP), Fialkow (Truncated K-Moment Problem), Lasserre, plus CGIK-related fragments |

The mix query established the homological algebra backbone (Bredon, Roos). The local query verified the moment-problem-specific application (CGIK, Michalski). Together they provided source-grounding for all 9 sections of `phase3_cohomological_obstructions.md`.

## Key Pitfall: Timeout

`--mode mix` and `--mode hybrid` frequently time out at the default 20s. Always:

```bash
export LIGHTRAG_TIMEOUT=90  # env var, NOT a CLI flag
```

Do NOT use `--timeout 90` as a CLI argument — it's not supported and causes exit code 2.
