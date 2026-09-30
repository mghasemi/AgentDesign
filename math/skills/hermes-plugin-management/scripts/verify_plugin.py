#!/usr/bin/env python3
"""
Plugin verification script - checks plugin structure and configuration.

Run this after creating or modifying a Hermes plugin to verify it's properly structured.

Usage:
    python3 ~/.hermes/profiles/math/skills/hermes-plugin-management/scripts/verify_wiki_plugin.py <plugin-name>
"""

import sys
import yaml
from pathlib import Path

def verify_plugin(plugin_name: str) -> bool:
    """Verify plugin structure and configuration."""
    plugin_dir = Path.home() / ".hermes" / "plugins" / plugin_name
    
    errors = []
    warnings = []
    
    # Check plugin directory exists
    if not plugin_dir.exists():
        errors.append(f"Plugin directory does not exist: {plugin_dir}")
        return False
    
    # Check plugin.yaml
    plugin_yaml = plugin_dir / "plugin.yaml"
    if not plugin_yaml.exists():
        errors.append("plugin.yaml not found at plugin root")
    else:
        try:
            with open(plugin_yaml) as f:
                data = yaml.safe_load(f)
            
            # Check required fields
            if 'name' not in data:
                errors.append("plugin.yaml missing 'name' field")
            
            if 'key' not in data:
                errors.append("plugin.yaml missing 'key' field (CRITICAL)")
            elif data['key'] != plugin_name:
                warnings.append(f"plugin.yaml key '{data['key']}' doesn't match plugin name '{plugin_name}'")
            
            if 'version' not in data:
                warnings.append("plugin.yaml missing 'version' field")
            
            if 'description' not in data:
                warnings.append("plugin.yaml missing 'description' field")
                
        except Exception as e:
            errors.append(f"Failed to parse plugin.yaml: {e}")
    
    # Check desktop component
    desktop_plugin = plugin_dir / "desktop" / "plugin.tsx"
    if not desktop_plugin.exists():
        warnings.append("desktop/plugin.tsx not found - desktop UI will be disabled")
    else:
        # Check plugin.tsx has required exports
        content = desktop_plugin.read_text()
        if 'HermesPlugin' not in content:
            errors.append("desktop/plugin.tsx doesn't import HermesPlugin")
        if 'export default' not in content:
            errors.append("desktop/plugin.tsx missing default export")
        if 'id:' not in content:
            errors.append("desktop/plugin.tsx missing 'id' field in HermesPlugin")
    
    # Check backend API
    backend_dirs = ['dashboard', 'web', 'tools', 'memory', 'plugins']
    has_backend = any((plugin_dir / d).exists() for d in backend_dirs)
    if not has_backend:
        warnings.append("No backend directory found (dashboard, web, tools, etc.)")
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Plugin Verification: {plugin_name}")
    print(f"{'='*60}")
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    
    if not errors and not warnings:
        print("\n✓ Plugin structure looks good!")
        return True
    
    if errors:
        print(f"\n❌ Plugin has {len(errors)} error(s) that must be fixed")
        return False
    
    print(f"\n✓ Plugin structure OK, {len(warnings)} warning(s)")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: verify_plugin.py <plugin-name>")
        sys.exit(1)
    
    plugin_name = sys.argv[1]
    success = verify_plugin(plugin_name)
    sys.exit(0 if success else 1)