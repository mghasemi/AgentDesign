/**
 * Vikunja Dashboard — Hermes desktop plugin (runtime disk door).
 *
 * Compiled from plugins/vikunja/desktop/plugin.tsx for this shell: the disk
 * loader evaluates plain ESM and only rewrites `@hermes/plugin-sdk` / react*
 * specifiers, so lucide-react icons are replaced with styled text glyphs.
 * Behavior matches the .tsx source (projects sidebar, task browser, subtasks,
 * filters, search, toggle-done).
 *
 * Backend: plugins/vikunja/dashboard/plugin_api.py — all calls go through
 * ctx.rest (authenticated, namespace-scoped), never raw fetch.
 */

import { useState, useMemo } from 'react'
import { host, PALETTE_AREA, useQuery } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'

// Store plugin context globally.
let pluginCtx = null

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex || '')
  if (!result) return '0, 0, 0'
  return (
    parseInt(result[1], 16) + ', ' + parseInt(result[2], 16) + ', ' + parseInt(result[3], 16)
  )
}

function getPriorityColor(priority) {
  if (priority === undefined || priority === 0) return 'var(--ui-text-tertiary)'
  if (priority >= 4) return 'var(--ui-danger)'
  if (priority === 3) return 'var(--ui-warning)'
  if (priority === 2) return 'var(--ui-accent)'
  return 'var(--ui-success)'
}

// ---------------------------------------------------------------------------
// Task item
// ---------------------------------------------------------------------------
function TaskItem({ task, onToggle, expanded, onExpand }) {
  const hasSubtasks = (task.related_tasks?.subtask || []).length > 0
  const openSubtasks = (task.related_tasks?.subtask || []).filter((st) => !st.done)

  return jsxs('div', {
    className: 'flex items-start gap-2 px-2 py-1 hover:bg-ui-action-hover rounded',
    children: [
      // Expand chevron (indented rows only).
      jsx(
        'button',
        {
          type: 'button',
          disabled: !hasSubtasks,
          className: 'text-xs text-ui-text-tertiary leading-none mt-0.5 px-1 hover:text-ui-text-primary disabled:opacity-30',
          onClick: () => onExpand(task.id),
          children: (expanded && hasSubtasks ? '\u25B4' : '\u25BE') // ▲ / ▾
        }
      ),
      // Row.
      jsx(
        'button',
        {
          type: 'button',
          className: 'flex-1 min-w-0 text-left text-sm px-1 py-0.5 rounded hover:bg-ui-action-hover',
          onClick: () => onToggle(task),
          children: jsxs('div', {
            className: 'flex items-center gap-2',
            children: [
              task.done ? (
                jsx('span', {
                  title: 'done',
                  className: 'text-sm leading-none shrink-0 text-ui-success',
                  children: '\u2713' // ✓
                })
              ) : (
                jsx('span', {
                  className: 'text-sm leading-none shrink-0 text-ui-text-tertiary',
                  children: '\u25CB' // ○
                })
              ),
              jsx('span', { className: 'truncate flex-1', children: task.title }),
              (task.due_date && !task.done) &&
                jsx(
                  'span',
                  {
                    className: 'text-xs text-ui-text-tertiary shrink-0',
                    children: new Date(task.due_date).toLocaleDateString()
                  }
                ),
              task.priority > 0 &&
                jsx('span', {
                  title: 'priority ' + String(task.priority),
                  style: { color: getPriorityColor(task.priority) },
                  className: 'text-xs shrink-0',
                  children: '\u2605' // ★
                })
            ]
          })
        }
      ),
      hasSubtasks &&
        jsx(
          'span',
          {
            className: 'text-xs text-ui-text-tertiary ml-auto shrink-0 mt-0.5',
            children: String(openSubtasks.length) + ' open'
          }
        )
    ]
  })
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
function VikunjaPage() {
  const [selectedProject, setSelectedProject] = useState(null)
  const [filter, setFilter] = useState('open')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedTasks, setExpandedTasks] = useState(() => new Set())

  function toggleExpand(taskId) {
    setExpandedTasks((prev) => {
      const next = new Set(prev)
      if (next.has(taskId)) {
        next.delete(taskId)
      } else {
        next.add(taskId)
      }
      return next
    })
  }

  // Load projects.
  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['vikunja', 'projects'],
    queryFn: () => pluginCtx.rest('/projects'),
    refetchOnWindowFocus: false
  })

  // Load tasks for selected project.
  const { data: tasks, isLoading: tasksLoading, refetch: refetchTasks } = useQuery({
    queryKey: ['vikunja', 'tasks', selectedProject ? selectedProject.id : null],
    queryFn: () => (selectedProject ? pluginCtx.rest('/projects/' + String(selectedProject.id) + '/tasks') : Promise.resolve([])),
    enabled: !!selectedProject,
    refetchOnWindowFocus: false
  })

  function toggleTaskDone(task) {
    pluginCtx
      .rest('/tasks/' + String(task.id), {
        method: 'POST',
        body: JSON.stringify({ done: !task.done })
      })
      .then(() => refetchTasks())
  }

  // Top-level tasks only for the main list; subtasks rendered nested.
  const topTasks = useMemo(() => {
    if (!tasks) return []
    let list = Array.isArray(tasks) ? tasks : [tasks]
    const q = searchQuery.trim().toLowerCase()
    if (q) list = list.filter((t) => t.title && String(t.title).toLowerCase().includes(q))
    else if (filter === 'open') list = list.filter((t) => !t.done)
    else if (filter === 'done') list = list.filter((t) => t.done)

    return list
  }, [tasks, filter, searchQuery])

  const subtaskFilter = (st) => {
    if (searchQuery.trim()) {
      return st.title && String(st.title).toLowerCase().includes(searchQuery.trim().toLowerCase())
    }
    if (filter === 'open') return !st.done
    if (filter === 'done') return st.done
    return true
  }

  // --- Loading / error states -------------------------------------------
  if (projectsLoading) {
    return jsx(
      'div',
      { className: 'p-6 text-sm text-ui-text-tertiary', children: 'Loading projects…' }
    )
  }
  if (!projects || !Array.isArray(projects)) {
    return jsx(
      'div',
      {
        className: 'p-6 text-sm text-ui-danger',
        children: (projects && projects.error) || 'Failed to load Vikunja projects'
      }
    )
  }

  // --- Sidebar -----------------------------------------------------------
  const sidebar = jsxs(
    'div',
    {
      className: 'flex flex-col w-56 shrink-0 border-r border-ui-stroke-secondary bg-ui-bg-secondary',
      children: [
        jsx('input', {
          type: 'text',
          placeholder: 'Search tasks…',
          value: searchQuery,
          onInput: (e) => setSearchQuery(e.target.value),
          className:
            'm-2 mb-0 px-2 py-1 text-xs rounded border border-ui-stroke-secondary bg-ui-bg-primary text-ui-text-primary placeholder:text-ui-text-tertiary'
        }),
        jsx(
          'div',
          {
            className: 'flex-1 overflow-y-auto p-1.5 space-y-0.5',
            children: projects.map((project) =>
              jsx(
                'button',
                {
                  key: project.id,
                  type: 'button',
                  onClick: () => setSelectedProject(project),
                  className:
                    'w-full flex items-center gap-2 px-2 py-1.5 text-sm rounded transition-colors text-left ' +
                    (selectedProject && selectedProject.id === project.id
                      ? 'bg-ui-accent/10 text-ui-text-primary'
                      : 'text-ui-text-secondary hover:bg-ui-action-hover') ,
                  children: jsxs('div', {
                    className: 'flex items-center gap-2 min-w-0 flex-1',
                    children: [
                      jsx('span', {
                        className: 'w-2.5 h-2.5 rounded-full shrink-0',
                        style: { backgroundColor: project.hex_color || '#6b7280' }
                      }),
                      jsx('span', { className: 'truncate flex-1', children: project.title }),
                      project.is_favorite &&
                        jsx('span', {
                          title: 'favorite',
                          className: 'text-xs text-ui-accent shrink-0',
                          children: '\u2605'
                        })
                    ]
                  })
                }
              )
            )
          }
        )
      ]
    }
  )

  // --- Main content ------------------------------------------------------
  const main = jsxs(
    'div',
    {
      className: 'flex flex-col flex-1 min-w-0',
      children: [
        selectedProject && (
          jsx(
            'div',
            {
              className: 'px-4 py-3 border-b border-ui-stroke-secondary',
              children: jsxs('div', {
                className: 'flex items-center gap-2 min-w-0',
                children: [
                  selectedProject.hex_color &&
                    jsx('span', {
                      className: 'w-3 h-3 rounded-full shrink-0',
                      style: { backgroundColor: selectedProject.hex_color }
                    }),
                  jsx(
                    'h2',
                    { className: 'text-base font-semibold text-ui-text-primary truncate', children: selectedProject.title }
                  )
                ]
              })
            }
          )
        ),
        jsx(
          'div',
          {
            className: 'flex gap-1 px-4 py-2 border-b border-ui-stroke-secondary',
            children: ['all', 'open', 'done'].map((f) =>
              jsx(
                'button',
                {
                  key: f,
                  type: 'button',
                  onClick: () => setFilter(f),
                  className:
                    'px-2.5 py-1 text-xs font-medium rounded transition-colors ' +
                    (filter === f
                      ? 'bg-ui-accent/20 text-ui-text-primary'
                      : 'text-ui-text-tertiary hover:bg-ui-action-hover'),
                  children: f.charAt(0).toUpperCase() + f.slice(1)
                }
              )
            )
          }
        ),
        jsx(
          'div',
          {
            className: 'flex-1 overflow-y-auto p-2 space-y-1',
            children: !selectedProject ? (
              jsx('div', {
                className: 'p-6 text-center text-sm text-ui-text-tertiary',
                children: 'Select a project'
              })
            ) : tasksLoading ? (
              jsx('div', { className: 'p-4 text-sm text-ui-text-tertiary', children: 'Loading tasks…' })
            ) : topTasks.length === 0 ? (
              jsx('div', {
                className: 'p-6 text-center text-sm text-ui-text-tertiary',
                children: filter === 'open' ? 'No open tasks' : filter === 'done' ? 'No completed tasks' : 'No tasks found'
              })
            ) : (
              topTasks.map((task) => {
                const subs = (task.related_tasks?.subtask || []).filter(subtaskFilter)
                return jsxs(
                  'div',
                  {
                    key: task.id,
                    children: [
                      jsx(TaskItem, {
                        task: { ...task, _depth: 0 },
                        onToggle: toggleTaskDone,
                        expanded: expandedTasks.has(task.id),
                        onExpand: toggleExpand
                      }),
                      expandedTasks.has(task.id) && subs.length > 0 && (
                        jsx(
                          'div',
                          {
                            className: 'ml-5 border-l border-ui-stroke-secondary pl-1 space-y-1',
                            children: subs.map((st) =>
                              jsx(TaskItem, { task: { ...st, _depth: 1 }, onToggle: toggleTaskDone })
                            )
                          }
                        )
                      )
                    ]
                  }
                )
              })
            )
          }
        )
      ]
    }
  )

  return jsxs(
    'div',
    { className: 'flex h-full min-h-0 bg-ui-bg-primary text-ui-text-primary', children: [sidebar, main] }
  )
}

// ---------------------------------------------------------------------------
// Plugin definition
// ---------------------------------------------------------------------------
export default {
  id: 'vikunja',
  name: 'Vikunja Dashboard',
  description: 'Browse Vikunja projects and tasks with their status',
  defaultEnabled: true,

  register(ctx) {
    pluginCtx = ctx

    // Main pane.
    ctx.register({
      id: 'pane',
      area: 'panes',
      title: 'Vikunja',
      data: { placement: 'right', width: '500px' },
      render: () => jsx(VikunjaPage, {})
    })

    // Palette command.
    ctx.register({
      id: 'open',
      area: PALETTE_AREA,
      data: {
        id: 'vikunja.open',
        label: 'Vikunja: Open Dashboard',
        keywords: ['vikunja', 'project', 'task', 'kanban'],
        run: () => host.navigate('/vikunja/pane')
      }
    })
  }
}
