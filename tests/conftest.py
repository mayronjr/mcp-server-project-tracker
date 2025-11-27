"""
Configuração de fixtures para testes do servidor MCP Kanban Sheets.
"""
import pytest
from unittest.mock import patch
import pandas as pd


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Mock das variáveis de ambiente necessárias."""
    test_file = tmp_path / "test_kanban.xlsx"
    monkeypatch.setenv("KANBAN_FILE_PATH", str(test_file))
    monkeypatch.setenv("KANBAN_SHEET_NAME", "Test-Sheet")


@pytest.fixture
def sample_data() -> pd.DataFrame:
    """Dados de exemplo de um arquivo Kanban."""
    data = {
        'Nome-Projeto': ['TestProject', 'TestProject', 'TestProject'],
        'Task-ID': ['TASK-001', 'TASK-002', 'TASK-003'],
        'Task-ID-Root': ['TASK-001', 'TASK-002', 'TASK-001'],
        'Sprint': ['Sprint 1', 'Sprint 1', 'Sprint 2'],
        'Contexto': ['Backend', 'Frontend', 'Backend'],
        'Descrição': ['Implementar API', 'Criar interface', 'Adicionar testes'],
        'Detalhado': ['Criar endpoints REST', 'Interface do usuário', 'Testes unitários e integração'],
        'Prioridade': ['Alta', 'Normal', 'Urgente'],
        'Status': ['Em Desenvolvimento', 'Todo', 'Todo'],
        'Data-Criação': ['2025-10-20', '2025-10-21', '2025-10-22'],
        'Data-Solução': ['', '', '']
    }
    return pd.DataFrame(data)


@pytest.fixture
def empty_data() -> pd.DataFrame:
    """Dados de um arquivo vazio (apenas estrutura)."""
    return pd.DataFrame(columns=[
        'Nome-Projeto', 'Task-ID', 'Task-ID-Root', 'Sprint', 'Contexto',
        'Descrição', 'Detalhado', 'Prioridade', 'Status',
        'Data-Criação', 'Data-Solução'
    ])


@pytest.fixture
def temp_excel_file(tmp_path, sample_data):
    """Cria um arquivo Excel temporário com dados de teste."""
    file_path = tmp_path / "test_kanban.xlsx"

    # Converter colunas de volta para formato com espaços
    df_to_save = sample_data.copy()
    df_to_save.columns = [col.replace('-', ' ') for col in df_to_save.columns]

    # Salvar arquivo Excel
    df_to_save.to_excel(file_path, sheet_name='Test-Sheet', index=False)

    return str(file_path)


@pytest.fixture
def temp_csv_file(tmp_path, sample_data):
    """Cria um arquivo CSV temporário com dados de teste."""
    file_path = tmp_path / "test_kanban.csv"

    # Converter colunas de volta para formato com espaços
    df_to_save = sample_data.copy()
    df_to_save.columns = [col.replace('-', ' ') for col in df_to_save.columns]

    # Salvar arquivo CSV
    df_to_save.to_csv(file_path, index=False)

    return str(file_path)


@pytest.fixture
def mock_connector(sample_data, tmp_path):
    """Mock do LocalFileConnector com dados de teste."""
    from utils.local_file_connector import LocalFileConnector

    # Criar arquivo temporário
    file_path = tmp_path / "test_kanban.xlsx"

    # Mock do __load_data e __save_data para evitar I/O real
    with patch.object(LocalFileConnector, '_LocalFileConnector__load_data'), \
         patch.object(LocalFileConnector, '_LocalFileConnector__save_data'):

        # Criar connector
        connector = LocalFileConnector(
            file_path=str(file_path),
            sheet_name="Test-Sheet"
        )

        # Injetar dados de teste diretamente
        connector.df = sample_data.copy()

        with patch('main.get_connector') as mock_get_conn:
            mock_get_conn.return_value = connector
            yield connector


@pytest.fixture(autouse=True)
def reset_connector_cache():
    """Reset o connector entre cada teste."""
    import main
    yield
    main.reset_connector()


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
        "data_solucao": ""
    }


@pytest.fixture
def empty_sheet_data():
    """Dados de planilha vazia (apenas cabeçalho)."""
    return {
        'values': [
            ['Nome Projeto', 'Task ID', 'Task ID Root', 'Sprint', 'Contexto',
             'Descrição', 'Detalhado', 'Prioridade', 'Status',
             'Data Criação', 'Data Solução']
        ]
    }
