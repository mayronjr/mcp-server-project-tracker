# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP (Model Context Protocol) server for managing Kanban tasks using local files (Excel or CSV) as a backend. The server provides tools to create, read, update, and filter tasks through the MCP protocol.

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
   - Defines MCP tools: `get_one_or_more_tasks`, `list_tasks`, `batch_add_tasks`, `batch_update_tasks`, `get_valid_configs`
   - Uses local file connector for Excel/CSV file access
   - All logging goes to stderr (never stdout) per MCP STDIO protocol requirements
   - Uses singleton pattern for `LocalFileConnector` instance via `get_connector()`

2. **[utils/local_file_connector.py](utils/local_file_connector.py)**: Local file connector with caching
   - Loads file data once into pandas DataFrame for fast queries
   - Automatically saves file after add/update operations
   - Supports both Excel (.xlsx, .xls) and CSV (.csv) formats
   - Search/filter logic implemented using pandas operations for efficiency
   - Column names normalized (spaces -> hyphens) internally, converted back for output
   - Creates file with proper structure if it doesn't exist

3. **[models/](models/)**: Pydantic v2 models for type safety and validation
   - `task.py`: Core models (Task, TaskUpdate, TaskUpdateFields, BatchTaskAdd, BatchTaskUpdate, SearchFilters, PaginationParams, PaginatedResponse)
   - `task_status.py`: TaskStatus enum (Todo, Em Desenvolvimento, Impedido, Concluído, Cancelado, Não Relacionado, Pausado)
   - `task_priority.py`: TaskPriority enum (Baixa, Normal, Alta, Urgente)
   - All models use `use_enum_values = True` to serialize enums as strings
   - Field validators convert string inputs to enums with helpful error messages

4. **[tests/](tests/)**: Comprehensive pytest-based test suite
   - Uses mocks for file operations to avoid real file access
   - Fixtures in `conftest.py` provide mock connector and sample data
   - `autouse` fixture resets connector between tests to avoid state pollution
   - Tests cover all MCP tools with various scenarios and edge cases

### File Structure

The server expects an Excel or CSV file with the following columns:

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
- `KANBAN_FILE_PATH`: Path to Excel (.xlsx) or CSV (.csv) file (default: "kanban.xlsx")
- `KANBAN_SHEET_NAME`: Sheet tab name for Excel files (optional, default: first sheet)

The file will be created automatically with the proper structure if it doesn't exist.

### Key Architectural Patterns

1. **Pydantic Models with Enum Serialization**: All data structures use Pydantic v2
   - Enums automatically converted to string values via `use_enum_values = True`
   - Field validation happens automatically at model level
   - Validators in `TaskUpdateFields` convert strings back to enums for validation

2. **Cached DataFrame Pattern** ([utils/local_file_connector.py](utils/local_file_connector.py)):
   - Load file once into pandas DataFrame in `__init__` via `__load_data()`
   - All searches/filters use pandas operations (no file I/O)
   - After `add()` or `update_one()`, automatically call `__save_data()` to persist changes
   - Column name normalization: spaces -> hyphens internally, converted back in output

3. **Batch Operations**: Efficient batch processing
   - `batch_add_tasks`: Collects all tasks, single file write operation
   - `batch_update_tasks`: Builds batch updates, single file write operation
   - Returns detailed success/error status for each operation

4. **Date Auto-filling**:
   - `data_criacao`: Auto-generated in `batch_add_tasks`
   - `data_solucao`: Auto-set when status changes to final state (Concluído, Cancelado, Não Relacionado)

5. **Pagination Support**: Optional in `list_tasks`
   - When `pagination` provided: returns `PaginatedResponse` with metadata
   - When not provided: returns simple list (backward compatibility)
   - Pagination applied after filtering, using list slicing

6. **File Format Support**:
   - Excel files (.xlsx, .xls): Uses openpyxl engine, supports multiple sheets
   - CSV files (.csv): Standard CSV format with automatic encoding detection

## MCP Tools Quick Reference

### get_one_or_more_tasks
Get one or more specific tasks by project and task_id list. Required: `project`, `task_id_list`.

### list_tasks
Search/filter tasks. Filters: `prioridade` (Baixa/Normal/Alta/Urgente), `status` (Todo/Em Desenvolvimento/Impedido/Concluído/Cancelado/Não Relacionado/Pausado), `contexto`, `projeto`, `texto_busca`, `task_id`, `sprint`. Supports pagination.

### batch_add_tasks
Add multiple tasks efficiently. Auto-generates `data_criacao` for each task.

### batch_update_tasks
Update multiple tasks efficiently. Fields: `status`, `prioridade`, `contexto`, `descricao`, `detalhado`, `sprint`, `task_id_root`. Auto-sets `data_solucao` for final statuses.

### get_valid_configs
Returns valid Status and Priority enum values.

## Testing Strategy

Tests use mocks to avoid file I/O operations. Key fixtures in `conftest.py`:
- `mock_env_vars`: Mocked environment variables
- `mock_connector`: Pre-configured LocalFileConnector with mocked file operations
- `sample_data`: Standard test data (3 tasks)
- `empty_data`: Empty dataset for edge case testing
- `reset_connector_cache`: Autouse fixture to reset singleton between tests

When adding new features, ensure tests cover:
- Success cases with various inputs
- Validation errors for invalid inputs
- Edge cases (empty results, missing tasks, etc.)
- Batch operations with partial failures
- Both Excel and CSV file formats

## Important Implementation Notes

1. **Connector Singleton**: [main.py](main.py) uses global `_connector` variable with `get_connector()` factory. Use `reset_connector()` in tests to clear state.

2. **Field Name Mapping**: [main.py](main.py) tools use field mapping dicts (e.g., `field_to_header`) to convert Pydantic field names to file column headers.

3. **MCP STDIO Protocol**: Never write to stdout (reserved for MCP protocol). All logs go to stderr via logging configuration in [main.py:22-25](main.py#L22-L25).

4. **Enum Validation**: [models/task.py](models/task.py) `TaskUpdateFields` has custom validators to convert strings to enums with clear error messages showing valid values.

5. **File Auto-creation**: If the specified file doesn't exist, it will be created automatically with the proper column structure.
