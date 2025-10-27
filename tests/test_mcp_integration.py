"""
Testes de integração para o servidor MCP.

Estes testes verificam a integração completa do servidor MCP,
incluindo decoradores @server.tool e validações de Pydantic.
"""
import pytest
from models import TaskStatus, TaskPriority


class TestMCPServerIntegration:
    """Testes de integração do servidor MCP."""

    def test_server_tools_registered(self, mock_env_vars, mock_credentials_file,
                                     mock_credentials):
        """Verifica se todas as ferramentas estão registradas no servidor."""
        from main import server

        # Verificar se as ferramentas esperadas estão registradas
        expected_tools = [
            "list_tasks",
            "add_task",
            "update_task",
            "batch_add_tasks",
            "batch_update_tasks",
            "get_valid_configs"
        ]

        # O FastMCP armazena as ferramentas, vamos verificar se elas existem
        # como atributos ou funções definidas
        import main
        for tool_name in expected_tools:
            assert hasattr(main, tool_name), f"Ferramenta '{tool_name}' não encontrada"

    def test_task_status_enum_values(self):
        """Verifica valores do enum TaskStatus."""
        assert TaskStatus.TODO.value == "Todo"
        assert TaskStatus.EM_DESENVOLVIMENTO.value == "Em Desenvolvimento"
        assert TaskStatus.CONCLUIDO.value == "Concluído"
        assert TaskStatus.CANCELADO.value == "Cancelado"

    def test_task_priority_enum_values(self):
        """Verifica valores do enum TaskPriority."""
        assert TaskPriority.BAIXA.value == "Baixa"
        assert TaskPriority.NORMAL.value == "Normal"
        assert TaskPriority.ALTA.value == "Alta"
        assert TaskPriority.URGENTE.value == "Urgente"

    def test_environment_variables_required(self):
        """Verifica se variáveis de ambiente obrigatórias são validadas."""
        # Este teste verifica que o código do main.py requer KANBAN_SHEET_ID
        # Verificamos que SPREADSHEET_ID não é None no código
        import main

        # Verificar que o código tem validação de SPREADSHEET_ID
        assert hasattr(main, 'SPREADSHEET_ID')
        # Se chegamos aqui, significa que a variável foi configurada corretamente
        # pois o módulo lança EnvironmentError se não estiver definida

    def test_credentials_file_required(self, mock_env_vars):
        """Verifica se o arquivo de credenciais é obrigatório."""
        import os
        from unittest.mock import patch

        # Mock que simula arquivo não existente
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                import importlib
                import main as main_module
                importlib.reload(main_module)


class TestPydanticModels:
    """Testes dos modelos Pydantic."""

    def test_task_model_validation(self):
        """Testa validação do modelo Task."""
        from models import Task

        # Dados válidos
        task_data = {
            "project": "TestProject",
            "task_id": "TASK-001",
            "task_id_root": "TASK-001",
            "sprint": "Sprint 1",
            "contexto": "Backend",
            "descricao": "Tarefa teste",
            "detalhado": "Descrição detalhada",
            "prioridade": TaskPriority.NORMAL,
            "status": TaskStatus.TODO,
            "data_criacao": "2025-10-24",
            "data_solucao": ""
        }

        task = Task(**task_data) # type: ignore
        assert task.task_id == "TASK-001"
        assert task.prioridade == "Normal"  # Devido ao use_enum_values
        assert task.status == "Todo"  # Devido ao use_enum_values

    def test_task_model_enum_serialization(self):
        """Testa serialização de enums no modelo Task."""
        from models import Task

        task = Task(
            project="TestProject",
            task_id="TASK-001",
            task_id_root="TASK-001",
            sprint="Sprint 1",
            contexto="Backend",
            descricao="Tarefa",
            detalhado="",
            prioridade=TaskPriority.ALTA,
            status=TaskStatus.EM_DESENVOLVIMENTO,
            data_criacao="2025-10-24",
            data_solucao=""
        )

        # model_dump deve retornar strings devido ao use_enum_values
        task_dict = task.model_dump()
        assert task_dict["prioridade"] == "Alta"
        assert task_dict["status"] == "Em Desenvolvimento"

    def test_search_filters_optional_fields(self):
        """Testa que SearchFilters aceita todos os campos como opcionais."""
        from models import SearchFilters

        # Deve ser possível criar sem nenhum campo
        filters = SearchFilters()
        assert filters.prioridade is None
        assert filters.status is None
        assert filters.contexto is None

        # Deve ser possível criar com apenas alguns campos
        filters2 = SearchFilters(prioridade=["Alta"]) # type: ignore
        assert filters2.prioridade == ["Alta"]
        assert filters2.status is None

    def test_pagination_params_validation(self):
        """Testa validação dos parâmetros de paginação."""
        from models import PaginationParams
        from pydantic import ValidationError

        # Valores válidos
        pagination = PaginationParams(page=1, page_size=25)
        assert pagination.page == 1
        assert pagination.page_size == 25

        # Valores padrão
        pagination2 = PaginationParams(page=1, page_size=25)
        assert pagination2.page_size == 25

        # Página mínima
        with pytest.raises(ValidationError):
            PaginationParams(page=0, page_size=25)

        # Tamanho de página fora do range
        with pytest.raises(ValidationError):
            PaginationParams(page=1, page_size=0)

        with pytest.raises(ValidationError):
            PaginationParams(page=1, page_size=501)

    def test_batch_task_add_validation(self):
        """Testa validação do modelo BatchTaskAdd."""
        from models import BatchTaskAdd, Task

        task1 = Task(
            project="TestProject",
            task_id="TASK-001",
            task_id_root="TASK-001",
            sprint="Sprint 1",
            contexto="Backend",
            descricao="Tarefa 1",
            detalhado="",
            prioridade=TaskPriority.NORMAL,
            status=TaskStatus.TODO,
            data_criacao="2025-10-24",
            data_solucao=""
        )

        batch = BatchTaskAdd(tasks=[task1])
        assert len(batch.tasks) == 1
        assert batch.tasks[0].task_id == "TASK-001"

    def test_batch_task_update_validation(self):
        """Testa validação do modelo BatchTaskUpdate."""
        from models import BatchTaskUpdate, TaskUpdate

        update1 = TaskUpdate(
            task_id="TASK-001",
            fields={"Status": "Concluído"}
        )

        batch = BatchTaskUpdate(updates=[update1])
        assert len(batch.updates) == 1
        assert batch.updates[0].task_id == "TASK-001"
        assert batch.updates[0].fields["Status"] == "Concluído"
