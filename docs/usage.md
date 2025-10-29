# Usage Guide

This guide provides comprehensive instructions on how to use the MCP Server for Google Sheets Kanban with various MCP clients.

## Table of Contents

- [Connecting to MCP Clients](#connecting-to-mcp-clients)
- [Available Tools](#available-tools)
- [Tool Usage Examples](#tool-usage-examples)
- [Common Workflows](#common-workflows)
- [Best Practices](#best-practices)

## Connecting to MCP Clients

### Claude Desktop

1. Locate your Claude Desktop configuration file:
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. Add the server configuration:

```json
{
  "mcpServers": {
    "kanban-sheets": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/mcp-server-sheets", "run", "main.py"]
    }
  }
}
```

**Important:** Replace `/absolute/path/to/mcp-server-sheets` with the actual absolute path to your project.

**Windows Example:**
```json
{
  "mcpServers": {
    "kanban-sheets": {
      "command": "uv",
      "args": ["--directory", "C:\\Users\\YourName\\Projects\\mcp-server-sheets", "run", "main.py"]
    }
  }
}
```

**macOS/Linux Example:**
```json
{
  "mcpServers": {
    "kanban-sheets": {
      "command": "uv",
      "args": ["--directory", "/home/username/projects/mcp-server-sheets", "run", "main.py"]
    }
  }
}
```

3. Restart Claude Desktop

4. Verify the connection by checking if the kanban-sheets tools appear in the available tools list

### Other MCP Clients

For other MCP clients that support the Model Context Protocol, configure them to connect via STDIO:

```bash
uv --directory /path/to/mcp-server-sheets run main.py
```

## Available Tools

The server provides 6 tools for managing your Kanban tasks:

| Tool | Description |
|------|-------------|
| `list_tasks` | List and search tasks with advanced filters and pagination |
| `add_task` | Add a new task to the spreadsheet |
| `update_task` | Update an existing task by Task ID |
| `batch_add_tasks` | Add multiple tasks in one operation |
| `batch_update_tasks` | Update multiple tasks in one operation |
| `get_valid_configs` | Get valid values for Status and Priority fields |

## Tool Usage Examples

### 1. get_valid_configs

Get the valid values for Status and Priority fields.

**When to use:**
- Before adding or updating tasks to ensure you use valid values
- When you're unsure what status or priority values are available

**Example Request:**
```
Use the get_valid_configs tool
```

**Response:**
```json
{
  "valid_task_status": [
    "Todo",
    "Em Desenvolvimento",
    "Impedido",
    "Concluído",
    "Cancelado",
    "Não Relacionado",
    "Pausado"
  ],
  "valid_task_priorities": [
    "Baixa",
    "Normal",
    "Alta",
    "Urgente"
  ]
}
```

---

### 2. list_tasks

List and search tasks with powerful filtering and pagination.

#### Example 2.1: List All Tasks (Simple)

**Request:**
```
List all tasks from the Kanban board
```

**Response:** Array of all tasks

#### Example 2.2: List with Pagination

**Natural Language:**
```
Show me the first page of tasks, 20 per page
```

**Result:** Returns paginated response with:
- First 20 tasks
- Total count
- Page metadata (has_next, has_previous, total_pages)

#### Example 2.3: Filter by Priority

**Natural Language:**
```
Show me all urgent and high priority tasks
```

**Equivalent JSON:**
```json
{
  "filters": {
    "prioridade": ["Urgente", "Alta"]
  }
}
```

#### Example 2.4: Filter by Status

**Natural Language:**
```
Show me all tasks that are in development or blocked
```

**Equivalent JSON:**
```json
{
  "filters": {
    "status": ["Em Desenvolvimento", "Impedido"]
  }
}
```

#### Example 2.5: Search by Text

**Natural Language:**
```
Find all tasks related to "API implementation"
```

**Equivalent JSON:**
```json
{
  "filters": {
    "texto_busca": "API implementation"
  }
}
```

**Note:** Text search looks in both Descrição and Detalhado fields (case-insensitive)

#### Example 2.6: Filter by Project

**Natural Language:**
```
Show me all tasks for the "MCP Server" project
```

**Equivalent JSON:**
```json
{
  "filters": {
    "projeto": "MCP Server"
  }
}
```

#### Example 2.7: Filter by Context

**Natural Language:**
```
Show me all Backend tasks
```

**Equivalent JSON:**
```json
{
  "filters": {
    "contexto": "Backend"
  }
}
```

#### Example 2.8: Filter by Sprint

**Natural Language:**
```
Show me tasks in Sprint 3
```

**Equivalent JSON:**
```json
{
  "filters": {
    "sprint": "Sprint 3"
  }
}
```

#### Example 2.9: Find Specific Task by ID

**Natural Language:**
```
Find task TASK-123
```

**Equivalent JSON:**
```json
{
  "filters": {
    "task_id": "TASK-123"
  }
}
```

#### Example 2.10: Combine Multiple Filters

**Natural Language:**
```
Show me high priority Backend tasks that are in Todo or In Development status, from the MCP Server project, with pagination of 25 items per page
```

**Equivalent JSON:**
```json
{
  "filters": {
    "prioridade": ["Alta"],
    "status": ["Todo", "Em Desenvolvimento"],
    "contexto": "Backend",
    "projeto": "MCP Server"
  },
  "pagination": {
    "page": 1,
    "page_size": 25
  }
}
```

---

### 3. add_task

Add a single task to the spreadsheet.

#### Example 3.1: Add a Complete Task

**Natural Language:**
```
Add a new task:
- Project: MCP Server Sheets
- Task ID: TASK-101
- Context: Backend
- Description: Implement batch operations
- Priority: Alta
- Status: Todo
- Sprint: Sprint 2
- Detailed: Add support for batch adding and updating tasks using Google Sheets batchUpdate API
```

**Result:** Task is added with auto-generated creation date

#### Example 3.2: Add a Minimal Task

**Natural Language:**
```
Add a task with ID TASK-102 for the MCP Server Sheets project, context Frontend, description "Update UI for task filters", priority Normal, status Todo
```

**Result:** Task is added with only required fields, optional fields left empty

#### Example 3.3: Add a Subtask

**Natural Language:**
```
Add a subtask TASK-102-A under parent task TASK-102, project MCP Server Sheets, context Frontend, description "Create filter component", priority Normal, status Todo
```

**Equivalent JSON:**
```json
{
  "task": {
    "project": "MCP Server Sheets",
    "task_id": "TASK-102-A",
    "task_id_root": "TASK-102",
    "contexto": "Frontend",
    "descricao": "Create filter component",
    "prioridade": "Normal",
    "status": "Todo",
    "sprint": "",
    "detalhado": ""
  }
}
```

---

### 4. update_task

Update an existing task by its Task ID.

#### Example 4.1: Update Status

**Natural Language:**
```
Update task TASK-101 to status "Em Desenvolvimento"
```

**Result:** Task status is updated. If changed to a final status (Concluído, Cancelado, Não Relacionado), the completion date is automatically set.

#### Example 4.2: Update Priority

**Natural Language:**
```
Change the priority of task TASK-102 to Urgente
```

#### Example 4.3: Update Multiple Fields

**Natural Language:**
```
Update task TASK-101:
- Status: Concluído
- Detailed description: Batch operations implemented successfully using Google Sheets batchUpdate API. Includes comprehensive error handling.
```

**Result:** Both fields are updated, and since status is "Concluído", the completion date is automatically set.

#### Example 4.4: Move Task to Sprint

**Natural Language:**
```
Move task TASK-103 to Sprint 3
```

#### Example 4.5: Add Details to Task

**Natural Language:**
```
Update task TASK-104 with detailed description: "Implement JWT authentication with refresh tokens. Use bcrypt for password hashing. Add rate limiting to login endpoint."
```

---

### 5. batch_add_tasks

Add multiple tasks in a single operation for better performance.

#### Example 5.1: Add Multiple Tasks

**Natural Language:**
```
Add these tasks to the MCP Server Sheets project:

1. Task ID: TASK-201, Context: Backend, Description: "Setup database", Priority: Alta, Status: Todo
2. Task ID: TASK-202, Context: Backend, Description: "Create API endpoints", Priority: Alta, Status: Todo
3. Task ID: TASK-203, Context: Frontend, Description: "Build task list UI", Priority: Normal, Status: Todo
4. Task ID: TASK-204, Context: DevOps, Description: "Setup CI/CD", Priority: Normal, Status: Todo
```

**Equivalent JSON:**
```json
{
  "batch": {
    "tasks": [
      {
        "project": "MCP Server Sheets",
        "task_id": "TASK-201",
        "contexto": "Backend",
        "descricao": "Setup database",
        "prioridade": "Alta",
        "status": "Todo",
        "task_id_root": "",
        "sprint": "",
        "detalhado": ""
      },
      {
        "project": "MCP Server Sheets",
        "task_id": "TASK-202",
        "contexto": "Backend",
        "descricao": "Create API endpoints",
        "prioridade": "Alta",
        "status": "Todo",
        "task_id_root": "",
        "sprint": "",
        "detalhado": ""
      },
      {
        "project": "MCP Server Sheets",
        "task_id": "TASK-203",
        "contexto": "Frontend",
        "descricao": "Build task list UI",
        "prioridade": "Normal",
        "status": "Todo",
        "task_id_root": "",
        "sprint": "",
        "detalhado": ""
      },
      {
        "project": "MCP Server Sheets",
        "task_id": "TASK-204",
        "contexto": "DevOps",
        "descricao": "Setup CI/CD",
        "prioridade": "Normal",
        "status": "Todo",
        "task_id_root": "",
        "sprint": "",
        "detalhado": ""
      }
    ]
  }
}
```

**Response:**
```json
{
  "success_count": 4,
  "error_count": 0,
  "details": [
    {
      "task_id": "TASK-201",
      "status": "success",
      "message": "Tarefa adicionada com sucesso"
    },
    {
      "task_id": "TASK-202",
      "status": "success",
      "message": "Tarefa adicionada com sucesso"
    },
    {
      "task_id": "TASK-203",
      "status": "success",
      "message": "Tarefa adicionada com sucesso"
    },
    {
      "task_id": "TASK-204",
      "status": "success",
      "message": "Tarefa adicionada com sucesso"
    }
  ]
}
```

---

### 6. batch_update_tasks

Update multiple tasks in a single operation.

#### Example 6.1: Update Multiple Task Statuses

**Natural Language:**
```
Update these tasks to "Concluído" status:
- TASK-201
- TASK-202
- TASK-203
```

**Equivalent JSON:**
```json
{
  "batch": {
    "updates": [
      {
        "task_id": "TASK-201",
        "fields": {"status": "Concluído"}
      },
      {
        "task_id": "TASK-202",
        "fields": {"status": "Concluído"}
      },
      {
        "task_id": "TASK-203",
        "fields": {"status": "Concluído"}
      }
    ]
  }
}
```

**Response:**
```json
{
  "success_count": 3,
  "error_count": 0,
  "details": [
    {
      "task_id": "TASK-201",
      "status": "success",
      "message": "Tarefa atualizada com sucesso"
    },
    {
      "task_id": "TASK-202",
      "status": "success",
      "message": "Tarefa atualizada com sucesso"
    },
    {
      "task_id": "TASK-203",
      "status": "success",
      "message": "Tarefa atualizada com sucesso"
    }
  ]
}
```

#### Example 6.2: Move Multiple Tasks to Sprint

**Natural Language:**
```
Move tasks TASK-204, TASK-205, and TASK-206 to Sprint 4
```

#### Example 6.3: Bulk Priority Update

**Natural Language:**
```
Change priority to Urgente for tasks TASK-210, TASK-211, and TASK-212
```

---

## Common Workflows

### Workflow 1: Sprint Planning

1. **List all unassigned tasks:**
   ```
   Show me all tasks with no sprint assigned
   ```

2. **Review and prioritize:**
   ```
   Show me all Todo tasks sorted by priority
   ```

3. **Assign tasks to sprint:**
   ```
   Move tasks TASK-101, TASK-102, TASK-103 to Sprint 3
   ```

### Workflow 2: Daily Standup

1. **Check in-progress tasks:**
   ```
   Show me all tasks in "Em Desenvolvimento" status
   ```

2. **Check blocked tasks:**
   ```
   Show me all tasks with "Impedido" status
   ```

3. **Update task status:**
   ```
   Update task TASK-105 to status "Concluído"
   ```

### Workflow 3: Project Overview

1. **Get project statistics:**
   ```
   Show me all tasks for the "MCP Server" project
   ```

2. **Check urgent items:**
   ```
   Show me all urgent priority tasks for the MCP Server project that are not completed
   ```

3. **Review completed work:**
   ```
   Show me all completed tasks from Sprint 2
   ```

### Workflow 4: Task Breakdown

1. **Create parent task:**
   ```
   Add task TASK-300, project "MCP Server", context "Backend", description "Implement authentication system", priority Alta, status Todo
   ```

2. **Add subtasks:**
   ```
   Add these subtasks under TASK-300:
   - TASK-300-A: Setup JWT library
   - TASK-300-B: Create login endpoint
   - TASK-300-C: Create registration endpoint
   - TASK-300-D: Implement password hashing
   ```

3. **Track progress:**
   ```
   Show me all tasks with task_id_root "TASK-300"
   ```

### Workflow 5: Bug Triage

1. **Add multiple bugs:**
   ```
   Use batch_add_tasks to add these bug tasks:
   - TASK-401: Login fails on mobile
   - TASK-402: Data not saving correctly
   - TASK-403: UI alignment issue
   All with priority "Alta" and status "Todo"
   ```

2. **Assign priorities:**
   ```
   Update task TASK-401 to priority Urgente
   ```

3. **Track bug fixes:**
   ```
   Show me all tasks with context "Bug Fix" that are not completed
   ```

## Best Practices

### Task IDs

- Use a consistent naming scheme (e.g., `TASK-001`, `PROJ-BACKEND-001`)
- For subtasks, use hierarchical IDs (e.g., `TASK-001-A`, `TASK-001-B`)
- Keep IDs unique across your entire project

### Project Names

- Use consistent project names across all tasks
- Consider using the same case (e.g., "MCP Server Sheets" vs "mcp server sheets")
- Keep project names descriptive but concise

### Context Usage

- Define standard contexts for your team (e.g., Backend, Frontend, DevOps, Testing, Documentation)
- Use consistent capitalization
- Consider using hierarchical contexts (e.g., "Backend/API", "Backend/Database")

### Descriptions

- Keep "Descrição" (brief description) concise - one line summary
- Use "Detalhado" (detailed description) for implementation details, acceptance criteria, or notes
- Update "Detalhado" as the task progresses with notes or blockers

### Priority Management

- **Urgente**: Critical bugs, blockers, or time-sensitive tasks
- **Alta**: Important features or significant bugs
- **Normal**: Standard tasks and minor improvements
- **Baixa**: Nice-to-have features or minor enhancements

### Status Workflow

Recommended status flow:
```
Todo → Em Desenvolvimento → Concluído
                ↓
            Impedido → Em Desenvolvimento
```

Alternative outcomes:
- **Cancelado**: Task is no longer needed
- **Não Relacionado**: Task was created by mistake or is out of scope
- **Pausado**: Task is on hold temporarily

### Sprint Management

- Use consistent sprint naming (e.g., "Sprint 1", "Sprint 2", "2024-Q1-Sprint1")
- Move tasks to sprints using batch operations for efficiency
- Keep sprint names short and clear

### Using Pagination

- For large projects (100+ tasks), always use pagination
- Recommended page_size: 20-50 for most use cases
- Use filters with pagination to narrow down results

### Batch Operations

- Use batch operations when adding/updating 3+ tasks
- Batch operations are much faster than individual operations
- Check the response details to identify any failed operations

### Text Search

- Text search is case-insensitive
- Searches both brief and detailed descriptions
- Use specific keywords for better results
- Combine with other filters to narrow results

## Tips and Tricks

### Quick Status Updates

For frequently used status updates, you can create simple commands:
```
Mark TASK-105 as done
Move TASK-106 to in development
Block TASK-107
```

### Finding Related Tasks

Use task_id_root to find all subtasks:
```
Show me all subtasks of TASK-300
```

### Project Health Check

Get a quick overview:
```
Show me all high priority tasks that are blocked or paused for the MCP Server project
```

### Sprint Velocity

Track completed work:
```
Show me all completed tasks from Sprint 3
```

### Context Switching

Filter by context to focus on specific areas:
```
Show me all my Backend tasks in Todo or In Development status
```

## Troubleshooting

### Tool Not Found

If the tools don't appear in your MCP client:
1. Check that the server is configured correctly in your client's config file
2. Ensure the path to the project directory is absolute, not relative
3. Restart your MCP client
4. Check the server logs for errors

### Tasks Not Appearing

If list_tasks returns empty or unexpected results:
1. Verify your spreadsheet has data
2. Check that column headers match exactly
3. Ensure filters are using valid values (use `get_valid_configs`)
4. Try listing without filters first

### Update/Add Failures

If tasks fail to add or update:
1. Verify Status and Priority values are valid (use `get_valid_configs`)
2. Check that required fields are provided
3. Ensure Task IDs are unique when adding
4. Verify the service account has edit access to the spreadsheet

### Permission Errors

If you get permission errors:
1. Verify your `credentials.json` is valid
2. Ensure the spreadsheet is shared with the service account email
3. Check that the service account has "Editor" access
4. Verify the KANBAN_SHEET_ID in `.env` is correct

For more help, see the [Troubleshooting Guide](troubleshooting.md).
