# Vikunja Dashboard Plugin

A Hermes desktop plugin for browsing Vikunja projects and tasks.

## Features

- **Project List**: View all Vikunja projects in a sidebar
- **Task Browser**: See all tasks for a selected project with their status
- **Subtasks**: Expand/collapse tasks with nested subtasks
- **Status Tracking**: Visual indicators for completed (✓) vs open (○) tasks
- **Labels**: Color-coded labels on tasks
- **Priority**: Visual priority indicators (1-5 scale)
- **Due Dates**: Show due dates on open tasks
- **Search**: Filter projects and tasks by title
- **Toggle Complete**: Click a task to toggle its done status

## Installation

1. Place the plugin folder in `$HERMES_HOME/plugins/vikunja/`
2. Enable the plugin in your profile configuration
3. Set the `VIKUNJA_TOKEN` in the `dashboard/.emv` file (or profile config)
4. Set `VIKUNJA_URL` to your Vikunja server URL

## Configuration

The plugin reads the Vikunja token from `dashboard/.emv` in the same directory.

```bash
# Example .emv file content
VIKUNJA_URL=http://YOUR-HOST:3456
VIKUNJA_TOKEN=tk_your_api_token_here
```

## Usage

- **Palette Command**: `Vikunja: Open Dashboard` (or `vikunja.open`)
- **UI**: Opens as a right-side pane from the status bar
- **Keyboard**: Use the palette to navigate to the Vikunja pane

## Architecture

```
vikunja/
├── plugin.yaml          # Plugin metadata
├── manifest.json        # API entry point
├── dashboard/
│   ├── .emv            # Environment variables (URL, token)
│   └── plugin_api.py   # FastAPI backend routes
└── desktop/
    └── plugin.tsx      # React frontend component
```