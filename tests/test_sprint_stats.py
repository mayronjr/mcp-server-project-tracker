"""
Testes para a ferramenta get_sprint_stats do servidor MCP.
"""
import pytest
import pandas as pd
from unittest.mock import patch
from main import get_sprint_stats
from utils.local_file_connector import LocalFileConnector


@pytest.fixture
def sprint_data() -> pd.DataFrame:
    """Dados de exemplo com múltiplas sprints para testes de estatísticas."""
    data = {
        'Nome-Projeto': ['ProjectA', 'ProjectA', 'ProjectA', 'ProjectA', 'ProjectB', 'ProjectB'],
        'Task-ID': ['TASK-001', 'TASK-002', 'TASK-003', 'TASK-004', 'TASK-005', 'TASK-006'],
        'Task-ID-Root': ['', '', '', '', '', ''],
        'Sprint': ['Sprint 1', 'Sprint 1', 'Sprint 1', 'Sprint 2', 'Sprint 1', 'Sprint 2'],
        'Contexto': ['Backend', 'Frontend', 'Backend', 'Backend', 'Backend', 'Frontend'],
        'Descrição': ['Task 1', 'Task 2', 'Task 3', 'Task 4', 'Task 5', 'Task 6'],
        'Detalhado': ['Details 1', 'Details 2', 'Details 3', 'Details 4', 'Details 5', 'Details 6'],
        'Prioridade': ['Alta', 'Normal', 'Baixa', 'Alta', 'Normal', 'Urgente'],
        'Status': ['Concluído', 'Concluído', 'Em Desenvolvimento', 'Todo', 'Concluído', 'Concluído'],
        'Data-Criação': ['2025-10-20', '2025-10-21', '2025-10-22', '2025-10-23', '2025-10-24', '2025-10-25'],
        'Data-Solução': ['2025-10-25', '2025-10-26', '', '', '2025-10-27', '2025-10-28']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sprint_connector(sprint_data, tmp_path):
    """Mock do LocalFileConnector com dados de sprint para testes."""
    file_path = tmp_path / "test_kanban.xlsx"

    with patch.object(LocalFileConnector, '_LocalFileConnector__load_data'), \
         patch.object(LocalFileConnector, '_LocalFileConnector__save_data'):

        connector = LocalFileConnector(
            file_path=str(file_path),
            sheet_name="Test-Sheet"
        )
        connector.df = sprint_data.copy()

        with patch('main.get_connector') as mock_get_conn:
            mock_get_conn.return_value = connector
            yield connector


def test_get_sprint_stats_all_sprints(mock_env_vars, sprint_connector):
    """Testa estatísticas de todas as sprints sem filtro de projeto."""
    result = get_sprint_stats()

    assert isinstance(result, dict)
    assert "sprints" in result
    assert "total_sprints" in result
    assert result["total_sprints"] == 2  # Sprint 1 e Sprint 2

    sprints = result["sprints"]
    assert len(sprints) == 2

    # Verificar Sprint 1 (4 tarefas: 3 concluídas de ambos os projetos)
    # TASK-001, TASK-002, TASK-003 do ProjectA + TASK-005 do ProjectB
    sprint1 = next(s for s in sprints if s['sprint'] == 'Sprint 1')
    assert sprint1['total_tasks'] == 4
    assert sprint1['completed_tasks'] == 3
    assert sprint1['completion_percentage'] == 75.0
    assert 'tasks_by_status' in sprint1
    assert sprint1['tasks_by_status']['Concluído'] == 3
    assert sprint1['tasks_by_status']['Em Desenvolvimento'] == 1

    # Verificar Sprint 2 (2 tarefas: 1 concluída)
    # TASK-004 do ProjectA + TASK-006 do ProjectB
    sprint2 = next(s for s in sprints if s['sprint'] == 'Sprint 2')
    assert sprint2['total_tasks'] == 2
    assert sprint2['completed_tasks'] == 1
    assert sprint2['completion_percentage'] == 50.0
    assert sprint2['tasks_by_status']['Concluído'] == 1
    assert sprint2['tasks_by_status']['Todo'] == 1


def test_get_sprint_stats_with_project_filter(mock_env_vars, sprint_connector):
    """Testa estatísticas de sprints filtradas por projeto."""
    result = get_sprint_stats(project="ProjectA")

    assert isinstance(result, dict)
    assert result["total_sprints"] == 2

    sprints = result["sprints"]

    # Sprint 1 do ProjectA: 3 tarefas (2 concluídas)
    sprint1 = next(s for s in sprints if s['sprint'] == 'Sprint 1')
    assert sprint1['total_tasks'] == 3
    assert sprint1['completed_tasks'] == 2
    assert sprint1['completion_percentage'] == 66.67

    # Sprint 2 do ProjectA: 1 tarefa (0 concluída)
    sprint2 = next(s for s in sprints if s['sprint'] == 'Sprint 2')
    assert sprint2['total_tasks'] == 1
    assert sprint2['completed_tasks'] == 0
    assert sprint2['completion_percentage'] == 0.0


def test_get_sprint_stats_project_b(mock_env_vars, sprint_connector):
    """Testa estatísticas de sprints para ProjectB."""
    result = get_sprint_stats(project="ProjectB")

    assert isinstance(result, dict)
    assert result["total_sprints"] == 2

    sprints = result["sprints"]

    # Sprint 1 do ProjectB: 1 tarefa (1 concluída) = 100%
    sprint1 = next(s for s in sprints if s['sprint'] == 'Sprint 1')
    assert sprint1['total_tasks'] == 1
    assert sprint1['completed_tasks'] == 1
    assert sprint1['completion_percentage'] == 100.0

    # Sprint 2 do ProjectB: 1 tarefa (1 concluída) = 100%
    sprint2 = next(s for s in sprints if s['sprint'] == 'Sprint 2')
    assert sprint2['total_tasks'] == 1
    assert sprint2['completed_tasks'] == 1
    assert sprint2['completion_percentage'] == 100.0


def test_get_sprint_stats_empty_sprints(mock_env_vars, empty_data):
    """Testa quando não há sprints definidas."""
    from main import reset_connector

    reset_connector()

    with patch.object(LocalFileConnector, '_LocalFileConnector__load_data'), \
         patch.object(LocalFileConnector, '_LocalFileConnector__save_data'):
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        connector = LocalFileConnector(file_path=temp_file.name, sheet_name="Test")
        connector.df = empty_data.copy()

        with patch('main.get_connector', return_value=connector):
            result = get_sprint_stats()

    assert isinstance(result, dict)
    assert result["total_sprints"] == 0
    assert len(result["sprints"]) == 0


def test_get_sprint_stats_no_matching_project(mock_env_vars, sprint_connector):
    """Testa quando o projeto filtrado não existe."""
    result = get_sprint_stats(project="NonExistentProject")

    assert isinstance(result, dict)
    assert result["total_sprints"] == 0
    assert len(result["sprints"]) == 0


def test_get_sprint_stats_tasks_without_sprint(mock_env_vars, tmp_path):
    """Testa quando existem tarefas sem sprint definida."""
    from main import reset_connector

    reset_connector()

    # Criar dados com tarefas sem sprint
    data = {
        'Nome-Projeto': ['TestProject', 'TestProject'],
        'Task-ID': ['TASK-001', 'TASK-002'],
        'Task-ID-Root': ['', ''],
        'Sprint': ['', ''],  # Sem sprint
        'Contexto': ['Backend', 'Frontend'],
        'Descrição': ['Task 1', 'Task 2'],
        'Detalhado': ['Details 1', 'Details 2'],
        'Prioridade': ['Alta', 'Normal'],
        'Status': ['Concluído', 'Todo'],
        'Data-Criação': ['2025-10-20', '2025-10-21'],
        'Data-Solução': ['2025-10-25', '']
    }
    df = pd.DataFrame(data)

    with patch.object(LocalFileConnector, '_LocalFileConnector__load_data'), \
         patch.object(LocalFileConnector, '_LocalFileConnector__save_data'):
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        connector = LocalFileConnector(file_path=temp_file.name, sheet_name="Test")
        connector.df = df

        with patch('main.get_connector', return_value=connector):
            result = get_sprint_stats()

    assert isinstance(result, dict)
    assert result["total_sprints"] == 0
    assert len(result["sprints"]) == 0


def test_get_sprint_stats_100_percent_completion(mock_env_vars, tmp_path):
    """Testa sprint com 100% de conclusão."""
    from main import reset_connector

    reset_connector()

    # Criar dados com todas as tarefas concluídas
    data = {
        'Nome-Projeto': ['TestProject', 'TestProject'],
        'Task-ID': ['TASK-001', 'TASK-002'],
        'Task-ID-Root': ['', ''],
        'Sprint': ['Sprint Complete', 'Sprint Complete'],
        'Contexto': ['Backend', 'Frontend'],
        'Descrição': ['Task 1', 'Task 2'],
        'Detalhado': ['Details 1', 'Details 2'],
        'Prioridade': ['Alta', 'Normal'],
        'Status': ['Concluído', 'Concluído'],
        'Data-Criação': ['2025-10-20', '2025-10-21'],
        'Data-Solução': ['2025-10-25', '2025-10-26']
    }
    df = pd.DataFrame(data)

    with patch.object(LocalFileConnector, '_LocalFileConnector__load_data'), \
         patch.object(LocalFileConnector, '_LocalFileConnector__save_data'):
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        connector = LocalFileConnector(file_path=temp_file.name, sheet_name="Test")
        connector.df = df

        with patch('main.get_connector', return_value=connector):
            result = get_sprint_stats()

    assert isinstance(result, dict)
    assert result["total_sprints"] == 1

    sprint = result["sprints"][0]
    assert sprint['sprint'] == 'Sprint Complete'
    assert sprint['total_tasks'] == 2
    assert sprint['completed_tasks'] == 2
    assert sprint['completion_percentage'] == 100.0
    assert sprint['tasks_by_status']['Concluído'] == 2


def test_get_sprint_stats_0_percent_completion(mock_env_vars, tmp_path):
    """Testa sprint com 0% de conclusão."""
    from main import reset_connector

    reset_connector()

    # Criar dados com nenhuma tarefa concluída
    data = {
        'Nome-Projeto': ['TestProject', 'TestProject'],
        'Task-ID': ['TASK-001', 'TASK-002'],
        'Task-ID-Root': ['', ''],
        'Sprint': ['Sprint Incomplete', 'Sprint Incomplete'],
        'Contexto': ['Backend', 'Frontend'],
        'Descrição': ['Task 1', 'Task 2'],
        'Detalhado': ['Details 1', 'Details 2'],
        'Prioridade': ['Alta', 'Normal'],
        'Status': ['Todo', 'Em Desenvolvimento'],
        'Data-Criação': ['2025-10-20', '2025-10-21'],
        'Data-Solução': ['', '']
    }
    df = pd.DataFrame(data)

    with patch.object(LocalFileConnector, '_LocalFileConnector__load_data'), \
         patch.object(LocalFileConnector, '_LocalFileConnector__save_data'):
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        connector = LocalFileConnector(file_path=temp_file.name, sheet_name="Test")
        connector.df = df

        with patch('main.get_connector', return_value=connector):
            result = get_sprint_stats()

    assert isinstance(result, dict)
    assert result["total_sprints"] == 1

    sprint = result["sprints"][0]
    assert sprint['sprint'] == 'Sprint Incomplete'
    assert sprint['total_tasks'] == 2
    assert sprint['completed_tasks'] == 0
    assert sprint['completion_percentage'] == 0.0
    assert sprint['tasks_by_status']['Todo'] == 1
    assert sprint['tasks_by_status']['Em Desenvolvimento'] == 1
