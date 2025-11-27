"""
Testes para a ferramenta list_tasks do servidor MCP.
"""
import pytest
from unittest.mock import patch
from main import list_tasks
from models import SearchFilters, PaginationParams


def test_list_tasks_all(mock_env_vars, mock_connector):
    """Testa listagem de todas as tarefas sem filtros."""
    result = list_tasks()

    assert isinstance(result, list)
    assert len(result) == 3  # 3 tarefas no sample_sheet_data
    assert result[0]["Task ID"] == "TASK-001"
    assert result[1]["Task ID"] == "TASK-002"
    assert result[2]["Task ID"] == "TASK-003"


def test_list_tasks_with_priority_filter(mock_env_vars, mock_connector):
    """Testa filtro por prioridade."""
    filters = SearchFilters(prioridade=["Alta"]) # type: ignore
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["Task ID"] == "TASK-001"
    assert result[0]["Prioridade"] == "Alta"


def test_list_tasks_with_status_filter(mock_env_vars, mock_connector):
    """Testa filtro por status."""
    filters = SearchFilters(status=["Todo"]) # type: ignore
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 2  # TASK-002 e TASK-003
    assert all(task["Status"] == "Todo" for task in result)


def test_list_tasks_with_context_filter(mock_env_vars, mock_connector):
    """Testa filtro por contexto."""
    filters = SearchFilters(contexto="Backend")
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 2  # TASK-001 e TASK-003
    assert all("Backend" in task["Contexto"] for task in result)


def test_list_tasks_with_text_search(mock_env_vars, mock_connector):
    """Testa busca por texto na descrição."""
    filters = SearchFilters(texto_busca="API")
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["Task ID"] == "TASK-001"
    assert "API" in result[0]["Descrição"]


def test_list_tasks_with_task_id_filter(mock_env_vars, mock_connector):
    """Testa busca por Task ID específico."""
    filters = SearchFilters(task_id="TASK-002")
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["Task ID"] == "TASK-002"


def test_list_tasks_with_multiple_filters(mock_env_vars, mock_connector):
    """Testa combinação de múltiplos filtros."""
    filters = SearchFilters(
        status=["Todo"], # type: ignore
        contexto="Backend"
    )
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["Task ID"] == "TASK-003"


def test_list_tasks_with_pagination(mock_env_vars, mock_connector):
    """Testa paginação básica."""
    pagination = PaginationParams(page=1, page_size=2)
    result = list_tasks(pagination=pagination)

    assert isinstance(result, dict)
    assert result["total_count"] == 3
    assert len(result["tasks"]) == 2
    assert result["page"] == 1
    assert result["page_size"] == 2
    assert result["total_pages"] == 2


def test_list_tasks_pagination_second_page(mock_env_vars, mock_connector):
    """Testa segunda página da paginação."""
    pagination = PaginationParams(page=2, page_size=2)
    result = list_tasks(pagination=pagination)

    assert isinstance(result, dict)
    assert result["total_count"] == 3
    assert len(result["tasks"]) == 1  # Última página tem apenas 1 item
    assert result["page"] == 2


def test_list_tasks_with_filters_and_pagination(mock_env_vars, mock_connector):
    """Testa filtros combinados com paginação."""
    filters = SearchFilters(contexto="Backend")
    pagination = PaginationParams(page=1, page_size=1)
    result = list_tasks(filters=filters, pagination=pagination)

    assert isinstance(result, dict)
    assert result["total_count"] == 2
    assert len(result["tasks"]) == 1
    assert result["total_pages"] == 2


def test_list_tasks_empty_result(mock_env_vars, mock_connector):
    """Testa quando não há tarefas que correspondem aos filtros."""
    filters = SearchFilters(task_id="TASK-999")
    result = list_tasks(filters=filters)

    assert isinstance(result, list)
    assert len(result) == 0


def test_list_tasks_empty_sheet(mock_env_vars, empty_data):
    """Testa listagem de planilha vazia."""
    from main import reset_connector
    from unittest.mock import patch
    from utils.local_file_connector import LocalFileConnector

    # Resetar connector antes de criar novo mock
    reset_connector()

    # Criar connector com dados vazios
    with patch.object(LocalFileConnector, '_LocalFileConnector__load_data'), \
         patch.object(LocalFileConnector, '_LocalFileConnector__save_data'):
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        connector = LocalFileConnector(file_path=temp_file.name, sheet_name="Test")
        connector.df = empty_data.copy()

        with patch('main.get_connector', return_value=connector):
            result = list_tasks()

    assert isinstance(result, list)
    assert len(result) == 0
