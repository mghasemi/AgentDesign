/**
 * Wiki Browser Page — UI for browsing the Hermes knowledge wiki.
 * Simple page that displays wiki status and provides controls.
 */

import { useState, useEffect } from 'react'
import { Play, Square, RefreshCw, ExternalLink, Database } from 'lucide-react'

const WIKI_URL = 'http://localhost:5173'
const WIKI_PATH = '/home/YOUR-USER/Code/wiki'

interface ServerStatus {
  running: boolean
  port: number
  pid: number | null
}

interface ServerAction {
  ok: boolean
  message: string
  error?: string
}

export function WikiBrowserPage() {
  const [status, setStatus] = useState<ServerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  async function checkStatus() {
    try {
      const response = await fetch(`${WIKI_URL}/status`)
      if (response.ok) {
        const data: ServerStatus = await response.json()
        setStatus(data)
      } else {
        setStatus({ running: false, port: 5173, pid: null })
      }
    } catch (error) {
      setStatus({ running: false, port: 5173, pid: null })
    } finally {
      setLoading(false)
    }
  }

  async function startServer() {
    setActionLoading(true)
    try {
      const response = await fetch(`${WIKI_URL}/start`, { method: 'POST' })
      const result: ServerAction = await response.json()
      await checkStatus()
    } catch (error) {
      console.error('Failed to start server:', error)
    }
    setActionLoading(false)
  }

  async function stopServer() {
    setActionLoading(true)
    try {
      const response = await fetch(`${WIKI_URL}/stop`, { method: 'POST' })
      const result: ServerAction = await response.json()
      await checkStatus()
    } catch (error) {
      console.error('Failed to stop server:', error)
    }
    setActionLoading(false)
  }

  async function restartServer() {
    setActionLoading(true)
    try {
      // First stop, then start
      await stopServer()
      await new Promise(resolve => setTimeout(resolve, 1000))
      await startServer()
    } catch (error) {
      console.error('Failed to restart server:', error)
    }
    setActionLoading(false)
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <p className="text-muted-foreground">Loading wiki status...</p>
        </div>
      </div>
    )
  }

  const isRunning = status?.pid !== null

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold">Wiki Browser</h1>
        <p className="text-muted-foreground mt-2">
          Browse the Hermes knowledge wiki and manage the local dev server
        </p>
      </div>

      {/* Server Status Card */}
      <div className="rounded-lg border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Database className="h-5 w-5" />
          <h2 className="text-lg font-semibold">Dev Server Status</h2>
        </div>
        
        <p className="text-sm text-muted-foreground mb-4">
          {isRunning 
            ? `Running on port ${status?.port} (PID: ${status?.pid ?? 'unknown'})`
            : 'Not running'
          }
        </p>
        
        <div className="flex gap-2">
          {!isRunning ? (
            <button
              onClick={startServer}
              disabled={actionLoading}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground px-4 py-2"
            >
              <Play className="h-4 w-4 mr-2" />
              Start Server
            </button>
          ) : (
            <>
              <button
                onClick={stopServer}
                disabled={actionLoading}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-destructive text-destructive-foreground hover:bg-destructive/90 px-4 py-2"
              >
                <Square className="h-4 w-4 mr-2" />
                Stop Server
              </button>
              <button
                onClick={restartServer}
                disabled={actionLoading}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground px-4 py-2"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Restart
              </button>
            </>
          )}
          <a
            href={WIKI_URL}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 px-4 py-2 ${isRunning ? 'border border-input bg-background hover:bg-accent hover:text-accent-foreground' : 'bg-muted text-muted-foreground'}`}
            disabled={!isRunning}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Open Wiki
          </a>
        </div>
      </div>

      {/* Wiki Information Card */}
      <div className="rounded-lg border bg-card p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-2">Wiki Information</h3>
        <p className="text-sm text-muted-foreground mb-4">Location and resources</p>
        
        <div className="text-sm space-y-2">
          <p>
            <strong>Wiki Path:</strong>{' '}
            <code className="bg-muted px-2 py-1 rounded">~/Code/wiki</code>
          </p>
          <p>
            <strong>Dev Port:</strong>{' '}
            <code className="bg-muted px-2 py-1 rounded">5173</code>
          </p>
          <p>
            <strong>Documentation:</strong>{' '}
            <a 
              href="https://hermes-agent.nousresearch.com/docs" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              Hermes Documentation
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}