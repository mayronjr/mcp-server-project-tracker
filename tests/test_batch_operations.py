"""
Testes para as ferramentas batch_add_tasks e batch_update_tasks do servidor MCP.
"""
import pytest
from unittest.mock import patch
from main import batch_add_tasks, batch_update_tasks, get_valid_configs
from models import (
    Task, TaskStatus, TaskPriority,
    BatchTaskAdd, BatchTaskUpdate, TaskUpdate, TaskUpdateFields
)


class TestBatchAddTasks:
    """Testes para batch_add_tasks."""

    def test_batch_add_single_task(self, mock_env_vars, mock_connector):
        """Testa adição em lote de uma única tarefa."""
        task = Task(
            project="TestProject",
            task_id="TASK-B001",
            task_id_root="TASK-B001",
            sprint="Sprint 1",
            contexto="Backend",
            descricao="Tarefa batch 1",
            detalhado="Detalhes",
            prioridade=TaskPriority.NORMAL,
            status=TaskStatus.TODO
        )

        batch = BatchTaskAdd(tasks=[task])
        result = batch_add_tasks(batch)

        assert isinstance(result, dict)
        assert result["success_count"] == 1
        assert result["error_count"] == 0
        assert len(result["details"]) == 1
        assert result["details"][0]["status"] == "success"

    def test_batch_add_multiple_tasks(self, mock_env_vars, mock_connector):
        """Testa adição em lote de múltiplas tarefas."""
        tasks = []
        for i in range(5):
            task = Task(
                project="TestProject",
                task_id=f"TASK-B{i:03d}",
                task_id_root=f"TASK-B{i:03d}",
                sprint="Sprint 1",
                contexto="Backend",
                descricao=f"Tarefa batch {i}",
                detalhado="",
                prioridade=TaskPriority.NORMAL,
                status=TaskStatus.TODO
            )
            tasks.append(task)

        batch = BatchTaskAdd(tasks=tasks)
        result = batch_add_tasks(batch)

        assert isinstance(result, dict)
        assert result["success_count"] == 5
        assert result["error_count"] == 0
        assert len(result["details"]) == 5

    def test_batch_add_mixed_priorities(self, mock_env_vars, mock_connector):
        """Testa adição de tarefas com diferentes prioridades."""
        priorities = [TaskPriority.BAIXA, TaskPriority.NORMAL,
                     TaskPriority.ALTA, TaskPriority.URGENTE]
        tasks = []

        for i, priority in enumerate(priorities):
            task = Task(
                project="TestProject",
                task_id=f"TASK-P{i}",
                task_id_root=f"TASK-P{i}",
                sprint="Sprint 1",
                contexto="Test",
                descricao=f"Tarefa prioridade {priority.value}",
                detalhado="",
                prioridade=priority,
                status=TaskStatus.TODO
            )
            tasks.append(task)

        batch = BatchTaskAdd(tasks=tasks)
        result = batch_add_tasks(batch)

        assert result["success_count"] == 4
        assert result["error_count"] == 0

    def test_batch_add_api_error(self, mock_env_vars, mock_connector):
        """Testa tratamento de erro na API."""
        # Simular erro ao adicionar tarefa
        with patch.object(mock_connector, 'add', return_value={"error": "Erro de API"}):
            task = Task(
                project="TestProject",
                task_id="TASK-ERROR",
                task_id_root="TASK-ERROR",
                sprint="Sprint 1",
                contexto="Test",
                descricao="Tarefa erro",
                detalhado="",
                prioridade=TaskPriority.NORMAL,
                status=TaskStatus.TODO
            )

            batch = BatchTaskAdd(tasks=[task])
            result = batch_add_tasks(batch)

        assert result["error_count"] > 0


class TestBatchUpdateTasks:
    """Testes para batch_update_tasks."""

    def test_batch_update_single_task(self, mock_env_vars, mock_connector):
        """Testa atualização em lote de uma única tarefa."""
        updates = [
            TaskUpdate(
                project="TestProject",
                task_id="TASK-001",
                fields=TaskUpdateFields(status="Concluído")
            )
        ]

        batch = BatchTaskUpdate(updates=updates)
        result = batch_update_tasks(batch)

        assert isinstance(result, dict)
        assert result["success_count"] == 1
        assert result["error_count"] == 0
        assert len(result["details"]) == 1
        assert result["details"][0]["status"] == "success"

    def test_batch_update_multiple_tasks(self, mock_env_vars, mock_connector):
        """Testa atualização em lote de múltiplas tarefas."""
        updates = [
            TaskUpdate(project="TestProject", task_id="TASK-001", fields=TaskUpdateFields(status="Concluído")),
            TaskUpdate(project="TestProject", task_id="TASK-002", fields=TaskUpdateFields(status="Em Desenvolvimento")),
            TaskUpdate(project="TestProject", task_id="TASK-003", fields=TaskUpdateFields(prioridade="Urgente"))
        ]

        batch = BatchTaskUpdate(updates=updates)
        result = batch_update_tasks(batch)

        assert isinstance(result, dict)
        assert result["success_count"] == 3
        assert result["error_count"] == 0
        assert len(result["details"]) == 3

    def test_batch_update_task_not_found(self, mock_env_vars, mock_connector):
        """Testa atualização de tarefa inexistente."""
        updates = [
            TaskUpdate(project="TestProject", task_id="TASK-999", fields=TaskUpdateFields(status="Concluído"))
        ]

        batch = BatchTaskUpdate(updates=updates)
        result = batch_update_tasks(batch)

        assert isinstance(result, dict)
        assert result["success_count"] == 0
        assert result["error_count"] == 1
        assert result["details"][0]["status"] == "error"
        assert "não encontrada" in result["details"][0]["message"].lower()

    def test_batch_update_invalid_status(self, mock_env_vars, mock_connector):
        """Testa atualização com status inválido."""
        # Com Pydantic, status inválido gerará um ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            updates = [
                TaskUpdate(project="TestProject", task_id="TASK-001", fields=TaskUpdateFields(status="StatusInvalido"))
            ]

    def test_batch_update_invalid_priority(self, mock_env_vars, mock_connector):
        """Testa atualização com prioridade inválida."""
        # Com Pydantic, prioridade inválida gerará um ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            updates = [
                TaskUpdate(project="TestProject", task_id="TASK-001", fields=TaskUpdateFields(prioridade="PrioridadeInvalida"))
            ]

    def test_batch_update_mixed_success_error(self, mock_env_vars, mock_connector):
        """Testa atualização em lote com sucesso e erros mistos."""
        updates = [
            TaskUpdate(project="TestProject", task_id="TASK-001", fields=TaskUpdateFields(status="Concluído")),
            TaskUpdate(project="TestProject", task_id="TASK-999", fields=TaskUpdateFields(status="Concluído")),
            TaskUpdate(project="TestProject", task_id="TASK-002", fields=TaskUpdateFields(status="Em Desenvolvimento")),
        ]

        batch = BatchTaskUpdate(updates=updates)
        result = batch_update_tasks(batch)

        assert isinstance(result, dict)
        assert result["success_count"] == 2
        assert result["error_count"] == 1

    def test_batch_update_multiple_fields(self, mock_env_vars, mock_connector):
        """Testa atualização de múltiplos campos (data_solucao é definida automaticamente)."""
        updates = [
            TaskUpdate(
                project="TestProject",
                task_id="TASK-001",
                fields=TaskUpdateFields(
                    status="Concluído",
                    prioridade="Alta",
                    detalhado="Tarefa finalizada com sucesso"
                )
            )
        ]

        batch = BatchTaskUpdate(updates=updates)
        result = batch_update_tasks(batch)

        assert result["success_count"] == 1
        assert result["error_count"] == 0


class TestGetValidConfigs:
    """Testes para get_valid_configs."""

    def test_get_valid_configs_structure(self, mock_env_vars):
        """Testa estrutura do retorno."""
        result = get_valid_configs()

        assert isinstance(result, dict)
        assert "valid_task_status" in result
        assert "valid_task_priorities" in result

    def test_get_valid_configs_status_values(self, mock_env_vars):
        """Testa valores de status válidos."""
        result = get_valid_configs()

        expected_status = ["Todo", "Em Desenvolvimento", "Impedido", "Concluído", "Cancelado", "Não Relacionado", "Pausado"]
        assert result["valid_task_status"] == expected_status

    def test_get_valid_configs_priority_values(self, mock_env_vars):
        """Testa valores de prioridade válidos."""
        result = get_valid_configs()

        expected_priorities = ["Baixa", "Normal", "Alta", "Urgente"]
        assert result["valid_task_priorities"] == expected_priorities
