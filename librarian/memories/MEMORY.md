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
Numerical experiments (MP/DSDP/MeanDeltaSONC) run in IreneRewrite (/home/YOUR-USER/Code/Python/IreneRewrite/, worktree of Irene, branch rewrite, own .venv); classic Irene reference-only. Procedures: irene-rewrite-dev skill.
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
A #713-718 RESOLVED 2026-08-31: conjecture FALSE (βN ctr-ex); max-ideal criterion correct; B #719-722; C #723-726 open; audit #727; script create_correspondence_tasks.py.
§
qwen3.8-27b (LM Studio): effort maps to thinking on/off only; budget 4k + SOUL.md anti-loop suffix set in LM Studio UI.
§
AGENTS.md writes are gated by a consent prompt (protected agent-instruction files); user approves on request — don't retry unapproved, flag in handoff instead.