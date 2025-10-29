# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server for managing Kanban tasks using Google Sheets as a backend. The server provides tools to create, read, update, and filter tasks in a Google Sheets spreadsheet through the MCP protocol.

## Code Style Guidelines

### Import Standards
- **AVOID lazy imports**: Always place imports at the top of the file
- **DO NOT** use imports inside functions or methods unless absolutely necessary
- Use explicit imports rather than importing entire modules when possible
- Group imports in the standard order: standard library, third-party, local modules

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv
uv sync

# Install development dependencies for testing
uv pip install -r requirements-dev.txt
```

### Running the Server
```bash
# Start the MCP server (uses STDIO protocol)
uv run main.py
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov

# Generate HTML coverage report
uv run pytest --cov --cov-report=html
# View report at htmlcov/index.html

# Run specific test file
uv run pytest tests/test_list_tasks.py

# Run specific test function
uv run pytest tests/test_list_tasks.py::test_list_tasks_all

# Run tests by marker
uv run pytest -m unit           # Run only unit tests
uv run pytest -m integration    # Run only integration tests
uv run pytest -m "not slow"     # Skip slow tests
```

## Architecture

### Core Components

1. **main.py**: MCP server entry point using FastMCP
   - Defines MCP tools: `list_tasks`, `add_task`, `update_task`, `batch_add_tasks`, `batch_update_tasks`, `get_valid_configs`
   - Handles Google Sheets API authentication via service account
   - All logging goes to stderr (never stdout) per MCP STDIO protocol requirements

2. **models/**: Pydantic v2 models for type safety and validation
   - `task.py`: Core models (Task, TaskUpdate, BatchTaskAdd, BatchTaskUpdate, SearchFilters, PaginationParams, PaginatedResponse)
   - `task_status.py`: TaskStatus enum (Todo, Em Desenvolvimento, Impedido, Concluído, Cancelado, Não Relacionado, Pausado)
   - `task_priority.py`: TaskPriority enum (Baixa, Normal, Alta, Urgente)
   - All models use `use_enum_values = True` to serialize enums as strings

3. **tests/**: Comprehensive pytest-based test suite
   - Uses mocks for Google Sheets API to avoid real API calls
   - Fixtures in `conftest.py` provide mock services, credentials, and sample data
   - Tests cover all MCP tools with various scenarios and edge cases

### Google Sheets Integration

The server expects a Google Sheets spreadsheet with the following column structure (A-K):

| Column | Field Name     | Description                  |
|--------|----------------|------------------------------|
| A      | Projeto        | Project name (required)      |
| B      | Task ID        | Unique task identifier       |
| C      | Task ID Root   | Parent task ID (optional)    |
| D      | Sprint         | Sprint name (optional)       |
| E      | Contexto       | Task context (required)      |
| F      | Descrição      | Brief description (required) |
| G      | Detalhado      | Detailed description         |
| H      | Prioridade     | Priority (enum)              |
| I      | Status         | Current status (enum)        |
| J      | Data Criação   | Creation date                |
| K      | Data Solução   | Completion date              |

### Configuration

Required environment variables in `.env`:
- `KANBAN_SHEET_ID`: Google Sheets spreadsheet ID
- `KANBAN_SHEET_NAME`: Sheet tab name (default: "Back-End")

Required file:
- `credentials.json`: Google Cloud Service Account credentials with Sheets API access

### Key Architectural Patterns

1. **Pydantic Models**: All data structures use Pydantic v2 for validation and serialization
   - Enums are automatically converted to their string values
   - Field validation happens automatically at the model level
   - See PYDANTIC_MIGRATION.md for migration details

2. **Batch Operations**: The server supports batch add/update operations using Google Sheets batchUpdate API
   - Reduces API calls and improves performance
   - Returns detailed success/error status for each operation

3. **Advanced Filtering**: `list_tasks` supports multiple filter types
   - By priority, status, context, project, sprint, task_id
   - Text search across description fields (case-insensitive)
   - Filters are combinable for complex queries

4. **Pagination**: Optional pagination support in `list_tasks`
   - When pagination params provided: returns PaginatedResponse with metadata
   - When not provided: returns simple list (legacy behavior for backward compatibility)

5. **Error Handling**: Comprehensive error handling with descriptive messages
   - Validates enum values before Google Sheets operations
   - Returns appropriate error structures for both single and batch operations

## MCP Tools Quick Reference (for Claude chats)

When using this MCP server in Claude chats, these tools are available:

### list_tasks
Search/filter tasks. Filters: `prioridade` (Baixa/Normal/Alta/Urgente), `status` (Todo/Em Desenvolvimento/Impedido/Concluído/Cancelado/Não Relacionado/Pausado), `contexto`, `projeto`, `texto_busca`, `task_id`, `sprint`. Supports pagination.

Example: "Show me all high priority Backend tasks in Todo status"

### add_task
Add single task. Required: `project`, `task_id`, `contexto`, `descricao`, `prioridade`, `status`. Optional: `task_id_root`, `sprint`, `detalhado`.

Example: "Add TASK-101 for project MCP Server, context Backend, description Implement API, priority Alta, status Todo"

### update_task
Update task by ID. Fields: `status`, `prioridade`, `contexto`, `descricao`, `detalhado`, `sprint`, `task_id_root`. Auto-sets completion date for final statuses.

Example: "Update TASK-101 to status Concluído"

### batch_add_tasks / batch_update_tasks
Add/update multiple tasks efficiently.

Example: "Mark TASK-101, TASK-102, TASK-103 as Concluído"

### get_valid_configs
Returns valid Status and Priority values.

## MCP Client Configuration

To use this server with an MCP client, add to your client configuration:

```json
{
  "mcpServers": {
    "kanban-sheets": {
      "command": "uv",
      "args": ["run", "main.py"]
    }
  }
}
```

## Testing Strategy

Tests use mocks to avoid Google Sheets API calls. Key fixtures:
- `mock_env_vars`: Mocked environment variables
- `mock_sheets_service`: Mock Google Sheets service
- `mock_credentials`: Mock Google credentials
- `sample_sheet_data`: Standard test data set
- `empty_sheet_data`: Empty sheet for edge case testing

When adding new features, ensure tests cover:
- Success cases with various inputs
- Validation errors for invalid inputs
- Edge cases (empty results, missing tasks, etc.)
- Batch operations with partial failures
