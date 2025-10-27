"""
Testes para a ferramenta add_task do servidor MCP.
"""
import pytest
from unittest.mock import patch
from main import add_task
from models import Task, TaskStatus, TaskPriority


def test_add_task_success(mock_env_vars, mock_credentials_file, mock_credentials,
                          mock_get_sheets_service, sample_task_data):
    """Testa adição de tarefa com sucesso."""
    task = Task(**sample_task_data)
    result = add_task(task)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()
    assert task.task_id in result


def test_add_task_with_all_fields(mock_env_vars, mock_credentials_file,
                                  mock_credentials, mock_get_sheets_service):
    """Testa adição de tarefa com todos os campos preenchidos."""
    task = Task(
        project="TestProject",
        task_id="TASK-200",
        task_id_root="TASK-200",
        sprint="Sprint 5",
        contexto="Full Stack",
        descricao="Tarefa completa",
        detalhado="Descrição muito detalhada da tarefa",
        prioridade=TaskPriority.URGENTE,
        status=TaskStatus.EM_DESENVOLVIMENTO,
        data_criacao="2025-10-24",
        data_solucao="2025-10-25"
    )

    result = add_task(task)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()
    assert "TASK-200" in result


def test_add_task_minimal_fields(mock_env_vars, mock_credentials_file,
                                 mock_credentials, mock_get_sheets_service):
    """Testa adição de tarefa com campos mínimos obrigatórios."""
    task = Task(
        project="TestProject",
        task_id="TASK-300",
        task_id_root="TASK-300",
        sprint="Sprint 1",
        contexto="Backend",
        descricao="Tarefa mínima",
        detalhado="",
        prioridade=TaskPriority.NORMAL,
        status=TaskStatus.TODO,
        data_criacao="2025-10-24",
        data_solucao=""
    )

    result = add_task(task)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()


def test_add_task_with_subtask(mock_env_vars, mock_credentials_file,
                               mock_credentials, mock_get_sheets_service):
    """Testa adição de subtarefa (task_id_root diferente)."""
    task = Task(
        project="TestProject",
        task_id="TASK-100-01",
        task_id_root="TASK-100",
        sprint="Sprint 2",
        contexto="Backend",
        descricao="Subtarefa",
        detalhado="Esta é uma subtarefa",
        prioridade=TaskPriority.ALTA,
        status=TaskStatus.TODO,
        data_criacao="2025-10-24",
        data_solucao=""
    )

    result = add_task(task)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()
    assert "TASK-100-01" in result


def test_add_task_with_different_priorities(mock_env_vars, mock_credentials_file,
                                             mock_credentials, mock_get_sheets_service):
    """Testa adição de tarefas com diferentes prioridades."""
    priorities = [
        TaskPriority.BAIXA,
        TaskPriority.NORMAL,
        TaskPriority.ALTA,
        TaskPriority.URGENTE
    ]

    for priority in priorities:
        task = Task(
            project="TestProject",
            task_id=f"TASK-{priority.value}",
            task_id_root=f"TASK-{priority.value}",
            sprint="Sprint 1",
            contexto="Test",
            descricao=f"Tarefa com prioridade {priority.value}",
            detalhado="",
            prioridade=priority,
            status=TaskStatus.TODO,
            data_criacao="2025-10-24",
            data_solucao=""
        )

        result = add_task(task)
        assert "sucesso" in result.lower()


def test_add_task_with_different_status(mock_env_vars, mock_credentials_file,
                                        mock_credentials, mock_get_sheets_service):
    """Testa adição de tarefas com diferentes status."""
    statuses = [
        TaskStatus.TODO,
        TaskStatus.EM_DESENVOLVIMENTO,
        TaskStatus.CONCLUIDO,
        TaskStatus.CANCELADO
    ]

    for status in statuses:
        task = Task(
            project="TestProject",
            task_id=f"TASK-{status.value}",
            task_id_root=f"TASK-{status.value}",
            sprint="Sprint 1",
            contexto="Test",
            descricao=f"Tarefa com status {status.value}",
            detalhado="",
            prioridade=TaskPriority.NORMAL,
            status=status,
            data_criacao="2025-10-24",
            data_solucao=""
        )

        result = add_task(task)
        assert "sucesso" in result.lower()


def test_add_task_api_error(mock_env_vars, mock_credentials_file,
                            mock_credentials, mock_sheets_service, sample_task_data):
    """Testa tratamento de erro da API do Google Sheets."""
    # Configurar mock para lançar exceção
    mock_sheets_service.spreadsheets().values().append().execute.side_effect = \
        Exception("Erro de conexão com Google Sheets")

    with patch('main.get_sheets_service', return_value=mock_sheets_service):
        task = Task(**sample_task_data)
        result = add_task(task)

    assert isinstance(result, str)
    assert "erro" in result.lower()


def test_add_task_with_special_characters(mock_env_vars, mock_credentials_file,
                                          mock_credentials, mock_get_sheets_service):
    """Testa adição de tarefa com caracteres especiais."""
    task = Task(
        project="TestProject",
        task_id="TASK-SPECIAL",
        task_id_root="TASK-SPECIAL",
        sprint="Sprint 1",
        contexto="Backend",
        descricao="Tarefa com caracteres: @#$%&*",
        detalhado="Descrição com acentuação: áéíóú ãõ ç",
        prioridade=TaskPriority.NORMAL,
        status=TaskStatus.TODO,
        data_criacao="2025-10-24",
        data_solucao=""
    )

    result = add_task(task)

    assert isinstance(result, str)
    assert "sucesso" in result.lower()
