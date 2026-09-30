**Dependency Setup Guide**
1. Create virtualenv: `python -m venv .venv`
2. Activate: `. .venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Verify imports in REPL:
```python
>>> from Irene.mean_certificates import MeanCertificate
>>> symbols = __import__('sympy').symbols
>>> X,Y,Z,W = symbols('X Y Z W')
```