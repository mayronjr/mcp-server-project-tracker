# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP (Model Context Protocol) server for managing Kanban tasks using Google Sheets as a backend. The server provides tools to create, read, update, and filter tasks through the MCP protocol.

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
```

## Architecture

### Core Components

1. **[main.py](main.py)**: MCP server entry point using FastMCP
   - Defines MCP tools: `get_one_task`, `list_tasks`, `add_task`, `update_task`, `batch_add_tasks`, `batch_update_tasks`, `get_valid_configs`
   - Handles Google Sheets API authentication via service account
   - All logging goes to stderr (never stdout) per MCP STDIO protocol requirements
   - Uses singleton pattern for `PlanilhasConnector` instance via `get_connector()`

2. **[utils/planilhas_connector.py](utils/planilhas_connector.py)**: Google Sheets connector with local caching
   - Loads sheet data once into pandas DataFrame for fast queries
   - Automatically reloads cache after add/update operations
   - Handles all Google Sheets API interactions (get, add, update, batchUpdate)
   - Search/filter logic implemented using pandas operations for efficiency
   - Column names normalized (spaces -> hyphens) internally, converted back for output

3. **[models/](models/)**: Pydantic v2 models for type safety and validation
   - `task.py`: Core models (Task, TaskUpdate, TaskUpdateFields, BatchTaskAdd, BatchTaskUpdate, SearchFilters, PaginationParams, PaginatedResponse)
   - `task_status.py`: TaskStatus enum (Todo, Em Desenvolvimento, Impedido, Concluído, Cancelado, Não Relacionado, Pausado)
   - `task_priority.py`: TaskPriority enum (Baixa, Normal, Alta, Urgente)
   - All models use `use_enum_values = True` to serialize enums as strings
   - Field validators convert string inputs to enums with helpful error messages

4. **[tests/](tests/)**: Comprehensive pytest-based test suite
   - Uses mocks for Google Sheets API to avoid real API calls
   - Fixtures in `conftest.py` provide mock services, credentials, and sample data
   - `autouse` fixture resets connector between tests to avoid state pollution
   - Tests cover all MCP tools with various scenarios and edge cases

### Google Sheets Integration

The server expects a Google Sheets spreadsheet with columns A-K:

| Column | Field Name     | Description                  |
|--------|----------------|------------------------------|
| A      | Nome Projeto   | Project name (required)      |
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

1. **Pydantic Models with Enum Serialization**: All data structures use Pydantic v2
   - Enums automatically converted to string values via `use_enum_values = True`
   - Field validation happens automatically at model level
   - Validators in `TaskUpdateFields` convert strings back to enums for validation

2. **Cached DataFrame Pattern** ([utils/planilhas_connector.py](utils/planilhas_connector.py)):
   - Load sheet once into pandas DataFrame in `__init__` via `__load_data()`
   - All searches/filters use pandas operations (no API calls)
   - After `add()` or `update_one()`, automatically call `__load_data()` to refresh cache
   - Column name normalization: spaces -> hyphens internally, converted back in output

3. **Batch Operations**: Uses Google Sheets batchUpdate API
   - `batch_add_tasks`: Collects all tasks, single `append()` call
   - `batch_update_tasks`: Builds batch data array, single `batchUpdate()` call
   - Returns detailed success/error status for each operation

4. **Date Auto-filling**:
   - `data_criacao`: Auto-generated in `add_task` and `batch_add_tasks`
   - `data_solucao`: Auto-set when status changes to final state (Concluído, Cancelado, Não Relacionado)

5. **Pagination Support**: Optional in `list_tasks`
   - When `pagination` provided: returns `PaginatedResponse` with metadata
   - When not provided: returns simple list (backward compatibility)
   - Pagination applied after filtering, using list slicing

## MCP Tools Quick Reference

### get_one_task
Get specific task by project and task_id. Required: `project`, `task_id`.

### list_tasks
Search/filter tasks. Filters: `prioridade` (Baixa/Normal/Alta/Urgente), `status` (Todo/Em Desenvolvimento/Impedido/Concluído/Cancelado/Não Relacionado/Pausado), `contexto`, `projeto`, `texto_busca`, `task_id`, `sprint`. Supports pagination.

### add_task
Add single task. Required: `project`, `task_id`, `contexto`, `descricao`, `prioridade`, `status`. Auto-generates `data_criacao`.

### update_task
Update task by ID. Fields: `status`, `prioridade`, `contexto`, `descricao`, `detalhado`, `sprint`, `task_id_root`. Auto-sets `data_solucao` for final statuses.

### batch_add_tasks / batch_update_tasks
Add/update multiple tasks efficiently using single API call.

### get_valid_configs
Returns valid Status and Priority enum values.

## Testing Strategy

Tests use mocks to avoid Google Sheets API calls. Key fixtures in `conftest.py`:
- `mock_env_vars`: Mocked environment variables
- `mock_sheets_service`: Mock Google Sheets service with sample data
- `mock_connector`: Pre-configured PlanilhasConnector with mocked service
- `sample_sheet_data`: Standard test data (3 tasks)
- `empty_sheet_data`: Empty sheet for edge case testing
- `reset_connector_cache`: Autouse fixture to reset singleton between tests

When adding new features, ensure tests cover:
- Success cases with various inputs
- Validation errors for invalid inputs
- Edge cases (empty results, missing tasks, etc.)
- Batch operations with partial failures

## Important Implementation Notes

1. **Connector Singleton**: [main.py](main.py) uses global `_connector` variable with `get_connector()` factory. Use `reset_connector()` in tests to clear state.

2. **Field Name Mapping**: [main.py](main.py) tools use field mapping dicts (e.g., `field_to_header`) to convert Pydantic field names to Google Sheets column headers.

3. **MCP STDIO Protocol**: Never write to stdout (reserved for MCP protocol). All logs go to stderr via logging configuration in [main.py:23-28](main.py#L23-L28).

4. **Enum Validation**: [models/task.py](models/task.py) `TaskUpdateFields` has custom validators to convert strings to enums with clear error messages showing valid values.
