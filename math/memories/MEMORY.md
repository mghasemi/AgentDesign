DOX.md is the doc chain: AGENTS.md → subproject AGENTS.md → *.md notes → Sources/RoughIdeas/. Rough Ideas = exploration seeds, never cited directly.
§
Reports: /home/YOUR-USER/Code/Python/Reports/[project]_[timestamp].md, centralized.
§
Wiki: /home/YOUR-USER/Code/wiki/ (not profile home/wiki/).
§
Style check: apply ghasemi-latex-style anti-pattern checklist manually (no verifier script exists).
§
Git: no repo at Code/Python root; repos at subproject level — Irene (YOUR-GITHUB/Irene.git), IreneRewrite (worktree, branch rewrite), positivstellensatz (YOUR-GITHUB/positivstellensatz.git, main).
§
IreneRewrite merged to Irene (2026-09-18). All experiments run in Irene/.venv (Irene 2.0.0.dev0). Folder deleted, branch removed. Procedures: irene-rewrite-dev skill.
§
OptimizationInNorm (#31): E1.4 Lp quantile relaxation gives UPPER bounds (γ_p*≥f*); L∞=pointwise nonneg. C1 dual CGIK ordering open (E3.3).
§
Skill curation: curator touches created_by=agent only; foreground skill_manage delete works on bundled skills (skill-library-curation).
§
skill_view JSON may synthesize top-level related_skills absent from the file — read_file the region before patching SKILL.md frontmatter.
§
GMW 2014 = Ghasemi–Marshall–Wagner CMB 57(2) 289-302, arXiv:1109.0048.
§
MomentSheaf repositioned vs IKKM 2022 (IEOT 94(2) Art.12, arXiv:1906.01691; commit 10a3140): inverse-limit principle = prior art, ack'd in abstract+intro; claimed novelty = synthesis (set-level {M(B_ω)} for fixed L, P/M₊ variance, stalks). BdL AIF 9 (1959) 305-331, Edwards AIF 13 (1963) 111-121 verified via Numdam.
§
Portainer :9000 endpoint 3, X-API-Key (PORTAINER_API_KEY in profile .env); no SSH.
§
qwen3.8-27b (LM Studio): effort maps to thinking on/off only; budget 4k + SOUL.md anti-loop suffix set in LM Studio UI.
§
AGENTS.md writes are consent-gated (protected agent-instruction files); flag the unapplied edits in handoff, then retry after the user says "retry" — that counts as consent.
§
Sum2d (#35): objective = tensor analogue of SOS decomposition for sums of 2d powers (higher-order Gram maps, Σ₂d membership); corpus queryable via LightRAG + Wiki — do not re-audit ingest.
§
APPROVE pending_id: 962c8e6a