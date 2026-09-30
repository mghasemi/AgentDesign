/**
 * Wiki Browser — Desktop UI component for the wiki-browser plugin.
 * 
 * Provides a page to browse and control the VitePress dev server for the Hermes wiki.
 * The wiki lives at ~/Code/wiki/ and runs on port 5173.
 */

import type { HermesPlugin } from '@hermes/plugin-sdk'
import { host, ROUTES_AREA, SIDEBAR_NAV_AREA, PALETTE_AREA } from '@hermes/plugin-sdk'

import { WikiBrowserPage } from './wiki-browser-page'

const WIKI_URL = 'http://localhost:5173'

const plugin: HermesPlugin = {
  id: 'wiki-browser',
  name: 'Wiki Browser',
  description: 'Browse the Hermes knowledge wiki and control the VitePress dev server',
  defaultEnabled: false,
  register(ctx) {
    ctx.registerMany([
      // Main wiki browser page
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/wiki-browser' } as const,
        render: () => <WikiBrowserPage />
      },
      // Sidebar navigation entry
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 45,
        data: { 
          codicon: 'book', 
          label: 'Wiki', 
          path: '/wiki-browser'
        } as const
      },
      // Palette command to open wiki browser page
      {
        id: 'open-wiki',
        area: PALETTE_AREA,
        data: {
          id: 'wiki-browser.open',
          label: 'Wiki: Open browser',
          keywords: ['wiki', 'knowledge', 'documentation'],
          run: () => host.navigate('/wiki-browser')
        } as const
      },
      // Palette command to start server
      {
        id: 'start-wiki',
        area: PALETTE_AREA,
        data: {
          id: 'wiki-browser.start',
          label: 'Wiki: Start dev server',
          keywords: ['wiki', 'start', 'vitepress'],
          run: async () => {
            try {
              const response = await fetch(`${WIKI_URL}/start`, { method: 'POST' })
              const result = await response.json()
              if (result.ok) {
                host.notifications.success('Wiki server started', result.message)
              } else {
                host.notifications.error('Failed to start wiki server', result.error ?? result.message)
              }
            } catch (e) {
              host.notifications.error('Error', 'Failed to start wiki server')
            }
          }
        } as const
      },
      // Palette command to stop server
      {
        id: 'stop-wiki',
        area: PALETTE_AREA,
        data: {
          id: 'wiki-browser.stop',
          label: 'Wiki: Stop dev server',
          keywords: ['wiki', 'stop', 'vitepress'],
          run: async () => {
            try {
              const response = await fetch(`${WIKI_URL}/stop`, { method: 'POST' })
              const result = await response.json()
              if (result.ok) {
                host.notifications.success('Wiki server stopped', result.message)
              } else {
                host.notifications.error('Failed to stop wiki server', result.error ?? result.message)
              }
            } catch (e) {
              host.notifications.error('Error', 'Failed to stop wiki server')
            }
          }
        } as const
      },
      // Palette command to restart server
      {
        id: 'restart-wiki',
        area: PALETTE_AREA,
        data: {
          id: 'wiki-browser.restart',
          label: 'Wiki: Restart dev server',
          keywords: ['wiki', 'restart', 'vitepress'],
          run: async () => {
            try {
              const response = await fetch(`${WIKI_URL}/restart`, { method: 'POST' })
              const result = await response.json()
              if (result.ok) {
                host.notifications.success('Wiki server restarted', result.message)
              } else {
                host.notifications.error('Failed to restart wiki server', result.error ?? result.message)
              }
            } catch (e) {
              host.notifications.error('Error', 'Failed to restart wiki server')
            }
          }
        } as const
      }
    ])
  }
}

export default plugin