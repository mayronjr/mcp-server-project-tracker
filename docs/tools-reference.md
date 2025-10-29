# MCP Tools Quick Reference

## Available Tools

### 1. list_tasks
List/search tasks with filters and pagination.

**Filters:** `prioridade`, `status`, `contexto`, `projeto`, `texto_busca`, `task_id`, `sprint`
**Pagination:** `page`, `page_size`

```
Show me all high priority Backend tasks in Todo status
```

### 2. add_task
Add a single task. Required: `project`, `task_id`, `contexto`, `descricao`, `prioridade`, `status`

```
Add task TASK-101 for project "MCP Server", context Backend, description "Implement API", priority Alta, status Todo
```

### 3. update_task
Update task by task_id. Fields: `status`, `prioridade`, `contexto`, `descricao`, `detalhado`, `sprint`, `task_id_root`

```
Update TASK-101 to status "Concluído"
```

### 4. batch_add_tasks
Add multiple tasks in one operation.

```
Add tasks TASK-201, TASK-202, TASK-203 to project "MCP Server" with priority Alta
```

### 5. batch_update_tasks
Update multiple tasks in one operation.

```
Update TASK-201, TASK-202, TASK-203 to status "Em Desenvolvimento"
```

### 6. get_valid_configs
Get valid Status and Priority values.

**Status:** Todo, Em Desenvolvimento, Impedido, Concluído, Cancelado, Não Relacionado, Pausado
**Priority:** Baixa, Normal, Alta, Urgente

## Task Structure

Required fields: `project`, `task_id`, `contexto`, `descricao`, `prioridade`, `status`
Optional fields: `task_id_root`, `sprint`, `detalhado`
Auto-generated: `data_criacao`, `data_solucao`

## Quick Examples

```
# List urgent tasks
Show me all urgent tasks

# Filter by multiple criteria
Show me high priority Backend tasks in Todo or Em Desenvolvimento status from Sprint 2

# Add with details
Add TASK-150, project "MCP", context Backend, description "Add logging", detailed "Implement structured logging with winston", priority Normal, status Todo

# Batch complete tasks
Mark TASK-101, TASK-102, TASK-103 as Concluído

# Search by text
Find tasks containing "authentication"
```
