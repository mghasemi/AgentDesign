/**
 * Vikunja Dashboard — Hermes desktop plugin for managing Vikunja projects and tasks.
 *
 * Provides a UI to browse Vikunja projects and view tasks with their status.
 * Backend: dashboard/plugin_api.py (list projects, list tasks)
 */

import { useState, useMemo } from 'react'
import { host, PALETTE_AREA, useQuery } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'
import { ChevronDown, Circle, Star, CheckCircle } from 'lucide-react'

// Store plugin context globally
let pluginCtx = null

// Flatten task hierarchy to a flat list
function flattenTasks(taskList) {
  const result = []
  function walk(tasks, depth = 0) {
    if (!tasks) return
    for (const task of tasks) {
      result.push({ ...task, _depth: depth, _hasSubtasks: task.related_tasks?.subtask?.length > 0 })
      walk(task.related_tasks?.subtask, depth + 1)
    }
  }
  walk(taskList)
  return result
}

// Color utilities
function hexToRgb(hex) {
  const result = /^#?([a-f\\d]{2})([a-f\\d]{2})([a-f\\d]{2})$/i.exec(hex || '')
  return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '0, 0, 0'
}

// Priority color
function getPriorityColor(priority) {
  if (priority === undefined || priority === 0) return 'var(--ui-text-tertiary)'
  if (priority >= 4) return 'var(--ui-danger)'
  if (priority === 3) return 'var(--ui-warning)'
  if (priority === 2) return 'var(--ui-accent)'
  return 'var(--ui-success)'
}

// Task item component
function TaskItem({ task, onToggle, filter }) {
  const hasSubtasks = task.related_tasks?.subtask?.length > 0
  const openSubtasks = task.related_tasks?.subtask?.filter(st => !st.done) || []
  const showChildren = expandedTasks.has(task.id) && hasSubtasks
  
  // Filter subtasks based on filter
  const filteredChildren = task.related_tasks?.subtask?.filter(st => {
    if (filter === 'open') return !st.done
    if (filter === 'done') return st.done
    return true
  }) || []

  return jsxs('div', {
    className: 'flex items-start gap-2 px-2 py-1 hover:bg-ui-action-hover',
    children: [
      jsx('div', {
        className: 'flex items-center gap-1.5 pt-0.5',
        children: task._depth > 0 && (
          jsx(ChevronDown, {
            className: `h-3.5 w-3.5 text-ui-text-tertiary transition-transform ${showChildren ? 'rotate-180' : ''}`,
            style: { transformOrigin: 'center' }
          })
        )
      }),
      jsx('button', {
        type: 'button',
        className: 'flex items-center gap-2 px-2 py-0.5 text-sm rounded hover:bg-ui-action-hover text-left',
        onClick: () => onToggle(task),
        children: jsxs('div', {
          className: 'flex-1 min-w-0 flex items-center gap-2',
          children: [
            jsx('div', {
              className: 'flex items-center gap-1.5',
              children: [
                task.done && jsx(CheckCircle, { className: 'h-4 w-4 text-ui-success shrink-0' }),
                !task.done && jsx(Circle, { className: 'h-4 w-4 text-ui-text-tertiary shrink-0' }),
                jsx('span', {
                  className: 'truncate',
                  children: task.title
                }),
                task.due_date && !task.done && jsx('span', {
                  className: 'text-xs text-ui-text-tertiary',
                  children: new Date(task.due_date).toLocaleDateString()
                }),
                task.priority && task.priority > 0 && jsx(Star, {
                  className: 'h-3 w-3 shrink-0',
                  style: { color: getPriorityColor(task.priority) }
                })
              ]
            }),
            task.labels && task.labels.length > 0 && jsx('div', {
              className: 'flex gap-1 mt-0.5 flex-wrap',
              children: task.labels.map(label => 
                jsx('span', {
                  key: label.id,
                  className: 'px-1.5 py-0.5 text-xs rounded',
                  style: {
                    backgroundColor: `rgba(${hexToRgb(label.hex_color)}, 0.15)`,
                    color: `rgb(${hexToRgb(label.hex_color)})`,
                    borderColor: `rgba(${hexToRgb(label.hex_color)}, 0.3)`
                  },
                  children: label.title
                })
              )
            })
          ]
        })
      }),
      hasSubtasks && jsx('span', {
        className: 'text-xs text-ui-text-tertiary ml-auto',
        children: `${openSubtasks.length} open`
      })
    ]
  })
}

// Global state
let expandedTasks = new Set()

// Main Vikunja page component
function VikunjaPage() {
  const [selectedProject, setSelectedProject] = useState(null)
  const [filter, setFilter] = useState('open')
  const [searchQuery, setSearchQuery] = useState('')

  // Load projects
  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['vikunja', 'projects'],
    queryFn: () => pluginCtx.rest('/projects'),
    refetchOnWindowFocus: false
  })

  // Load tasks for selected project
  const { data: tasks, isLoading: tasksLoading, refetch: refetchTasks } = useQuery({
    queryKey: ['vikunja', 'tasks', selectedProject?.id],
    queryFn: () => selectedProject ? pluginCtx.rest(`/projects/${selectedProject.id}/tasks`) : Promise.resolve([]),
    enabled: !!selectedProject,
    refetchOnWindowFocus: false
  })

  // Toggle task expanded state
  function toggleExpand(taskId) {
    const newSet = new Set(expandedTasks)
    if (newSet.has(taskId)) {
      newSet.delete(taskId)
    } else {
      newSet.add(taskId)
    }
    expandedTasks = newSet
  }

  // Toggle task done state
  function toggleTaskDone(task) {
    pluginCtx.rest(`/tasks/${task.id}`, {
      method: 'POST',
      body: JSON.stringify({ done: !task.done })
    }).then(() => {
      refetchTasks()
    })
  }

  // Get filtered tasks
  const allTasks = useMemo(() => {
    if (!tasks) return []
    const flatTasks = flattenTasks(tasks).map(t => ({ ...t, _expanded: expandedTasks.has(t.id) }))
    
    // Apply search filter
    let filtered = flatTasks
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(t => t.title.toLowerCase().includes(query))
    }
    
    // Apply status filter
    if (filter === 'open') {
      filtered = filtered.filter(t => !t.done)
    } else if (filter === 'done') {
      filtered = filtered.filter(t => t.done)
    }
    return filtered
  }, [tasks, filter, searchQuery])

  if (projectsLoading) {
    return jsx('div', {
      className: 'p-6',
      children: jsx('div', {
        className: 'text-sm text-ui-text-tertiary',
        children: 'Loading projects...'
      })
    })
  }

  if (!projects) {
    return jsx('div', {
      className: 'p-6',
      children: jsx('div', {
        className: 'text-sm text-ui-text-tertiary',
        children: 'Failed to load projects'
      })
    })
  }

  return jsxs('div', {
    className: 'flex h-full',
    children: [
      // Sidebar - Projects
      jsxs('div', {
        className: 'flex flex-col w-64 border-r border-ui-stroke-secondary bg-ui-bg-secondary',
        children: [
          jsxs('div', {
            className: 'flex items-center gap-2 px-3 py-2 border-b border-ui-stroke-secondary',
            children: [
              jsx('h2', {
                className: 'text-sm font-semibold text-ui-text-primary',
                children: 'PROJECTS'
              }),
              jsx('input', {
                type: 'text',
                placeholder: 'Search...',
                className: 'flex-1 text-xs px-1.5 py-0.5 border border-ui-stroke-secondary rounded bg-ui-bg-primary text-ui-text-primary placeholder:text-ui-text-tertiary',
                value: searchQuery,
                onInput: (e) => setSearchQuery(e.target.value)
              })
            ]
          }),
          jsx('div', {
            className: 'flex-1 overflow-y-auto',
            children: projects.map(project => 
              jsx('button', {
                key: project.id,
                type: 'button',
                className: `flex items-center gap-2 px-3 py-1.5 text-sm w-full text-left rounded transition-colors ${
                  selectedProject?.id === project.id 
                    ? 'bg-ui-action-secondary' 
                    : 'hover:bg-ui-action-hover'
                }`,
                onClick: () => setSelectedProject(project),
                children: jsxs('div', {
                  className: 'flex items-center gap-2',
                  children: [
                    jsx('div', {
                      className: 'w-3 h-3 rounded-full',
                      style: { backgroundColor: project.hex_color || '#6b7280' }
                    }),
                    jsxs('div', {
                      className: 'flex-1 min-w-0',
                      children: [
                        project.title,
                        project.is_favorite && jsx(Star, {
                          className: 'h-3 w-3 text-ui-accent ml-1 shrink-0'
                        })
                      ]
                    }),
                    project.is_archived && jsx('span', {
                      className: 'text-xs text-ui-text-tertiary',
                      children: 'ARCH'
                    })
                  ]
                })
              })
            )
          })
        ]
      }),
      // Main content
      jsxs('div', {
        className: 'flex flex-col flex-1',
        children: [
          // Project header
          selectedProject && jsxs('div', {
            className: 'flex items-center justify-between px-4 py-3 border-b border-ui-stroke-secondary',
            children: [
              jsx('div', {
                className: 'flex items-center gap-2',
                children: [
                  jsx('div', {
                    className: 'w-4 h-4 rounded-full',
                    style: { backgroundColor: selectedProject.hex_color || '#6b7280' }
                  }),
                  jsx('h2', {
                    className: 'text-lg font-semibold text-ui-text-primary',
                    children: selectedProject.title
                  })
                ]
              }),
              selectedProject.description && jsx('span', {
                className: 'text-sm text-ui-text-tertiary max-w-xs truncate',
                children: selectedProject.description
              })
            ]
          }),
          // Filter tabs
          selectedProject && jsxs('div', {
            className: 'flex gap-1 px-4 py-2 bg-ui-bg-secondary border-b border-ui-stroke-secondary',
            children: ['all', 'open', 'done'].map(f => 
              jsx('button', {
                key: f,
                type: 'button',
                className: `px-3 py-1 text-xs font-medium rounded transition-colors ${
                  filter === f 
                    ? 'bg-ui-accent text-ui-accent-foreground' 
                    : 'text-ui-text-tertiary hover:bg-ui-action-hover hover:text-ui-text-primary'
                }`,
                onClick: () => setFilter(f),
                children: f.charAt(0).toUpperCase() + f.slice(1)
              })
            )
          }),
          // Tasks list
          jsx('div', {
            className: 'flex-1 overflow-y-auto',
            children: tasksLoading 
              ? jsx('div', {
                  className: 'p-4 text-sm text-ui-text-tertiary',
                  children: 'Loading tasks...'
                })
              : allTasks.length === 0
                ? jsx('div', {
                    className: 'p-8 text-center text-sm text-ui-text-tertiary',
                    children: filter === 'open' 
                      ? 'No open tasks' 
                      : filter === 'done' 
                        ? 'No completed tasks'
                        : 'No tasks found'
                  })
                : jsxs('div', {
                    className: 'divide-y divide-ui-stroke-secondary',
                    children: allTasks.map(task => 
                      jsx('div', {
                        key: task.id,
                        children: jsxs('div', {
                          children: [
                            jsx(TaskItem, {
                              task,
                              onToggle: (t) => {
                                if (!t.done) {
                                  toggleTaskDone(t)
                                } else {
                                  toggleExpand(t.id)
                                }
                              },
                              filter
                            }),
                            // Show subtasks on next line
                            expandedTasks.has(task.id) && task.related_tasks?.subtask && (
                              jsxs('div', {
                                className: 'pl-4 border-l border-ui-stroke-secondary',
                                children: task.related_tasks.subtask
                                  .filter(st => {
                                    if (filter === 'open') return !st.done
                                    if (filter === 'done') return st.done
                                    return true
                                  })
                                  .map(st => 
                                    jsx(TaskItem, {
                                      key: st.id,
                                      task: { ...st, _depth: 1 },
                                      onToggle: () => toggleTaskDone(st),
                                      filter
                                    })
                                  )
                              })
                            )
                          ]
                        })
                      })
                    )
                  })
          })
        ]
      })
    ]
  })
}

// Plugin definition
export default {
  id: 'vikunja',
  name: 'Vikunja Dashboard',
  description: 'Browse Vikunja projects and tasks with their status',
  defaultEnabled: true,

  register(ctx) {
    pluginCtx = ctx

    // Main pane
    ctx.register({
      id: 'pane',
      area: 'panes',
      title: 'Vikunja',
      data: { placement: 'right', width: '500px' },
      render: () => jsx(VikunjaPage, {})
    })

    // Palette command
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