---
name: hermes-plugin-management
description: Use when installing, enabling, or debugging Hermes plugins.
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, desktop, electron, troubleshooting, plugins, typescript, react]
    related_skills: [inspecting-hermes-desktop-dom, hermes-desktop-troubleshooting]
---

# Hermes Plugin Management

## Critical Lesson: The `key` Field is REQUIRED

The most common cause of plugins not appearing in the UI is a **MISSING `key` field** in `plugin.yaml`. 

### Why it matters:
- Without `key`, the plugin cannot be properly identified in the Hermes plugin system
- Cannot be tracked in Settings → Plugins
- Cannot be toggled on/off
- Desktop UI component won't link to backend
- Plugin appears as "not enabled" with no UI integration

### Required plugin.yaml structure:
```yaml
name: <plugin-name>           # Required: human-readable name
key: <plugin-name>            # REQUIRED: unique identifier (CRITICAL!)
version: <version>            # Required: semantic version
description: <description>    # Required: description of functionality
```

## Install a Plugin from GitHub

```bash
# Clone to temp, then copy ONLY the plugin subdirectory
git clone --depth 1 <repo-url> /tmp/plugin-src
cp -r /tmp/plugin-src/<plugin-dir> ~/.hermes/plugins/<plugin-name>
```

### Critical: Plugin Directory Structure

`hermes plugins` scans `~/.hermes/plugins/*/` and expects `plugin.yaml` at the **root** of each plugin directory — NOT nested inside a subdirectory.

**Wrong:** `~/.hermes/plugins/hermes-android/hermes-android-plugin/plugin.yaml` (plugin invisible)
**Right:** `~/.hermes/plugins/hermes-android/plugin.yaml` (plugin detected)

If a plugin doesn't show up in `hermes plugins list`, check that `plugin.yaml` sits directly under the plugin folder.

## Enable a Plugin

```bash
hermes plugins enable <plugin-name>
# Takes effect on next gateway restart
hermes gateway restart
```

Verify:
```bash
hermes plugins list | grep <plugin-name>
# Should show: enabled
```

## Plugin Structure Requirements

Every Hermes plugin implementing both agent and desktop components needs a unified package structure:

### Agent-Plugin Root Structure
```
~/.hermes/plugins/<plugin-name>/
├── plugin.yaml         # REQUIRED: Backend plugin manifest with 'key' field
└── <category>/          # Category (web, tools, etc.) with Python backend
    └── <routes>.py      # REST API routes
```

### Desktop-UI Component (for UI integration)
```
~/.hermes/plugins/<plugin-name>/
├── plugin.yaml
└── desktop/
    └── plugin.tsx    # REQUIRED: Desktop UI component
                      # Must export default HermesPlugin with 'id', 'name', 'description' fields
```

**Critical:** The desktop component (`desktop/plugin.tsx`) must:
- Export a default `HermesPlugin` object with an `id` field matching the backend key
- Import from `@hermes/plugin-sdk`
- Be a valid React component that registers UI contributions

If missing or incomplete, plugin appears disabled in Settings and provides no UI integration.

### Unified Package Pattern (Recommended)
```
~/.hermes/plugins/<plugin-name>/
├── plugin.yaml                    # Agent plugin manifest (MUST have 'key')
├── <category>/                   # Python backend (API routes)
│   └── <api>.py
└── desktop/                      # TypeScript React UI component
    ├── plugin.tsx                # Must export default HermesPlugin
    ├── api.ts                    # API layer for backend communication
    └── <page>.tsx                # React page components
```

This ONE-INSTALL pattern is preferred over separate agent + desktop plugins.

## Troubleshooting Plugin Visibility

When a plugin doesn't appear in the UI:

1. **Check the key field**: `plugin.yaml` must have a `key` field for proper identification
2. **Verify plugin.yaml at root**: Must be at `plugin` directory root, not nested
3. **Verify BOTH components exist**: Agent plugins need desktop UI component at `desktop/plugin.tsx`
4. **Verify plugin ID**: Desktop plugin's `id` should match or be compatible with backend key
5. **Check for hidden prefixes**: Plugins with keys starting `dashboard_auth/`, `model-providers/`, or `platforms/` are filtered from user-visible list
6. **Check HIDDEN_KEY_PREFIXES**: The UI filters out plugins whose key starts with certain prefixes (see `agent-plugins.ts` line 47)
7. **Restart Hermes Desktop**: Completely restart the app, not just reload
8. **Check Hermes logs**: Look for plugin loading errors or compatibility warnings
9. **Verify desktop component exports**: Ensure `desktop/plugin.tsx` exists and exports valid HermesPlugin

### Common Pitfall: Server-Side vs Direct API Calls

The desktop UI component should communicate with the backend through `ctx.rest` (which proxies via Hermes gateway), NOT directly to localhost ports. Direct calls to `localhost:5173` or other ports from the desktop component will fail unless specifically allowed by the gateway.

For API endpoints on the same port as the wiki server (5123), use direct fetch in page components, not through the plugin REST interface. The plugin REST interface (`/api/plugins/<plugin-name>/...`) routes to backend plugin endpoints, not arbitrary localhost ports.

### Common Pitfall: Missing defaultEnabled or default State

If `defaultEnabled: false` is set, the plugin will be in Settings → Plugins but must be manually enabled. If omitted, it defaults to `true`, which may not be desired for opt-in features.

## Desktop UI Component Pattern

When creating a desktop UI component (`desktop/plugin.tsx`):

```typescript
import type { HermesPlugin } from '@hermes/plugin-sdk'
import { host, ROUTES_AREA, SIDEBAR_NAV_AREA, PALETTE_AREA } from '@hermes/plugin-sdk'

import { YourPage } from './your-page'

const plugin: HermesPlugin = {
  id: '<plugin-name>',              // MUST match the key in plugin.yaml
  name: '<Human Name>',
  description: '<Description>',
  defaultEnabled: false,            // Set true for auto-enable, false for opt-in
  register(ctx) {
    // REGISTER ALL CONTRIBUTIONS
    ctx.registerMany([
      // Routes
      {
        id: 'route',
        area: ROUTES_AREA,
        data: { path: '/path' } as const,
        render: () => <YourPage />
      },
      // Sidebar navigation
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: <number>,
        data: { codicon: 'icon-name', label: 'Label', path: '/path' } as const
      },
      // Palette commands
      {
        id: 'command',
        area: PALETTE_AREA,
        data: {
          id: 'plugin-name.action',
          label: 'Action Label',
          keywords: ['keyword1', 'keyword2'],
          run: () => { /* action */ }
        } as const
      }
    ])
  }
}

export default plugin
```

### API Layer Pattern (`desktop/api.ts`)

```typescript
import type { PluginRestOptions } from '@hermes/plugin-sdk'
import { atom } from 'nanostores'

type Rest = <T>(path: string, opts?: PluginRestOptions) => Promise<T>

let rest: Rest | null = null

export const $statusAtom = atom<null | StatusType>(null)

export function bindApi(r: Rest): () => void {
  rest = r
  // Initial data load if needed
  return () => { rest = null }
}

// All API calls go through this layer
export async function fetchStatus() {
  if (!rest) throw new Error('API not initialized')
  return rest<StatusType>('/status')
}
```

**Pitfall:** Desktop UI must call backend APIs through `ctx.rest` namespace (which proxies via Hermes gateway), NOT directly to localhost ports.

## Verification and Debugging

### Manual Verification Steps

After creating or modifying a plugin, verify:

1. **Plugin directory structure**:
   ```bash
   ls -la ~/.hermes/plugins/<plugin-name>/
   # Should see: plugin.yaml, dashboard/, desktop/
   ```

2. **plugin.yaml has key field**:
   ```bash
   python3 -c "import yaml; data=yaml.safe_load(open('~/.hermes/plugins/<plugin-name>/plugin.yaml')); print('key:', data.get('key', 'MISSING!'))"
   ```

3. **Desktop component exists**:
   ```bash
   ls -la ~/.hermes/plugins/<plugin-name>/desktop/plugin.tsx
   ```

4. **Restart Hermes Desktop completely** and check Settings → Plugins

### Debug Log Locations

```
~/.hermes/logs/desktop.log           # Desktop app logs
~/.hermes/profiles/<name>/logs/gateway.log  # Gateway logs
```

Look for:
- `[plugins]` messages during startup
- Plugin loading errors
- TypeScript compilation errors in desktop plugin

## Common Troubleshooting Table

| Symptom | Cause | Fix |
|---------|-------|-----|
| Plugin not in `hermes plugins list` | Missing/malformed `plugin.yaml` at plugin root | Move `plugin.yaml` to plugin directory root; verify it has `key` field |
| Plugin disabled but UI component missing | Plugin needs BOTH backend AND desktop UI components | Create `desktop/plugin.tsx` with valid HermesPlugin export |
| `plugin.yaml` missing key field | No unique identifier for plugin | Add `key: <plugin-name>` field to `plugin.yaml` |
| Desktop plugin not loading | Invalid TypeScript or missing HermesPlugin export | Check console errors; ensure default export is valid HermesPlugin |
| Plugin appears but no sidebar entry | Route registration failed or wrong area | Verify `ROUTES_AREA` and `SIDEBAR_NAV_AREA` contributions in plugin.tsx |
| Plugin toggles but state doesn't persist | Not enabled in profile config | Add plugin to `plugins.enabled:` in `~/.hermes/profiles/<name>/config.yaml` |
| Desktop component fails to compile | TypeScript/React error in plugin.tsx | Check Hermes dev console for compilation errors |

## References

- `references/plugin-state-diagram.md` - Plugin lifecycle and state management
- `references/desktop-sdk-patterns.md` - Common patterns for desktop UI components
- `references/gateway-proxy-setup.md` - How ctx.rest proxies to backend endpoints