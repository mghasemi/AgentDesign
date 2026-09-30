#!/usr/bin/env python3
"""Extract profile configuration data for AgentDesign documentation."""
import json
from pathlib import Path
from yaml import safe_load
from datetime import datetime

PROFILES = ['math', 'librarian']
BASE = Path.home() / '.hermes' / 'profiles'

results = {}

for profile in PROFILES:
    pdir = BASE / profile
    config_path = pdir / 'config.yaml'
    env_path = pdir / '.env'
    profile_yaml = pdir / 'profile.yaml'

    with open(config_path) as f:
        cfg = safe_load(f)

    # MCP servers
    mcps = {}
    for name, scfg in cfg.get('mcp_servers', {}).items():
        cmd = scfg.get('command', [])
        if isinstance(cmd, list):
            cmd_str = ' '.join(cmd)
        else:
            cmd_str = str(cmd) if cmd else '(empty)'
        env_keys = list(scfg.get('env', {}).keys()) if isinstance(scfg.get('env'), dict) else []
        mcps[name] = {
            'command': cmd_str,
            'env_keys': env_keys,
            'env_count': len(env_keys)
        }

    # Disabled skills
    disabled = cfg.get('skills', {}).get('disabled', [])

    # Key config sections
    key_sections = {}
    for k in ['model', 'terminal', 'plugins', 'kanban', 'code_execution',
              'desktop', 'compression', 'telemetry', 'approvals', 'hooks',
              'platforms', 'image_gen', 'memory', 'context', 'moa']:
        if k in cfg:
            v = cfg[k]
            if isinstance(v, dict):
                key_sections[k] = {kk: vv for kk, vv in v.items()
                                   if not isinstance(vv, (list, dict)) or kk in ('disabled', 'entries', 'enabled')}
            elif isinstance(v, list):
                key_sections[k] = v
            else:
                key_sections[k] = v

    # .env parsing
    env_vars = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, val = line.split('=', 1)
                    env_vars[key.strip()] = val.strip()

    # home/ directory size
    home_dir = pdir / 'home'
    home_size = 0
    if home_dir.exists():
        import subprocess
        result = subprocess.run(['du', '-sb', str(home_dir)], capture_output=True, text=True)
        if result.returncode == 0:
            home_size = int(result.stdout.split()[0])

    # Scripts directory
    scripts_dir = pdir / 'scripts'
    scripts = []
    if scripts_dir.exists():
        scripts = [f.name for f in scripts_dir.iterdir() if f.is_file() and f.suffix == '.py']

    # Plugins
    plugins_dir = pdir / 'plugins'
    plugins = {}
    if plugins_dir.exists():
        plugins_enabled = cfg.get('plugins', {}).get('enabled', [])
        plugins_disabled = cfg.get('plugins', {}).get('disabled', [])
        plugin_entries = cfg.get('plugins', {}).get('entries', {})
        plugins = {
            'enabled': plugins_enabled,
            'disabled': plugins_disabled,
            'entries': plugin_entries
        }

    # Cron
    cron_dir = pdir / 'cron'
    cron_jobs = []
    if (cron_dir / 'jobs.json').exists():
        with open(cron_dir / 'jobs.json') as f:
            cron_data = json.load(f)
        for job in cron_data.get('jobs', []):
            cron_jobs.append({
                'name': job.get('name', '?'),
                'skill': job.get('skill', '?'),
                'model': job.get('model', '?'),
                'schedule': job.get('schedule', {}),
                'enabled': job.get('enabled', False),
                'last_status': job.get('last_status', '?')
            })

    # State DB
    state_db = pdir / 'state' / 'state.db'
    session_count = 0
    if state_db.exists():
        import sqlite3
        conn = sqlite3.connect(str(state_db))
        try:
            session_count = conn.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
        except:
            pass
        conn.close()

    # profile.yaml
    profile_desc = ''
    if profile_yaml.exists():
        with open(profile_yaml) as f:
            import yaml as yaml2
            pd = yaml2.safe_load(f)
            profile_desc = pd.get('description', '') if pd else ''

    results[profile] = {
        'profile_yaml_desc': profile_desc,
        'total_skills_resarch': len(list((pdir / 'skills' / 'research').iterdir())) if (pdir / 'skills' / 'research').exists() else 0,
        'total_skills_productivity': len(list((pdir / 'skills' / 'productivity').iterdir())) if (pdir / 'skills' / 'productivity').exists() else 0,
        'disabled_skills': disabled,
        'mcp_servers': mcps,
        'env_vars': {k: ('***' if any(x in k for x in ('KEY', 'TOKEN', 'PASSWORD', 'APPID')) else v)
                     for k, v in env_vars.items()},
        'home_size_bytes': home_size,
        'scripts': scripts,
        'plugins': plugins,
        'cron_jobs': cron_jobs,
        'session_count': session_count,
        'key_config_sections': key_sections,
        'profile_size_bytes': sum(f.stat().st_size for f in pdir.rglob('*') if f.is_file()) if pdir.exists() else 0
    }

# Compute diffs
if 'math' in results and 'librarian' in results:
    results['_diff'] = {
        'env_math_only': sorted(set(results['math']['env_vars']) - set(results['librarian']['env_vars'])),
        'env_librarian_only': sorted(set(results['librarian']['env_vars']) - set(results['math']['env_vars'])),
        'skill_disabled_diff': sorted(
            set(results['math']['disabled_skills']) - set(results['librarian']['disabled_skills'])
        ),
        'skill_disabled_in_librarian_only': sorted(
            set(results['librarian']['disabled_skills']) - set(results['math']['disabled_skills'])
        ),
        'mcp_diff': {
            name: {
                'math_cmd': results['math']['mcp_servers'].get(name, {}).get('command', ''),
                'lib_cmd': results['librarian']['mcp_servers'].get(name, {}).get('command', '')
            }
            for name in set(results['math']['mcp_servers']) | set(results['librarian']['mcp_servers'])
            if results['math']['mcp_servers'].get(name, {}).get('command', '') !=
               results['librarian']['mcp_servers'].get(name, {}).get('command', '')
        }
    }

output_path = Path(__file__).resolve().parent.parent / 'data' / 'profile_comparison.json'
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"Saved to {output_path}")
print(f"\n=== Math disabled that librarian does NOT disable ===")
for s in results['_diff']['skill_disabled_diff']:
    print(f"  {s}")
print(f"\n=== Librarian-only disabled skills ===")
for s in results['_diff']['skill_disabled_in_librarian_only']:
    print(f"  {s}")
print(f"\n=== MCP command diffs ===")
for name, diff in results['_diff']['mcp_diff'].items():
    print(f"  {name}:")
    print(f"    math: {diff['math_cmd'][:90]}")
    print(f"    lib:  {diff['lib_cmd'][:90]}")
