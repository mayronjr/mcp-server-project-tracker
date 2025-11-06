"""
Testes para a ferramenta get_one_or_more_tasks do servidor MCP Kanban Sheets.
"""
import pytest
from main import get_one_or_more_tasks


def test_get_one_task_success(mock_env_vars, mock_credentials_file,
                                mock_credentials, mock_get_sheets_service):
    """Testa busca de uma tarefa específica com sucesso."""
    result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-001"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" not in result[0]
    assert result[0]["Task ID"] == "TASK-001"
    assert result[0]["Nome Projeto"] == "TestProject"
    assert result[0]["Contexto"] == "Backend"
    assert result[0]["Descrição"] == "Implementar API"
    assert result[0]["Prioridade"] == "Alta"
    assert result[0]["Status"] == "Em Desenvolvimento"


def test_get_multiple_tasks_success(mock_env_vars, mock_credentials_file,
                                     mock_credentials, mock_get_sheets_service):
    """Testa busca de múltiplas tarefas com sucesso."""
    result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-001", "TASK-002"])

    assert isinstance(result, list)
    assert len(result) == 2

    # Primeira tarefa
    assert "error" not in result[0]
    assert result[0]["Task ID"] == "TASK-001"
    assert result[0]["Nome Projeto"] == "TestProject"
    assert result[0]["Prioridade"] == "Alta"

    # Segunda tarefa
    assert "error" not in result[1]
    assert result[1]["Task ID"] == "TASK-002"
    assert result[1]["Nome Projeto"] == "TestProject"
    assert result[1]["Prioridade"] == "Normal"


def test_get_one_task_different_task(mock_env_vars, mock_credentials_file,
                                      mock_credentials, mock_get_sheets_service):
    """Testa busca de uma segunda tarefa diferente."""
    result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-002"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" not in result[0]
    assert result[0]["Task ID"] == "TASK-002"
    assert result[0]["Nome Projeto"] == "TestProject"
    assert result[0]["Contexto"] == "Frontend"
    assert result[0]["Descrição"] == "Criar interface"
    assert result[0]["Prioridade"] == "Normal"
    assert result[0]["Status"] == "Todo"


def test_get_one_task_with_root_id(mock_env_vars, mock_credentials_file,
                                    mock_credentials, mock_get_sheets_service):
    """Testa busca de uma tarefa com task_id_root definido."""
    result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-003"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" not in result[0]
    assert result[0]["Task ID"] == "TASK-003"
    assert result[0]["Task ID Root"] == "TASK-001"
    assert result[0]["Nome Projeto"] == "TestProject"


def test_get_one_task_not_found(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_get_sheets_service):
    """Testa busca de uma tarefa que não existe."""
    result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-999"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0]
    assert result[0]["task_id"] == "TASK-999"
    assert result[0]["project"] == "TestProject"
    assert "não encontrada" in result[0]["error"]


def test_get_multiple_tasks_partial_found(mock_env_vars, mock_credentials_file,
                                           mock_credentials, mock_get_sheets_service):
    """Testa busca de múltiplas tarefas onde algumas existem e outras não."""
    result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-001", "TASK-999", "TASK-002"])

    assert isinstance(result, list)
    assert len(result) == 3

    # Primeira tarefa encontrada
    assert "error" not in result[0]
    assert result[0]["Task ID"] == "TASK-001"

    # Segunda tarefa não encontrada
    assert "error" in result[1]
    assert result[1]["task_id"] == "TASK-999"
    assert result[1]["project"] == "TestProject"

    # Terceira tarefa encontrada
    assert "error" not in result[2]
    assert result[2]["Task ID"] == "TASK-002"


def test_get_one_task_wrong_project(mock_env_vars, mock_credentials_file,
                                     mock_credentials, mock_get_sheets_service):
    """Testa busca de uma tarefa com projeto incorreto."""
    result = get_one_or_more_tasks(project="WrongProject", task_id_list=["TASK-001"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0]
    assert result[0]["task_id"] == "TASK-001"
    assert result[0]["project"] == "WrongProject"
    assert "não encontrada" in result[0]["error"]


def test_get_empty_list(mock_env_vars, mock_credentials_file,
                        mock_credentials, mock_get_sheets_service):
    """Testa busca com lista vazia de task_ids."""
    result = get_one_or_more_tasks(project="TestProject", task_id_list=[])

    assert isinstance(result, list)
    assert len(result) == 0


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
        result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-001"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0]
    assert result[0]["task_id"] == "TASK-001"
    assert "não encontrada" in result[0]["error"].lower()


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
        result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-001"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0]
    assert "não encontrada" in result[0]["error"].lower()


def test_get_one_task_api_error(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_connector):
    """Testa tratamento de erro na API do Google Sheets."""
    from unittest.mock import patch

    # Configurar patch para lançar exceção no get_one
    with patch.object(mock_connector, 'get_one', side_effect=Exception("API Error")):
        result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-001"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0]
    assert result[0]["task_id"] == "TASK-001"
    assert result[0]["project"] == "TestProject"
    assert "Erro ao buscar tarefa" in result[0]["error"]


def test_get_multiple_tasks_all_errors(mock_env_vars, mock_credentials_file,
                                        mock_credentials, mock_connector):
    """Testa busca de múltiplas tarefas onde todas retornam erro."""
    from unittest.mock import patch

    # Configurar patch para lançar exceção no get_one
    with patch.object(mock_connector, 'get_one', side_effect=Exception("API Error")):
        result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-001", "TASK-002"])

    assert isinstance(result, list)
    assert len(result) == 2

    # Todas devem ter erro
    for i, task_id in enumerate(["TASK-001", "TASK-002"]):
        assert "error" in result[i]
        assert result[i]["task_id"] == task_id
        assert result[i]["project"] == "TestProject"


def test_get_one_task_returns_all_fields(mock_env_vars, mock_credentials_file,
                                          mock_credentials, mock_get_sheets_service):
    """Testa se todos os campos da tarefa são retornados."""
    result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-001"])

    assert isinstance(result, list)
    assert len(result) == 1

    expected_fields = [
        "Nome Projeto", "Task ID", "Task ID Root", "Sprint", "Contexto",
        "Descrição", "Detalhado", "Prioridade", "Status",
        "Data Criação", "Data Solução"
    ]

    for field in expected_fields:
        assert field in result[0], f"Campo '{field}' não encontrado no resultado"


def test_get_one_task_case_sensitive(mock_env_vars, mock_credentials_file,
                                      mock_credentials, mock_get_sheets_service):
    """Testa se a busca é case-sensitive para project e task_id."""
    # Tentar com case diferente
    result = get_one_or_more_tasks(project="testproject", task_id_list=["task-001"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0]
    assert result[0]["task_id"] == "task-001"
    assert result[0]["project"] == "testproject"
    assert "não encontrada" in result[0]["error"]


def test_get_three_tasks_all_found(mock_env_vars, mock_credentials_file,
                                    mock_credentials, mock_get_sheets_service):
    """Testa busca de três tarefas existentes."""
    result = get_one_or_more_tasks(project="TestProject", task_id_list=["TASK-001", "TASK-002", "TASK-003"])

    assert isinstance(result, list)
    assert len(result) == 3

    # Todas devem ser encontradas
    for i, task_id in enumerate(["TASK-001", "TASK-002", "TASK-003"]):
        assert "error" not in result[i]
        assert result[i]["Task ID"] == task_id
        assert result[i]["Nome Projeto"] == "TestProject"
