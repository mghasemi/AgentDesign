/**
 * Wiki Browser — Hermes desktop plugin.
 *
 * Ensures the VitePress dev server for the math research wiki
 * (/home/YOUR-USER/Code/wiki, port 5173) is running, and provides a pane to
 * browse it inside the desktop app.
 *
 * Backend: plugins/wiki-browser/dashboard/plugin_api.py (start/stop/status).
 * All backend calls go through ctx.rest (authenticated, namespace-scoped) —
 * never raw fetch, which would 401 against the gateway.
 */

import {
  haptic,
  host,
  PALETTE_AREA,
  queryClient,
  useMutation,
  useQuery
} from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'

const ID = 'wiki-browser'
const WIKI_URL = 'http://localhost:5173/'
const STATUS_KEY = ['wiki-browser', 'status']

// ctx is only available inside register(); components capture it here.
let pluginCtx = null

function statusQuery() {
  return useQuery({
    queryKey: STATUS_KEY,
    queryFn: () => pluginCtx.rest('/status'),
    refetchInterval: 5000,
    refetchOnWindowFocus: false
  })
}

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function StatusDot({ running }) {
  return jsx('span', {
    className:
      'inline-block h-2 w-2 shrink-0 rounded-full ' +
      (running ? 'bg-(--ui-green)' : 'bg-(--ui-red)'),
    title: running ? 'Wiki server running' : 'Wiki server stopped'
  })
}

function WikiPane() {
  const { data, isLoading, isError, error } = statusQuery()

  const startMutation = useMutation({
    mutationFn: () => pluginCtx.rest('/start', { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: STATUS_KEY })
  })

  const stopMutation = useMutation({
    mutationFn: () => pluginCtx.rest('/stop', { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: STATUS_KEY })
  })

  const running = data?.running === true
  const busy = startMutation.isPending || stopMutation.isPending

  return jsxs('div', {
    className: 'flex h-full flex-col',
    children: [
      // Toolbar
      jsxs('div', {
        className:
          'flex items-center gap-2 border-b border-(--ui-stroke-secondary) px-3 py-2',
        children: [
          jsx(StatusDot, { running }),
          jsx('span', {
            className: 'text-sm font-medium text-(--ui-text-secondary)',
            children: running ? 'Wiki — connected' : 'Wiki — stopped'
          }),
          jsx('div', { className: 'flex-1' }),
          running
            ? jsx('button', {
                type: 'button',
                disabled: busy,
                className:
                  'rounded px-2 py-1 text-xs text-(--ui-text-secondary) transition-colors ' +
                  'hover:bg-(--chrome-action-hover) hover:text-(--ui-text-primary) ' +
                  'disabled:opacity-50',
                onClick: () => {
                  haptic('tap')
                  stopMutation.mutate()
                },
                children: busy ? 'Stopping…' : 'Stop'
              })
            : jsx('button', {
                type: 'button',
                disabled: busy,
                className:
                  'rounded bg-primary px-2 py-1 text-xs font-medium ' +
                  'text-primary-foreground transition-opacity hover:opacity-90 ' +
                  'disabled:opacity-50',
                onClick: () => {
                  haptic('tap')
                  startMutation.mutate()
                },
                children: busy ? 'Starting…' : 'Start'
              })
        ]
      }),

      // Content area
      (() => {
        if (isLoading) {
          return jsx('div', {
            className:
              'flex h-full items-center justify-center text-sm text-(--ui-text-tertiary)',
            children: 'Checking wiki server…'
          })
        }

        if (isError) {
          return jsxs('div', {
            className:
              'flex h-full flex-col items-center justify-center gap-2 p-4 text-center text-sm',
            children: [
              jsx('div', {
                className: 'text-(--ui-text-secondary)',
                children: `Cannot reach wiki backend: ${error?.message || 'unknown error'}`
              }),
              jsx('button', {
                type: 'button',
                className:
                  'rounded px-2 py-1 text-xs text-(--ui-text-secondary) ' +
                  'transition-colors hover:bg-(--chrome-action-hover) hover:text-(--ui-text-primary)',
                onClick: () => {
                  haptic('tap')
                  queryClient.invalidateQueries({ queryKey: STATUS_KEY })
                },
                children: 'Retry'
              })
            ]
          })
        }

        if (!running) {
          return jsx('div', {
            className:
              'flex h-full items-center justify-center text-sm text-(--ui-text-tertiary)',
            children: 'Wiki server is not running — click "Start".'
          })
        }

        return jsx('iframe', {
          src: WIKI_URL,
          className: 'h-full w-full border-0',
          title: 'Wiki Browser',
          sandbox: 'allow-scripts allow-same-origin allow-forms allow-popups'
        })
      })()
    ]
  })
}

function WikiChip() {
  const { data } = statusQuery()
  const running = data?.running === true

  return jsx('button', {
    type: 'button',
    className:
      'inline-flex h-full items-center gap-1 px-1.5 text-[0.6875rem] ' +
      'text-(--ui-text-tertiary) transition-colors hover:bg-(--chrome-action-hover) ' +
      'hover:text-(--ui-text-primary)',
    onClick: () => {
      haptic('tap')
      host.notify({
        kind: running ? 'info' : 'warning',
        message: running
          ? 'Wiki server is running (localhost:5173)'
          : 'Wiki server is stopped — click Start in the Wiki pane'
      })
    },
    children: jsxs('span', {
      className: 'flex items-center gap-1',
      children: [jsx(StatusDot, { running }), 'Wiki']
    })
  })
}

// ---------------------------------------------------------------------------
// Plugin definition
// ---------------------------------------------------------------------------

export default {
  id: ID,
  name: 'Wiki Browser',
  defaultEnabled: true,

  register(ctx) {
    pluginCtx = ctx

    // Right-hand pane for browsing the wiki.
    ctx.register({
      id: 'pane',
      area: 'panes',
      title: 'Wiki',
      data: { placement: 'right', width: '480px' },
      render: () => jsx(WikiPane, {})
    })

    // Status-bar indicator.
    ctx.register({
      id: 'chip',
      area: 'statusBar.right',
      order: 140,
      render: () => jsx(WikiChip, {})
    })

    // Palette command.
    ctx.register({
      id: 'open',
      area: PALETTE_AREA,
      data: {
        id: 'wiki-browser.open',
        label: 'Open Wiki Browser',
        keywords: ['wiki', 'browse', 'documentation'],
        run: async () => {
          try {
            const s = await ctx.rest('/status')
            if (s?.running) {
              host.notify({ kind: 'info', message: 'Wiki is running — see the Wiki pane' })
            } else {
              const res = await ctx.rest('/start', { method: 'POST' })
              host.notify({
                kind: res?.ok ? 'success' : 'error',
                message: res?.message || (res?.ok ? 'Wiki started' : 'Failed to start wiki')
              })
              queryClient.invalidateQueries({ queryKey: STATUS_KEY })
            }
          } catch (e) {
            host.notifyError(e, 'Wiki action failed')
          }
        }
      }
    })

    // Auto-start: run the wiki (if not already running) the moment the
    // plugin loads. Idempotent — /start is a no-op when the server is up.
    ctx.rest('/status')
      .then((s) => {
        if (s?.running) return
        return ctx.rest('/start', { method: 'POST' }).then((res) => {
          if (res?.ok) {
            host.notify({ kind: 'info', message: 'Wiki dev server started' })
            queryClient.invalidateQueries({ queryKey: STATUS_KEY })
          }
        })
      })
      .catch((e) => host.notifyError(e, 'Wiki auto-start failed'))
  }
}
