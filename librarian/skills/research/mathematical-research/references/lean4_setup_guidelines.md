# Lean4 Troubleshooting
## Common Errors & Fixes
- **Path Issues**: Use `find / -name lean` to locate executables after install
- **Dependency Conflicts**: Isolate toolchains with `env -i PATH=/usr/bin:/bin lean --version`
- **Session Mismatches**: Always set `$HOME` explicitly for multi-profile environments