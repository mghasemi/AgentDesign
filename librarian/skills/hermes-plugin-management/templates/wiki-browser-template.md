# Wiki Browser Plugin Template

This template provides the complete structure for the wiki-browser plugin, including both backend and desktop components.

## Plugin Structure

```
wiki-browser/
├── plugin.yaml           # Backend plugin manifest (MUST have 'key' field)
├── dashboard/             # Backend API routes
│   ├── manifest.json
│   └── plugin_api.py     # REST API endpoints
└── desktop/               # Desktop UI component
    ├── plugin.tsx        # Main HermesPlugin export
    ├── api.ts            # TypeScript API layer for backend communication
    └── wiki-browser-page.tsx  # React page component
```

## Files to Create/Modify

### 1. plugin.yaml (REQUIRED - add 'key' field)

```yaml
name: wiki-browser
version: 1.0.0
key: wiki-browser                    # REQUIRED: Unique identifier (CRITICAL!)
description: "Backend API for the Wiki Browser desktop plugin — manages VitePress dev server lifecycle, plus desktop UI for browsing the Hermes knowledge wiki"
```

**CRITICAL:** Add the `key` field if it's missing. This is the primary cause of plugins not appearing in the UI.

**Why it matters:** Without the `key` field:
- Plugin cannot be properly identified in the Hermes plugin system
- Cannot be tracked in Settings → Plugins
- Cannot be toggled on/off
- Desktop UI component won't link to backend

### 2. desktop/plugin.tsx (MUST exist for UI integration)

```typescript
/**
 * Wiki Browser — Desktop UI component for browsing the LLM Wiki.
 * 
 * Provides UI to control the VitePress dev server and browse the knowledge wiki.
 */

import type { HermesPlugin } from '@hermes/plugin-sdk'
import { host, ROUTES_AREA, SIDEBAR_NAV_AREA, PALETTE_AREA } from '@hermes/plugin-sdk'

import { WikiBrowserPage } from './wiki-browser-page'
import { bindApi } from './api'

const plugin: HermesPlugin = {
  id: 'wiki-browser',              // MUST match the key in plugin.yaml
  name: 'Wiki Browser',
  description: 'Browse the Hermes knowledge wiki and control the VitePress dev server',
  defaultEnabled: false,             // Save user has to explicitly enable in Settings
  register(ctx) {
    // Bind the API layer
    const dispose = bindApi(ctx.rest)
    
    ctx.onDispose(() => {
      dispose()
      // Cleanup: stop server when plugin is disabled
      ctx.rest.post('/stop').catch(() => undefined)
    })

    ctx.registerMany([
      // Route for the wiki browser page
      {
        id: 'wiki-page',
        area: ROUTES_AREA,
        data: { path: '/wiki-browser' } as const,
        render: () => <WikiBrowserPage />
      },
      // Sidebar navigation
      {
        id: 'wiki-nav',
        area: SIDEBAR_NAV_AREA,
        order: 45,
        data: { 
          codicon: 'book', 
          label: 'Wiki', 
          path: '/wiki-browser'
        } as const
      },
      // Palette commands
      {
        id: 'wiki-open',
        area: PALETTE_AREA,
        data: {
          id: 'wiki-browser.open',
          label: 'Wiki: Open browser',
          keywords: ['wiki', 'knowledge', 'documentation'],
          run: () => host.navigate('/wiki-browser')
        } as const
      }
    ])
  }
}

export default plugin
```

**IMPORTANT NOTES:**
1. **File Location:** Must be at `~/.hermes/plugins/wiki-browser/desktop/plugin.tsx`
2. **Export:** Must export a default `HermesPlugin` object with `id` field matching the `key` in plugin.yaml
3. **Imports:** Use imports from `@hermes/plugin-sdk`
4. **Register Function:** The `register(ctx)` function must register all UI contributions
5. **API Layer:** Use `bindApi()` function to initialize REST API calls through `ctx.rest`
6. **defaultEnabled:** Set to `false` for plugins that should be opt-in (visible in Settings)
7. **TypeScript:** Ensure the file is valid TypeScript/React

### 3. desktop/api.ts (Helper for backend communication)

```typescript
import type { PluginRestOptions } from '@hermes/plugin-sdk'
import { atom } from 'nanostores'

type Rest = <T>(path: string, opts?: PluginRestOptions) => Promise<T>

let rest: Rest | null = null

export const $serverStatus = atom<{ ran: boolean; port: number; pid: number | null } | null>(null)

export function bindApi(r: Rest): () => void {
  rest = r
  checkStatus() // Initial check
  return () => { rest = null }
}

export async function checkStatus() {
  if (!rest) throw new Error('API not initialized')
  const result = await rest<{ running: boolean; port: number; pid: number | null }>('/status')
  $serverStatus.set({ ran: true, port: result.port, pid: result.pid })
  return result
}

export async function startServer() {
  if (!rest) throw new Error('API not initialized')
  const result = await rest('{ ok: boolean; message: string; pid?: number; error?: string }')('/start')
  await checkStatus()
  return result
}

export async function stopServer() {
  if (!rest) throw new Error('API not initialized')
  const result = await rest('{ ok: boolean; message: string; error?: string }')('/stop')
  await checkStatus()
  return result
}

export async function restartServer() {
  if (!rest) throw new Error('API not initialized')
  const result = await rest('{ ok: boolean; message: string; pid?: number; error?: string }')('/restart')
  await checkStatus()
  return result
}
```

### 4. desktop/wiki-browser-page.tsx (React UI component)

A React page component that displays:
- Server status (running/not running)
- Start/Stop/Restart buttons
- Wiki folder information
- Quick actions

### 5. dashboard/plugin_api.py (Backend API - ALREADY EXISTS)

The backend API should provide endpoints for:
- Server status (`/status`)
- Start VitePress server (`/start`)
- Stop VitePress server (`/stop`)
- Restart server (`/restart`)

Verify the API is working:
```bash
curl http://localhost:8766/api/plugins/wiki-browser/status
```

## Implementation Steps

### Step 1: Add Key to plugin.yaml
```bash
# Edit the file
nano ~/.hermes/plugins/wiki-browser/plugin.yaml

# Add this line after 'version:'
key: wiki-browser
```

**Verification:**
```bash
grep "^key:" ~/.hermes/plugins/wiki-browser/plugin.yaml
# Should return: key: wiki-browser
```

### Step 2: Create Desktop Component Structure
```bash
# Create the desktop directory
mkdir -p ~/.hermes/plugins/wiki-browser/desktop

# Create the required files:
# 1. plugin.tsx - Main plugin entry point
# 2. api.ts - API layer for backend communication
# 3. wiki-browser-page.tsx - React page component
```

### Step 3: Restart Hermes Gateway
```bash
hermes gateway restart
```

### Step 4: Verify in UI
1. Open Hermes Desktop app
2. Go to Settings → Plugins → Agent Plugins
3. Check if "Wiki Browser" appears in the list
4. Toggle it ON
5. It should stay enabled after restart

## Common Pitfalls

1. **Missing `key` field**: Plugin won't be properly identified in UI or Settings
2. **Missing `id` field**: Desktop component won't load or link to backend
3. **Wrong file location**: Desktop component must be in `desktop/plugin.tsx`
4. **TypeScript syntax errors**: Will prevent plugin from loading
5. **Not restarting gateway**: Changes won't take effect until restart
6. **Desktop `id` doesn't match backend `key`**: UI won't connect to backend
7. **Direct API calls instead of ctx.rest**: Can't access backend through gateway

## Testing

After implementation:

```bash
# 1. Check plugin.yaml has key field
grep "key:" ~/.hermes/plugins/wiki-browser/plugin.yaml

# 2. Check desktop component exists
ls -la ~/.hermes/plugins/wiki-browser/desktop/plugin.tsx

# 3. Check plugin is recognized
hermes plugins list | grep wiki-browser

# 4. Check backend API is accessible
curl http://localhost:8766/api/plugins/wiki-browser/status

# 5. Verify gateway status
hermes gateway status

# 6. Check plugin logs
hermes logs -n 100 | grep -i wiki
```

## Post-Fix Validation Checklist

After fixing plugin visibility issues:

- [ ] `plugin.yaml` has `key` field matching plugin name
- [ ] `desktop/plugin.tsx` exists and exports valid HermesPlugin
- [ ] Desktop `id` matches backend `key` field
- [ ] All imports from `@hermes/plugin-sdk` are valid
- [ ] TypeScript compiles without errors
- [ ] Hermes gateway restarted
- [ ] Plugin appears in Settings → Plugins
- [ ] Plugin toggles properly (enables/disables)
- [ ] Backend API endpoints respond
- [ ] UI contributions are accessible

## References

- [Hermes Plugin Management Skill](../SKILL.md) - Main skill with debugging checklist
- [Debugging Reference](references/debugging.md) - Common issues and solutions
- [Hermes Plugin SDK](https://hermes-agent.nousresearch.com/docs/plugins) - Official documentation