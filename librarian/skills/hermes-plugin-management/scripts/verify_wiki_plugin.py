#!/usr/bin/env python3
"""
Verification script for the wiki-browser plugin.

This script helps verify that the plugin is correctly structured and functional
after creation or modification.

Usage:
    python3 verify_wiki_plugin.py [--verbose]
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

PLUGIN_NAME = 'wiki-browser'
PLUGIN_ROOT = Path.home() / '.hermes' / 'plugins' / PLUGIN_NAME

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and print result."""
    exists = path.exists()
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    print(f"{status} {description}: {path}")
    return exists

def check_yaml_field(path: Path, field: str, expected: str = None) -> bool:
    """Check if a YAML file has a specific field with expected value."""
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        value = data.get(field)
        if expected:
            matches = value == expected
            status = f"{GREEN}✓{RESET}" if matches else f"{RED}✗{RESET}"
            print(f"{status} {field} field: {value} (expected: {expected})")
            return matches
        else:
            status = f"{GREEN}✓{RESET}" if value else f"{RED}✗{RESET}"
            print(f"{status} {field} field exists: {bool(value)} (value: {value})")
            return bool(value)
    except Exception as e:
        print(f"{RED}✗{RESET} Failed to read {field} from {path}: {e}")
        return False

def check_tsx_export(path: Path) -> bool:
    """Check if a TSX file exports a default HermesPlugin."""
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        has_export = 'export default' in content
        has_hermes_plugin = 'HermesPlugin' in content
        has_id = 'id:' in content or 'id =' in content
        
        status = f"{GREEN}✓{RESET}" if all([has_export, has_hermes_plugin, has_id]) else f"{RED}✗{RESET}"
        print(f"{status} {path.name} exports HermesPlugin with id: {all([has_export, has_hermes_plugin, has_id])}")
        
        if not has_export:
            print(f"  {YELLOW}⚠{RESET} Missing: export default")
        if not has_hermes_plugin:
            print(f"  {YELLOW}⚠{RESET} Missing: HermesPlugin type")
        if not has_id:
            print(f"  {YELLOW}⚠{RESET} Missing: id field")
        
        return all([has_export, has_hermes_plugin, has_id])
    except Exception as e:
        print(f"{RED}✗{RESET} Failed to check {path}: {e}")
        return False

def check_hermes_command(cmd: str, args: list = None) -> bool:
    """Run a Hermes CLI command and check if it succeeds."""
    try:
        result = subprocess.run(
            [cmd] + (args or []),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"{GREEN}✓{RESET} {cmd} {' '.join(args) if args else ''}")
            return True
        else:
            print(f"{RED}✗{RESET} {cmd} failed: {result.stderr[:100]}")
            return False
    except FileNotFoundError:
        print(f"{YELLOW}⚠{RESET} {cmd} not found in PATH")
        return False
    except Exception as e:
        print(f"{RED}✗{RESET} Error running {cmd}: {e}")
        return False

def main():
    """Run all verification checks."""
    verbose = '--verbose' in sys.argv
    
    print(f"\n{'='*60}")
    print(f"Verifying {PLUGIN_NAME} plugin")
    print(f"{'='*60}\n")
    
    results = []
    
    # 1. Check plugin.yaml exists and has key field
    print("1. Checking plugin.yaml...")
    plugin_yaml = PLUGIN_ROOT / 'plugin.yaml'
    results.append(check_file_exists(plugin_yaml, "plugin.yaml exists"))
    if plugin_yaml.exists():
        results.append(check_yaml_field(plugin_yaml, 'key', PLUGIN_NAME))
        results.append(check_yaml_field(plugin_yaml, 'name'))
        results.append(check_yaml_field(plugin_yaml, 'version'))
    print()
    
    # 2. Check desktop component exists
    print("2. Checking desktop component...")
    desktop_dir = PLUGIN_ROOT / 'desktop'
    plugin_tsx = desktop_dir / 'plugin.tsx'
    api_ts = desktop_dir / 'api.ts'
    
    results.append(check_file_exists(desktop_dir, "desktop/ directory exists"))
    results.append(check_file_exists(plugin_tsx, "plugin.tsx exists"))
    if plugin_tsx.exists():
        results.append(check_tsx_export(plugin_tsx))
    results.append(check_file_exists(api_ts, "api.ts exists"))
    print()
    
    # 3. Check backend API exists
    print("3. Checking backend API...")
    dashboard_dir = PLUGIN_ROOT / 'dashboard'
    plugin_api = dashboard_dir / 'plugin_api.py'
    
    results.append(check_file_exists(dashboard_dir, "dashboard/ directory exists"))
    results.append(check_file_exists(plugin_api, "plugin_api.py exists"))
    print()
    
    # 4. Check Hermes recognizes the plugin
    print("4. Checking Hermes plugin recognition...")
    results.append(check_hermes_command('hermes', ['plugins', 'list']))
    print()
    
    # 5. Summary
    print(f"{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    status = f"{GREEN}✓ PASS{RESET}" if passed == total else f"{RED}✗ FAIL{RESET}"
    print(f"{status}: {passed}/{total} checks passed")
    
    if passed < total:
        print(f"\n{YELLOW}Next steps:{RESET}")
        print("1. Restart Hermes gateway: hermes gateway restart")
        print("2. Open Hermes Desktop → Settings → Plugins")
        print("3. Verify wiki-browser appears in the plugin list")
        print("4. Toggle it ON if needed")
        print("5. Check that UI integration works")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())