# Plugin State Diagram

## Plugin Lifecycle

```
                    ┌─────────────┐
                    │  DISCOVER  │
                    │  plugin.yaml│
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  LOAD       │
                    │  (Backend)  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  ENABLE/DISABLE│
                    │  (Config)    │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │  ENABLED    │          │  DISABLED   │
       │  (UI load)  │          │  (UI unload)│
       └──────┬──────┘          └──────┬──────┘
              │                         │
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │  DESKTOP    │          │  NO DESKTOP │
       │  UI loaded  │          │  (if missing)│
       │  - Routes   │          │              │
       │  - Sidebar  │          │              │
       │  - Commands │          │              │
       └─────────────┘          └─────────────┘
```

## State Transitions

### 1. Discovery → Load
- Triggered by: Plugin directory scan
- Action: Read `plugin.yaml`, parse key field
- Result: Plugin entry added to inventory

### 2. Load → Enabled/Disabled
- Triggered by: `plugins.enable` / `plugins.disable` commands or config
- Action: Update plugin state in profile config
- Result: Plugin marked for loading on next Hermes restart

### 3. Enabled → Desktop UI (Optional)
- Triggered by: Plugin loads into desktop process
- Prerequisite: `desktop/plugin.tsx` must exist
- Action: Import and register HermesPlugin
- Result: Routes, sidebar, and palette commands registered

### 4. Disable → Hide Desktop UI
- Triggered by: Plugin disabled in config
- Action: Unregister contributions from desktop
- Result: UI elements removed from Hermes

## Persistent State

Plugin state is stored in:
```
~/.hermes/profiles/<name>/config.yaml
```

```yaml
plugins:
  enabled:
    - plugin-name-1
    - plugin-name-2
```

## Loading Order

1. Bundled plugins (in hermes-agent package)
2. User plugins (in ~/.hermes/plugins)
3. Agent plugins (runtime-loaded Python packages)

Each category loads in order, with later categories able to override earlier ones by same ID.

## Key Fields

### plugin.yaml (Backend)
```yaml
name: Human Readable Name
key: unique-plugin-id      # CRITICAL: Must be unique
version: 1.0.0
description: Functionality description
```

### plugin.tsx (Desktop)
```typescript
const plugin: HermesPlugin = {
  id: 'unique-plugin-id',   // Must match key in plugin.yaml
  name: 'Human Readable Name',
  description: 'Description',
  defaultEnabled: false,
  register(ctx) {
    // UI contributions
  }
}
```

## Common State Issues

### Issue: Plugin in enabled list but no UI
**Cause**: Missing `key` field or `desktop/plugin.tsx`
**Solution**: Add key field and create desktop component

### Issue: Plugin shows in Settings but toggle doesn't work
**Cause**: Plugin ID mismatch between plugin.yaml and plugin.tsx
**Solution**: Ensure `id` in plugin.tsx matches `key` in plugin.yaml

### Issue: Plugin UI loads but backend API not found
**Cause**: Backend routes not properly mounted or missing routes
**Solution**: Check `plugin_api.py` exists and routes are defined