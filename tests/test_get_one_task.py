"""
Testes para a ferramenta get_one_task do servidor MCP Kanban Sheets.
"""
import pytest
from main import get_one_task


def test_get_one_task_success(mock_env_vars, mock_credentials_file,
                                mock_credentials, mock_get_sheets_service):
    """Testa busca de uma tarefa específica com sucesso."""
    result = get_one_task(project="TestProject", task_id="TASK-001")

    assert isinstance(result, dict)
    assert "error" not in result
    assert result["Task ID"] == "TASK-001"
    assert result["Nome Projeto"] == "TestProject"
    assert result["Contexto"] == "Backend"
    assert result["Descrição"] == "Implementar API"
    assert result["Prioridade"] == "Alta"
    assert result["Status"] == "Em Desenvolvimento"


def test_get_one_task_different_task(mock_env_vars, mock_credentials_file,
                                      mock_credentials, mock_get_sheets_service):
    """Testa busca de uma segunda tarefa diferente."""
    result = get_one_task(project="TestProject", task_id="TASK-002")

    assert isinstance(result, dict)
    assert "error" not in result
    assert result["Task ID"] == "TASK-002"
    assert result["Nome Projeto"] == "TestProject"
    assert result["Contexto"] == "Frontend"
    assert result["Descrição"] == "Criar interface"
    assert result["Prioridade"] == "Normal"
    assert result["Status"] == "Todo"


def test_get_one_task_with_root_id(mock_env_vars, mock_credentials_file,
                                    mock_credentials, mock_get_sheets_service):
    """Testa busca de uma tarefa com task_id_root definido."""
    result = get_one_task(project="TestProject", task_id="TASK-003")

    assert isinstance(result, dict)
    assert "error" not in result
    assert result["Task ID"] == "TASK-003"
    assert result["Task ID Root"] == "TASK-001"
    assert result["Nome Projeto"] == "TestProject"


def test_get_one_task_not_found(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_get_sheets_service):
    """Testa busca de uma tarefa que não existe."""
    result = get_one_task(project="TestProject", task_id="TASK-999")

    assert isinstance(result, dict)
    assert "error" in result
    assert "não encontrada" in result["error"]
    assert "TASK-999" in result["error"]


def test_get_one_task_wrong_project(mock_env_vars, mock_credentials_file,
                                     mock_credentials, mock_get_sheets_service):
    """Testa busca de uma tarefa com projeto incorreto."""
    result = get_one_task(project="WrongProject", task_id="TASK-001")

    assert isinstance(result, dict)
    assert "error" in result
    assert "não encontrada" in result["error"]
    assert "TASK-001" in result["error"]
    assert "WrongProject" in result["error"]


def test_get_one_task_empty_sheet(mock_env_vars, mock_credentials_file,
                                   mock_credentials, empty_sheet_data):
    """Testa busca em planilha vazia."""
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
        result = get_one_task(project="TestProject", task_id="TASK-001")

    assert isinstance(result, dict)
    assert "error" in result
    assert "não encontrada" in result["error"].lower()


def test_get_one_task_no_data(mock_env_vars, mock_credentials_file,
                               mock_credentials):
    """Testa busca quando não há dados na planilha."""
    from main import reset_connector
    from unittest.mock import MagicMock, patch

    # Resetar connector antes de criar novo mock
    reset_connector()

    # Criar mock que retorna sem values
    mock_service = MagicMock()
    mock_get = MagicMock()
    mock_get.execute.return_value = {}

    mock_values = MagicMock()
    mock_values.get.return_value = mock_get

    mock_spreadsheets = MagicMock()
    mock_spreadsheets.values.return_value = mock_values

    mock_service.spreadsheets.return_value = mock_spreadsheets

    # Aplicar o patch
    with patch('main.get_sheets_service', return_value=mock_service):
        result = get_one_task(project="TestProject", task_id="TASK-001")

    assert isinstance(result, dict)
    assert "error" in result
    assert "não encontrada" in result["error"].lower()


def test_get_one_task_api_error(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_get_sheets_service):
    """Testa tratamento de erro na API do Google Sheets."""
    # Configurar mock para lançar exceção
    mock_service = mock_get_sheets_service.return_value
    mock_service.spreadsheets().values().get().execute.side_effect = Exception("API Error")

    result = get_one_task(project="TestProject", task_id="TASK-001")

    assert isinstance(result, dict)
    assert "error" in result
    assert "Erro ao buscar tarefa" in result["error"]


def test_get_one_task_returns_all_fields(mock_env_vars, mock_credentials_file,
                                          mock_credentials, mock_get_sheets_service):
    """Testa se todos os campos da tarefa são retornados."""
    result = get_one_task(project="TestProject", task_id="TASK-001")

    expected_fields = [
        "Nome Projeto", "Task ID", "Task ID Root", "Sprint", "Contexto",
        "Descrição", "Detalhado", "Prioridade", "Status",
        "Data Criação", "Data Solução"
    ]

    for field in expected_fields:
        assert field in result, f"Campo '{field}' não encontrado no resultado"


def test_get_one_task_case_sensitive(mock_env_vars, mock_credentials_file,
                                      mock_credentials, mock_get_sheets_service):
    """Testa se a busca é case-sensitive para project e task_id."""
    # Tentar com case diferente
    result = get_one_task(project="testproject", task_id="task-001")

    assert isinstance(result, dict)
    assert "error" in result
    assert "não encontrada" in result["error"]
