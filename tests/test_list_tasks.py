"""
Testes para a ferramenta list_tasks do servidor MCP.
"""
import pytest
from unittest.mock import patch
from main import list_tasks
from models import SearchFilters, PaginationParams


def test_list_tasks_all(mock_env_vars, mock_credentials_file, mock_credentials,
                        mock_get_sheets_service):
    """Testa listagem de todas as tarefas sem filtros."""
    result = list_tasks()

    assert isinstance(result, list)
    assert len(result) == 3  # 3 tarefas no sample_sheet_data
    assert result[0]["Task ID"] == "TASK-001"
    assert result[1]["Task ID"] == "TASK-002"
    assert result[2]["Task ID"] == "TASK-003"


def test_list_tasks_with_priority_filter(mock_env_vars, mock_credentials_file,
                                         mock_credentials, mock_get_sheets_service):
    """Testa filtro por prioridade."""
    filters = SearchFilters(prioridade=["Alta"]) # type: ignore
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["Task ID"] == "TASK-001"
    assert result[0]["Prioridade"] == "Alta"


def test_list_tasks_with_status_filter(mock_env_vars, mock_credentials_file,
                                       mock_credentials, mock_get_sheets_service):
    """Testa filtro por status."""
    filters = SearchFilters(status=["Todo"]) # type: ignore
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 2  # TASK-002 e TASK-003
    assert all(task["Status"] == "Todo" for task in result)


def test_list_tasks_with_context_filter(mock_env_vars, mock_credentials_file,
                                        mock_credentials, mock_get_sheets_service):
    """Testa filtro por contexto."""
    filters = SearchFilters(contexto="Backend")
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 2  # TASK-001 e TASK-003
    assert all("Backend" in task["Contexto"] for task in result)


def test_list_tasks_with_text_search(mock_env_vars, mock_credentials_file,
                                     mock_credentials, mock_get_sheets_service):
    """Testa busca por texto na descrição."""
    filters = SearchFilters(texto_busca="API")
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["Task ID"] == "TASK-001"
    assert "API" in result[0]["Descrição"]


def test_list_tasks_with_task_id_filter(mock_env_vars, mock_credentials_file,
                                        mock_credentials, mock_get_sheets_service):
    """Testa busca por Task ID específico."""
    filters = SearchFilters(task_id="TASK-002")
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["Task ID"] == "TASK-002"


def test_list_tasks_with_multiple_filters(mock_env_vars, mock_credentials_file,
                                          mock_credentials, mock_get_sheets_service):
    """Testa combinação de múltiplos filtros."""
    filters = SearchFilters(
        status=["Todo"], # type: ignore
        contexto="Backend"
    )
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["Task ID"] == "TASK-003"


def test_list_tasks_with_pagination(mock_env_vars, mock_credentials_file,
                                    mock_credentials, mock_get_sheets_service):
    """Testa paginação básica."""
    pagination = PaginationParams(page=1, page_size=2)
    result = list_tasks(pagination=pagination)

    assert isinstance(result, dict)
    assert result["total_count"] == 3
    assert len(result["tasks"]) == 2
    assert result["page"] == 1
    assert result["page_size"] == 2
    assert result["total_pages"] == 2


def test_list_tasks_pagination_second_page(mock_env_vars, mock_credentials_file,
                                           mock_credentials, mock_get_sheets_service):
    """Testa segunda página da paginação."""
    pagination = PaginationParams(page=2, page_size=2)
    result = list_tasks(pagination=pagination)

    assert isinstance(result, dict)
    assert result["total_count"] == 3
    assert len(result["tasks"]) == 1  # Última página tem apenas 1 item
    assert result["page"] == 2


def test_list_tasks_with_filters_and_pagination(mock_env_vars, mock_credentials_file,
                                                mock_credentials, mock_get_sheets_service):
    """Testa filtros combinados com paginação."""
    filters = SearchFilters(contexto="Backend")
    pagination = PaginationParams(page=1, page_size=1)
    result = list_tasks(filters=filters, pagination=pagination)

    assert isinstance(result, dict)
    assert result["total_count"] == 2
    assert len(result["tasks"]) == 1
    assert result["total_pages"] == 2


def test_list_tasks_empty_result(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_get_sheets_service):
    """Testa quando não há tarefas que correspondem aos filtros."""
    filters = SearchFilters(task_id="TASK-999")
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 0


def test_list_tasks_empty_sheet(mock_env_vars, mock_credentials_file,
                                mock_credentials, empty_sheet_data):
    """Testa listagem de planilha vazia."""
    from main import reset_connector
    from unittest.mock import MagicMock, patch
    import copy

    # Resetar connector antes de criar novo mock
    reset_connector()

    # Criar mock que retorna dados vazios
    mock_service = MagicMock()
    mock_get = MagicMock()
    mock_get.execute.side_effect = lambda: copy.deepcopy(empty_sheet_data)

    mock_values = MagicMock()
    mock_values.get.return_value = mock_get

    mock_spreadsheets = MagicMock()
    mock_spreadsheets.values.return_value = mock_values

    mock_service.spreadsheets.return_value = mock_spreadsheets

    # Aplicar o patch
    with patch('main.get_sheets_service', return_value=mock_service):
        result = list_tasks()

    assert isinstance(result, list)
    assert len(result) == 0
