"""
Configuração de fixtures para testes do servidor MCP Kanban Sheets.
"""
import os
import pytest
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock das variáveis de ambiente necessárias."""
    monkeypatch.setenv("KANBAN_SHEET_ID", "test-sheet-id-123")
    monkeypatch.setenv("KANBAN_SHEET_NAME", "Test-Sheet")


@pytest.fixture
def sample_sheet_data():
    """Dados de exemplo de uma planilha Kanban."""
    return {
        "values": [
            # Cabeçalho
            ["Projeto", "Task ID", "Task ID Root", "Sprint", "Contexto", "Descrição",
             "Detalhado", "Prioridade", "Status", "Data Criação", "Data Solução"],
            # Tarefas de exemplo
            ["TestProject", "TASK-001", "TASK-001", "Sprint 1", "Backend", "Implementar API",
             "Criar endpoints REST", "Alta", "Em Desenvolvimento", "2025-10-20", ""],
            ["TestProject", "TASK-002", "TASK-002", "Sprint 1", "Frontend", "Criar interface",
             "Interface do usuário", "Normal", "Todo", "2025-10-21", ""],
            ["TestProject", "TASK-003", "TASK-001", "Sprint 2", "Backend", "Adicionar testes",
             "Testes unitários e integração", "Urgente", "Todo", "2025-10-22", ""],
        ]
    }


@pytest.fixture
def empty_sheet_data():
    """Dados de uma planilha vazia (apenas cabeçalho)."""
    return {
        "values": [
            ["Projeto", "Task ID", "Task ID Root", "Sprint", "Contexto", "Descrição",
             "Detalhado", "Prioridade", "Status", "Data Criação", "Data Solução"]
        ]
    }


@pytest.fixture
def mock_sheets_service(sample_sheet_data):
    """Mock do serviço Google Sheets API."""
    mock_service = MagicMock()

    # Mock do método get (para leitura)
    mock_get = MagicMock()
    mock_get.execute.return_value = sample_sheet_data

    # Mock do método append (para adicionar)
    mock_append = MagicMock()
    mock_append.execute.return_value = {
        "updates": {
            "updatedRows": 1
        }
    }

    # Mock do método update (para atualizar)
    mock_update = MagicMock()
    mock_update.execute.return_value = {
        "updatedCells": 1
    }

    # Mock do método batchUpdate (para atualização em lote)
    mock_batch_update = MagicMock()
    mock_batch_update.execute.return_value = {
        "totalUpdatedRows": 3
    }

    # Configurar a cadeia de chamadas
    mock_values = MagicMock()
    mock_values.get.return_value = mock_get
    mock_values.append.return_value = mock_append
    mock_values.update.return_value = mock_update
    mock_values.batchUpdate.return_value = mock_batch_update

    mock_spreadsheets = MagicMock()
    mock_spreadsheets.values.return_value = mock_values

    mock_service.spreadsheets.return_value = mock_spreadsheets

    return mock_service


@pytest.fixture
def mock_credentials():
    """Mock das credenciais do Google."""
    with patch('main.Credentials.from_service_account_file') as mock_creds:
        mock_instance = Mock()
        mock_instance.universe_domain = "googleapis.com"
        mock_creds.return_value = mock_instance
        yield mock_creds


@pytest.fixture
def mock_credentials_file():
    """Mock para verificação de arquivo de credenciais."""
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        yield mock_exists


@pytest.fixture
def mock_sheets_build(mock_sheets_service):
    """Mock da função build do Google API."""
    with patch('main.build') as mock_build:
        mock_build.return_value = mock_sheets_service
        yield mock_build


@pytest.fixture
def mock_get_sheets_service(mock_sheets_service):
    """Mock da função get_sheets_service do main."""
    with patch('main.get_sheets_service') as mock_func:
        mock_func.return_value = mock_sheets_service
        yield mock_func


@pytest.fixture
def sample_task_data():
    """Dados de exemplo de uma tarefa."""
    return {
        "project": "TestProject",
        "task_id": "TASK-100",
        "task_id_root": "TASK-100",
        "sprint": "Sprint 3",
        "contexto": "Backend",
        "descricao": "Nova tarefa de teste",
        "detalhado": "Descrição detalhada da tarefa",
        "prioridade": "Normal",
        "status": "Todo",
        "data_criacao": "2025-10-24",
        "data_solucao": ""
    }
