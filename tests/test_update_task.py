"""
Testes para a ferramenta update_task do servidor MCP.
"""
import pytest
from unittest.mock import patch
from main import update_task


def test_update_task_single_field(mock_env_vars, mock_credentials_file,
                                   mock_credentials, mock_get_sheets_service):
    """Testa atualização de um único campo."""
    updates = {"Status": "Concluído"}
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()
    assert "TASK-001" in result


def test_update_task_multiple_fields(mock_env_vars, mock_credentials_file,
                                     mock_credentials, mock_get_sheets_service):
    """Testa atualização de múltiplos campos."""
    updates = {
        "Status": "Concluído",
        "Data Solução": "2025-10-24",
        "Prioridade": "Alta"
    }
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_status_change(mock_env_vars, mock_credentials_file,
                                   mock_credentials, mock_get_sheets_service):
    """Testa mudança de status."""
    status_transitions = [
        {"Status": "Em Desenvolvimento"},
        {"Status": "Concluído"},
        {"Status": "Cancelado"}
    ]

    for updates in status_transitions:
        result = update_task("TASK-001", updates)
        assert "sucesso" in result.lower()


def test_update_task_priority_change(mock_env_vars, mock_credentials_file,
                                     mock_credentials, mock_get_sheets_service):
    """Testa mudança de prioridade."""
    priorities = ["Baixa", "Normal", "Alta", "Urgente"]

    for priority in priorities:
        updates = {"Prioridade": priority}
        result = update_task("TASK-001", updates)
        assert "sucesso" in result.lower()


def test_update_task_description(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_get_sheets_service):
    """Testa atualização da descrição."""
    updates = {
        "Descrição": "Nova descrição",
        "Detalhado": "Descrição detalhada atualizada"
    }
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_sprint(mock_env_vars, mock_credentials_file,
                            mock_credentials, mock_get_sheets_service):
    """Testa atualização da sprint."""
    updates = {"Sprint": "Sprint 10"}
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_context(mock_env_vars, mock_credentials_file,
                             mock_credentials, mock_get_sheets_service):
    """Testa atualização do contexto."""
    updates = {"Contexto": "Full Stack"}
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_not_found(mock_env_vars, mock_credentials_file,
                               mock_credentials, mock_get_sheets_service):
    """Testa atualização de tarefa inexistente."""
    updates = {"Status": "Concluído"}
    result = update_task("TASK-999", updates)

    assert isinstance(result, str)
    assert "não encontrada" in result.lower()


def test_update_task_invalid_status(mock_env_vars, mock_credentials_file,
                                    mock_credentials, mock_get_sheets_service):
    """Testa atualização com status inválido."""
    updates = {"Status": "StatusInvalido"}
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "erro" in result.lower() or "inválido" in result.lower()


def test_update_task_invalid_priority(mock_env_vars, mock_credentials_file,
                                      mock_credentials, mock_get_sheets_service):
    """Testa atualização com prioridade inválida."""
    updates = {"Prioridade": "PrioridadeInvalida"}
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "erro" in result.lower() or "inválido" in result.lower()


def test_update_task_with_dates(mock_env_vars, mock_credentials_file,
                                mock_credentials, mock_get_sheets_service):
    """Testa atualização das datas."""
    updates = {
        "Data Criação": "2025-10-20",
        "Data Solução": "2025-10-24"
    }
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_clear_field(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_get_sheets_service):
    """Testa limpeza de um campo (string vazia)."""
    updates = {"Data Solução": ""}
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_api_error(mock_env_vars, mock_credentials_file,
                               mock_credentials, mock_sheets_service):
    """Testa tratamento de erro da API do Google Sheets."""
    # Configurar mock para lançar exceção no get
    mock_sheets_service.spreadsheets().values().get().execute.side_effect = \
        Exception("Erro de conexão com Google Sheets")

    with patch('main.get_sheets_service', return_value=mock_sheets_service):
        updates = {"Status": "Concluído"}
        result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "erro" in result.lower()


def test_update_task_empty_updates(mock_env_vars, mock_credentials_file,
                                   mock_credentials, mock_get_sheets_service):
    """Testa atualização com dicionário vazio."""
    updates = {}
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    # Mesmo sem campos, deve processar sem erro


def test_update_task_root_id(mock_env_vars, mock_credentials_file,
                             mock_credentials, mock_get_sheets_service):
    """Testa atualização do Task ID Root."""
    updates = {"Task ID Root": "TASK-NEW-ROOT"}
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_special_characters(mock_env_vars, mock_credentials_file,
                                        mock_credentials, mock_get_sheets_service):
    """Testa atualização com caracteres especiais."""
    updates = {
        "Descrição": "Tarefa com: @#$%&*",
        "Detalhado": "Acentuação: áéíóú ãõ ç"
    }
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()
