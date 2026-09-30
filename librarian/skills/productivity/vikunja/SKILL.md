---
name: vikunja
description: "Use when working with Vikunja projects or tasks, especially when asked to show my projects, list projects, read project details, show my tasks, list tasks, read task details, create a project, update a project, create a task, add a task, create a todo, update a task, complete a task, or log a task."
---

# Vikunja Access Skill
Skill to read and write projects and tasks in a Vikunja server.

## Usage
Execute `vikunja_tool.py` from this skill folder.

### List all projects
```bash
python3 {baseDir}/vikunja_tool.py projects list
```

### Search projects
```bash
python3 {baseDir}/vikunja_tool.py projects search --query "research"
```

### Get one project by title
```bash
python3 {baseDir}/vikunja_tool.py projects get-by-title --title "Research Backlog"
```

### Create a project
```bash
python3 {baseDir}/vikunja_tool.py projects create --title "Research Backlog"
```

### Update a project
```bash
python3 {baseDir}/vikunja_tool.py projects update 12 --title "Research Roadmap"
```

### List all tasks
```bash
python3 {baseDir}/vikunja_tool.py tasks list
```

### List all overdue tasks
```bash
python3 {baseDir}/vikunja_tool.py tasks overdue
```

To scope overdue tasks to one project:

```bash
python3 {baseDir}/vikunja_tool.py tasks overdue --project-id 12
```

### Search tasks
```bash
python3 {baseDir}/vikunja_tool.py tasks search --query "summary"
```

### List tasks in a project
```bash
python3 {baseDir}/vikunja_tool.py tasks list --project-id 12
```

### Create a task
```bash
python3 {baseDir}/vikunja_tool.py tasks create --project-id 12 --title "Write summary"
```

Date-only due dates are accepted and normalized automatically:

```bash
python3 {baseDir}/vikunja_tool.py tasks create --project-id 12 --title "Write summary" --due-date 2026-03-22
```

Priority and labels are supported directly:

```bash
python3 {baseDir}/vikunja_tool.py tasks create --project-id 12 --title "Write summary" --priority 4 --labels "writing,review"
```

Subtask can be created under an existing parent task:

```bash
python3 {baseDir}/vikunja_tool.py tasks create --project-id 12 --title "Extract theorem list" --parent-task-id 45
```

Delete a task (verified working copy, 2026-09-06):

```bash
python3 {baseDir}/vikunja_tool.py tasks delete <task_id>
```

### Log a task (alias for create)
```bash
python3 {baseDir}/vikunja_tool.py tasks log --project-id 12 --title "Capture meeting notes"
```

### Update a task
```bash
python3 {baseDir}/vikunja_tool.py tasks update 45 --done true
```

Task updates preserve existing title, description, due date, project, and priority unless you explicitly override them:

```bash
python3 {baseDir}/vikunja_tool.py tasks update 45 --priority 5
python3 {baseDir}/vikunja_tool.py tasks update 45 --labels "theory,review"
```

### Complete a task
```bash
python3 {baseDir}/vikunja_tool.py tasks complete 45
```

### Dry run a write request
```bash
python3 {baseDir}/vikunja_tool.py --dry-run tasks create --project-id 12 --title "Draft notes"
```

## Pitfalls & Workarounds

### `tasks delete` exists in the current wrapper (verified 2026-09-06)
The skill folder's `vikunja_tool.py` supports `tasks delete <task_id>` (argparse subparser + dispatch to `DELETE /api/v1/tasks/{id}`). The earlier "no delete" note referred to an older copy; REST fallback still works if a stale copy is in use:
```bash
curl -X DELETE "http://YOUR-HOST:3456/api/v1/tasks/{task_id}" \
  --header "Authorization: Bearer $VIKUNJA_TOKEN"
```

### Batch creation via `subprocess.run` with argv list, not shell string
When looping task creations from Python, pass an **argv list** (`["python3", TOOL, "tasks", "create", "--project-id", pid, "--title", title]`) — never build a quoted shell string. The wrapper's `--parent-task-id` is `type=int`, so passing a tuple (e.g. the `(id, title)` return of a helper) fails argparse with rc=2 and a usage dump instead of an API error. Helper pattern: `mk()` returns just the int id; parse stdout JSON directly (`tasks create` prints the task object, no `data` wrapper).

### Subtask relations verified via `related_tasks.parenttask` (not `.relations`)
The Vikunja API stores parent-child relationships under `related_tasks.parenttask` on the **parent** task object, not as a `parent_task_id` field. When verifying that subtasks were created correctly:
```bash
# Check which tasks are children of task 373 (Phase 1)
python3 {VIKUNJA_TOOL} tasks get 373 | jq '.related_tasks.parenttask[].id'
# Returns: [384, 385, 386]
```

### Subtask relation orientation — verified against the server (2026-08-18)
Server semantics for `PUT /api/v1/tasks/{task_id}/relations` with `relation_kind: "subtask"`:
- `task_id` = the **subtask (child)**
- `other_task_id` = the **parent**

The active `vikunja_tool.py` (this skill folder) already sends this orientation:
`create_task_relation(child_id, parent_id)` → `{task_id: child_id, other_task_id: parent_id}`.
Verified end-to-end on 2026-08-18: `tasks create --parent-task-id P` puts the new child in the parent's `related_tasks.parenttask`.

**Do NOT swap the orientation.** Sending `task_id=parent, other_task_id=child` tells the server the parent is a subtask of the child: if the correct relation already exists the server rejects it with HTTP 409 `{"code": 4023, "message": "This task relation would create a cycle."}`; if it doesn't exist yet, it silently creates the INVERTED hierarchy. The workaround "create without `--parent-task-id`, then apply the relation manually" is therefore unnecessary — `--parent-task-id` works as documented.

Verify a subtask link:
```bash
python3 {baseDir}/vikunja_tool.py tasks get {parent_id} | jq '.related_tasks.parenttask[].id'
```

### Shell quoting hell with complex descriptions
When task titles or descriptions contain quotes, apostrophes (`→`, `…`, math notation), inline shell commands fail. **Solution**: Write a Python script that calls the tool via `subprocess.run()`:
```python
#!/usr/bin/env python3
import subprocess
VIKUNJA_TOOL = "/path/to/vikunja_tool.py"
subprocess.run([f"python3", VIKUNJA_TOOL, "tasks create", 
                f"--project-id 26",
                f'--title "{complex_title}"',
                f'--description "{desc_with_quotes}"'], shell=True)
```

### Token resolution via `.emv` files
The tool loads env vars from `.emv` files by walking up directory tree. If `VIKUNJA_TOKEN` is empty:
```bash
find /home/YOUR-USER -maxdepth 4 -name ".emv" | xargs cat
```

### Batch operations for task hierarchies
For creating many tasks (e.g., full hierarchy), write a Python script that loops through definitions. Don't inline each `tasks create` call — use the script pattern above with proper JSON parsing:
```python
def mk(project_id, title, desc="", labels=None):
    parts = ["python3", VIKUNJA_TOOL, "tasks create", 
             f"--project-id {project_id}",
             f'--title "{title}"']
    if desc: parts.append(f'--description "{desc}"')
    if labels: parts.append(f'--labels "{",".join(labels)}"')
    
    result = subprocess.run(" ".join(parts), shell=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return data["data"]["id"]
```

### `complete` doesn't hide from active view
The `tasks complete` action marks tasks internally but they still appear in `tasks list`. To filter:
```bash
python3 {VIKUNJA_TOOL} tasks list --project-id 26 | jq '.[] | select(.done == false)'
```
