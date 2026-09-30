---
name: sagemath-mcp
description: "Use for advanced algebraic structures (rings, fields, groups, number fields), arbitrary-precision arithmetic, matrix theory (eigenvalues, Jordan form), or any computation requiring SageMath's mathematical rigour. Falls back to SymPy when SageMath is absent."
metadata: {"clawdbot":{"emoji":"🔢","requires":{"bins":["python3"]},"optional_bins":["sage"],"config":{"env":{"SAGE_TIMEOUT":{"description":"Timeout in seconds for sage subprocess calls","default":"60","required":false}}}}}
---
# SageMath Symbolic & Algebraic Computation

Use this skill when you need SageMath's advanced mathematical environments: arbitrary-precision fields, abstract algebra, number theory, or matrix computations beyond SymPy's scope.

## When to Use

- Construct and manipulate polynomial rings, quotient rings, or finite fields.
- Compute eigenvalues, Jordan canonical forms, or Smith normal forms of matrices.
- Work with algebraic number fields, Galois groups, or integer lattices.
- Perform arithmetic in a `RealField(prec)` or `ComplexField(prec)` with arbitrary precision.
- Run SageMath scripts that are too large for inline `sage -c`.

## When Not to Use

- For basic calculus (derivatives, integrals, ODEs), prefer sympy-mcp — it is faster.
- For formal proofs, use lean4.
- For external data retrieval, use lightrag or academic-research-hub.

## Fallback Behaviour

If `sage` is not on `PATH`, the tool falls back to SymPy for supported operations and returns a `"fallback": true` flag in the JSON output. Install SageMath for full functionality.

## Commands

### Ring and field operations

```bash
python3 {baseDir}/sagemath_tool.py ring-ops "R.<x> = QQ[]; f = x^4 - 1; print(f.factor())"
python3 {baseDir}/sagemath_tool.py ring-ops "GF(7^2)" --format json
```

### Matrix operations

```bash
python3 {baseDir}/sagemath_tool.py matrix "A = matrix(QQ, [[1,2],[3,4]]); print(A.eigenvalues())"
python3 {baseDir}/sagemath_tool.py matrix "A = matrix(ZZ, [[6,4],[1,3]]); print(A.jordan_form())" --format json
```

### Arbitrary-precision arithmetic

```bash
python3 {baseDir}/sagemath_tool.py precision-arith "RR = RealField(100); print(RR(pi))"
python3 {baseDir}/sagemath_tool.py precision-arith "RR = RealField(200); print(RR(2).sqrt())"
```

### Number field operations

```bash
python3 {baseDir}/sagemath_tool.py number-field "K.<a> = NumberField(x^2 - 2); print(K.discriminant())"
python3 {baseDir}/sagemath_tool.py number-field "K.<z> = CyclotomicField(5); print(K.galois_group())"
```

### Run an arbitrary Sage script file

```bash
python3 {baseDir}/sagemath_tool.py run-script /path/to/script.sage
python3 {baseDir}/sagemath_tool.py run-script /path/to/script.sage --format json
```

## Output

```json
{
  "command": "matrix",
  "script": "A = matrix(QQ, [[1,2],[3,4]]); print(A.eigenvalues())",
  "stdout": "[-0.3722813..., 5.3722813...]",
  "stderr": "",
  "fallback": false,
  "success": true
}
```

## MCP Server (Recommended)

An MCP server at `sagemath_mcp_server.py` provides 9 native tools
(`sage_solve`, `sage_diff`, `sage_integrate`, `sage_simplify`,
`sage_factor`, `sage_expand`, `sage_latex`, `sage_matrix`,
`sage_run_script`). When SageMath is not installed, falls back
to SymPy transparently (no flag needed).

Registered in the math profile as MCP server `sagemath` — all 9 tools
appear automatically in new sessions as `mcp_sagemath_*`.

### Testing after install

```bash
hermes mcp test sagemath
```

### Pitfall: MCP times out on numerical work

`mcp_sagemath_sage_run_script` frequently times out (empty output,
`success: false`) on scripts that call `scipy.optimize.minimize_scalar`,
`numpy.trapezoid`, `scipy.integrate.quad`, or any loop with > ~20
iterations. This is NOT a broken install — the MCP runtime has a tight
timeout that numerical work exhausts. Symbolic-only calls (solve, diff,
integrate, simplify, factor) are fast and reliable via MCP.

**Fallback**: write the script to a `.py` file, then run via terminal:
```bash
unset CONDA_SHLVL CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_PYTHON_EXE
conda run -n sage python3 /path/to/script.py
```
The `unset` preamble is mandatory — the session inherits `CONDA_SHLVL=1`
which breaks `conda run` activation. Heredocs into `conda run` produce
no output; always use a `.py` file.

## CLI Tool (Legacy)

For situations where MCP is not available, use the CLI tool directly:

```bash
python3 {baseDir}/sagemath_tool.py ring-ops "R.<x> = QQ[]; f = x^4 - 1; print(f.factor())"
python3 {baseDir}/sagemath_tool.py matrix "A = matrix(QQ, [[1,2],[3,4]]); print(A.eigenvalues())"
```

## Configuration

- `SAGE_TIMEOUT`: subprocess timeout for `sage -c` calls. Defaults to `60` seconds.

## Installation

SageMath is installed at `/home/YOUR-USER/sage/` (source checkout, v10.10.beta2)
with the conda environment at `/home/YOUR-USER/miniconda3/envs/sage-dev/`.
The `sage` entry point is `/home/YOUR-USER/sage/sage` (shell script wrapper).
Subprocesses need `PATH` to include the conda `bin/` directory so that
`gap`, `gp`, etc. are found. The MCP server handles this automatically.

```bash
# Manual testing
PATH="/home/YOUR-USER/miniconda3/envs/sage-dev/bin:$PATH" /home/YOUR-USER/sage/sage -c "print(factor(x^4 - 1))"

# MCP server test
hermes mcp test sagemath
```
