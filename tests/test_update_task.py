"""
Testes para a ferramenta update_task do servidor MCP.
"""
import pytest
from unittest.mock import patch
from main import update_task
from models import TaskUpdateFields


def test_update_task_single_field(mock_env_vars, mock_credentials_file,
                                   mock_credentials, mock_get_sheets_service):
    """Testa atualização de um único campo."""
    updates = TaskUpdateFields(status="Concluído")
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()
    assert "TASK-001" in result


def test_update_task_multiple_fields(mock_env_vars, mock_credentials_file,
                                     mock_credentials, mock_get_sheets_service):
    """Testa atualização de múltiplos campos."""
    updates = TaskUpdateFields(
        status="Concluído",
        prioridade="Alta",
        detalhado="Tarefa finalizada"
    )
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_status_change(mock_env_vars, mock_credentials_file,
                                   mock_credentials, mock_get_sheets_service):
    """Testa mudança de status."""
    status_transitions = [
        TaskUpdateFields(status="Em Desenvolvimento"),
        TaskUpdateFields(status="Concluído"),
        TaskUpdateFields(status="Cancelado")
    ]

    for updates in status_transitions:
        result = update_task("TASK-001", updates)
        assert "sucesso" in result.lower()


def test_update_task_priority_change(mock_env_vars, mock_credentials_file,
                                     mock_credentials, mock_get_sheets_service):
    """Testa mudança de prioridade."""
    priorities = ["Baixa", "Normal", "Alta", "Urgente"]

    for priority in priorities:
        updates = TaskUpdateFields(prioridade=priority)
        result = update_task("TASK-001", updates)
        assert "sucesso" in result.lower()


def test_update_task_description(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_get_sheets_service):
    """Testa atualização da descrição."""
    updates = TaskUpdateFields(
        descricao="Nova descrição",
        detalhado="Descrição detalhada atualizada"
    )
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_sprint(mock_env_vars, mock_credentials_file,
                            mock_credentials, mock_get_sheets_service):
    """Testa atualização da sprint."""
    updates = TaskUpdateFields(sprint="Sprint 10")
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_context(mock_env_vars, mock_credentials_file,
                             mock_credentials, mock_get_sheets_service):
    """Testa atualização do contexto."""
    updates = TaskUpdateFields(contexto="Full Stack")
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_not_found(mock_env_vars, mock_credentials_file,
                               mock_credentials, mock_get_sheets_service):
    """Testa atualização de tarefa inexistente."""
    updates = TaskUpdateFields(status="Concluído")
    result = update_task("TASK-999", updates)

    assert isinstance(result, str)
    assert "não encontrada" in result.lower()


def test_update_task_invalid_status(mock_env_vars, mock_credentials_file,
                                    mock_credentials, mock_get_sheets_service):
    """Testa atualização com status inválido."""
    # Com Pydantic, status inválido gerará um ValidationError antes de chegar à função
    with pytest.raises(Exception):  # Pydantic ValidationError
        updates = TaskUpdateFields(status="StatusInvalido")
        result = update_task("TASK-001", updates)


def test_update_task_invalid_priority(mock_env_vars, mock_credentials_file,
                                      mock_credentials, mock_get_sheets_service):
    """Testa atualização com prioridade inválida."""
    # Com Pydantic, prioridade inválida gerará um ValidationError antes de chegar à função
    with pytest.raises(Exception):  # Pydantic ValidationError
        updates = TaskUpdateFields(prioridade="PrioridadeInvalida")
        result = update_task("TASK-001", updates)


def test_update_task_to_final_status(mock_env_vars, mock_credentials_file,
                                     mock_credentials, mock_get_sheets_service):
    """Testa atualização para status final (data_solucao deve ser definida automaticamente)."""
    final_statuses = ["Concluído", "Cancelado", "Não Relacionado"]

    for status in final_statuses:
        updates = TaskUpdateFields(status=status)
        result = update_task("TASK-001", updates)
        assert isinstance(result, str)
        assert "sucesso" in result.lower()


def test_update_task_clear_field(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_get_sheets_service):
    """Testa limpeza de um campo (string vazia)."""
    updates = TaskUpdateFields(detalhado="")
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
        updates = TaskUpdateFields(status="Concluído")
        result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "erro" in result.lower()


def test_update_task_empty_updates(mock_env_vars, mock_credentials_file,
                                   mock_credentials, mock_get_sheets_service):
    """Testa atualização sem campos preenchidos."""
    updates = TaskUpdateFields()
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "nenhum campo" in result.lower() or "erro" in result.lower()


def test_update_task_root_id(mock_env_vars, mock_credentials_file,
                             mock_credentials, mock_get_sheets_service):
    """Testa atualização do Task ID Root."""
    updates = TaskUpdateFields(task_id_root="TASK-NEW-ROOT")
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_update_task_special_characters(mock_env_vars, mock_credentials_file,
                                        mock_credentials, mock_get_sheets_service):
    """Testa atualização com caracteres especiais."""
    updates = TaskUpdateFields(
        descricao="Tarefa com: @#$%&*",
        detalhado="Acentuação: áéíóú ãõ ç"
    )
    result = update_task("TASK-001", updates)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()
