# Hermes Plugin Debugging Reference

## Quick Diagnostic Checklist

When a plugin is not visible or functional in the Hermes desktop UI:

### 1. Verify Plugin Installation
```bash
# List all installed plugins
hermes plugins list

# Check if plugin is installed but disabled
ls -la ~/.hermes/plugins/<plugin-name>/

# Check math profile specifically
hermes plugins list --profile math
```

### 2. Check Plugin.yaml Structure
A valid `plugin.yaml` must include:
```yaml
name: <plugin-name>           # Required: human-readable name
key: <plugin-name>            # Required: unique identifier (CRITICAL!)
version: <version>            # Required: semantic version
description: <description>    # Required: description of functionality
```

**Missing `key` field = plugin not properly identified in UI.**

### 3. Verify Plugin Components
```bash
# Check if both backend and desktop components exist
ls -la ~/.hermes/plugins/<plugin-name>/
ls -la ~/.hermes/plugins/<plugin-name>/desktop/

# Verify desktop component exports
grep -n "export default" ~/.hermes/plugins/<plugin-name>/desktop/plugin.tsx
```

### 4. Desktop UI Component Requirements
The `desktop/plugin.tsx` file must:

```typescript
import type { HermesPlugin } from '@hermes/plugin-sdk'

const plugin: HermesPlugin = {
  id: '<plugin-key>',           // MUST match or be compatible with backend
  name: '<Human Name>',
  description: '<Description>',
  defaultEnabled: false,         // Optional: false = opt-in in settings
  register(ctx) {
    // Register UI contributions
    ctx.register([
      { id: 'route', area: ROUTES_AREA, data: { path: '/path' } satisfies RouteContribution },
      // ... other contributions
    ])
  }
}

export default plugin
```

### 5. Check for Hidden Prefixes
Plugins with these key prefixes are filtered from the user-facing plugin list:
- `dashboard_auth/`
- `model-providers/`
- `platforms/`
- `image_gen/`
- `teams_pipeline/`

These are intentionally hidden from Settings → Plugins.

## Common Plugin Issues

### Issue: Plugin appears in `hermes plugins list` but not in UI
**Root Causes:**
1. Missing `key` field in plugin.yaml
2. Missing desktop/UI component at `desktop/plugin.tsx`
3. Desktop component doesn't export valid HermesPlugin
4. Plugin key starts with hidden prefix

**Solution:**
1. Add `key` field to plugin.yaml
2. Create desktop/plugin.tsx with proper HermesPlugin export
3. Restart Hermes gateway: `hermes gateway restart`

### Issue: Desktop component exists but doesn't load
**Root Causes:**
1. TypeScript compilation errors
2. Invalid HermesPlugin export
3. Missing imports from `@hermes/plugin-sdk`
4. Syntax errors in plugin.tsx

**Solution:**
1. Check Hermes logs for loading errors
2. Verify plugin.tsx compiles without errors
3. Ensure imports are correct
4. Restart Hermes gateway

### Issue: Backend API works but UI shows no integration
**Root Causes:**
1. Plugin registered as backend-only (no desktop component)
2. UI contributions not registered in `register()` function
3. Desktop component always disabled

**Solution:**
1. Create desktop/plugin.tsx
2. Register UI contributions in the `register(ctx)` function
3. Set `defaultEnabled: true` if needed

### Issue: Plugin.yaml missing `key` field (CRITICAL - Most Common)
**Symptom:** Plugin doesn't appear in `hermes plugins list` or appears as "not enabled" with no UI

**Root Cause:** The `key` field is REQUIRED for plugin identification and management
- Without it, the plugin cannot be properly tracked
- The plugin system cannot generate a canonical key for toggling

**Solution:**
1. Add `key: <plugin-name>` field to `plugin.yaml`
2. Ensure the key matches the plugin directory name
3. Restart Hermes gateway

**Verification:**
```bash
# Check if key field exists
grep "^key:" ~/.hermes/plugins/<plugin-name>/plugin.yaml

# Should return: key: <plugin-name>
```

### Issue: Missing Desktop UI Component
**Symptom:** Plugin appears in list but provides no UI integration

**Root Cause:** Unified plugin packages require both backend (`plugin.yaml`) AND desktop UI (`desktop/plugin.tsx`)

**Solution:**
1. Create `desktop/` directory in plugin root
2. Create `desktop/plugin.tsx` with proper HermesPlugin export
3. Import from `@hermes/plugin-sdk`
4. Export default HermesPlugin object with `id` field
5. Register UI contributions in `register(ctx)`
6. Restart Hermes gateway

**Pitfall:** Desktop components must use the same `id` as the backend `key` field, or they won't be properly linked.

## Plugin Loading Flow

```
1. Hermes starts → scans ~/.hermes/plugins/*/plugin.yaml
2. For each plugin with desktop/ folder:
   - Reads desktop/plugin.tsx
   - Validates HermesPlugin export
   - Registers with SDK if enabled
3. Settings → Plugins page:
   - Filters out hidden prefixes
   - Shows only 'user' and 'project' source plugins
   - Displays enabled/disabled status
```

## Debugging Commands

```bash
# Restart gateway to reload plugins
hermes gateway restart

# Check gateway status
hermes gateway status

# List plugins with verbose output
hermes plugins list -v

# Check specific profile's plugins
hermes plugins list --profile <profile-name>

# Enable plugin and restart
hermes plugins enable <plugin-name>
hermes gateway restart

# Check for desktop component
ls -la ~/.hermes/plugins/<plugin-name>/desktop/plugin.tsx

# Verify key field
grep "key:" ~/.hermes/plugins/<plugin-name>/plugin.yaml
```

## File System Layout

```
~/.hermes/
├── config.yaml                    # Main config
├── profiles/
│   └── math/
│       ├── config.yaml            # Profile-specific config
│       └── plugins/
│           └── <plugin-name>/
│               ├── plugin.yaml     # MUST have 'key' field
│               └── desktop/      # MUST exist for UI integration
│                   └── plugin.tsx
└── plugins/                        # Agent plugins root
    └── <plugin-name>/              # Unified package pattern
        ├── plugin.yaml (with key)
        ├── <category>/              # Backend API
        │   └── *.py
        └── desktop/                  # Desktop UI
            └── plugin.tsx
```

## Verification Steps

After fixing a plugin:

1. **Restart gateway:**
   ```bash
   hermes gateway restart
   ```

2. **Verify in Settings:**
   - Open Hermes desktop app
   - Go to Settings → Plugins
   - Check if plugin appears in the list
   - Toggle enabled/disabled state

3. **Check functionality:**
   - Verify backend API responds
   - Check UI components are accessible
   - Test any registered routes or features

4. **Validate in logs:**
   - Look for plugin loading messages
   - Check for errors or warnings
   - Verify plugin ID registration

5. **Confirm API endpoint:**
   ```bash
   curl http://localhost:8766/api/plugins/<plugin-name>/status
   ```

## Useful File Paths

- Plugin manifest: `~/.hermes/plugins/<name>/plugin.yaml`
- Desktop component: `~/.hermes/plugins/<name>/desktop/plugin.tsx`
- Backend API: `~/.hermes/plugins/<name>/<category>/…`
- Profile plugins: `~/.hermes/profiles/<profile>/plugins/<name>/`
- Plugin storage: `~/.hermes/storage/plugins/<name>/`

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

## Common Plugin Patterns

### Pattern: Unified Agent Plugin with Desktop UI
When creating a plugin with both backend API and desktop UI:

1. **Create plugin.yaml** at plugin root WITH `key` field
2. **Create backend API** in `web/` or `<category>/` directory
3. **Create desktop UI** in `desktop/plugin.tsx`
4. **Use REST proxy** via `ctx.rest` namespace to `/api/plugins/<plugin-name>/`
5. **Register contributions** in `register(ctx)` function
6. **Set defaultEnabled** based on whether plugin should be opt-in or opt-out

**Pitfall:** The desktop UI must call backend APIs through the namespaced REST proxy, not directly to localhost ports. The Hermes gateway handles the routing.

### Pattern: Profile-Specific Plugin Enablement
Plugins enabled in `~/.hermes/profiles/<profile>/config.yaml`:
- Only active when that profile is selected
- Visible in profile-scoped plugin list
- Can be overridden at profile level
- Use `hermes plugins list --profile <name>` to verify