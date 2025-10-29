import os
import sys
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from models import (
    TaskStatus,
    TaskPriority,
    Task,
    TaskUpdateFields,
    BatchTaskUpdate,
    BatchTaskAdd,
    SearchFilters,
    PaginationParams
)
from utils.planilhas_connector import PlanilhasConnector

# Configurar logging para stderr (nunca usar stdout em servidores MCP STDIO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("kanban-sheets")

load_dotenv('.env')

# Configuração: variáveis de ambiente
SPREADSHEET_ID = os.getenv("KANBAN_SHEET_ID")
SHEET_NAME = os.getenv("KANBAN_SHEET_NAME", "Back-End")  # Nome da aba, padrão "Back-End"
RANGE_NAME = f"{SHEET_NAME}!A:K"

if not SPREADSHEET_ID:
    raise EnvironmentError("Defina a variável de ambiente KANBAN_SHEET_ID com o ID da planilha.")

# Validar existência do arquivo de credenciais
CREDENTIALS_FILE = "credentials.json"
if not os.path.exists(CREDENTIALS_FILE):
    raise FileNotFoundError(
        f"Arquivo de credenciais '{CREDENTIALS_FILE}' não encontrado. "
        "Certifique-se de que o arquivo existe no diretório do projeto."
    )

# Inicializa o MCP server
server = FastMCP("kanban-sheets")
logger.info("Servidor MCP inicializado: kanban-sheets")

# Autenticação via Service Account (arquivo credentials.json)
def get_sheets_service():
    """Cria e retorna um serviço autenticado do Google Sheets API."""
    try:
        creds = Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        logger.debug("Credenciais carregadas com sucesso")
        return build("sheets", "v4", credentials=creds)
    except Exception as e:
        logger.error(f"Erro ao carregar credenciais: {e}")
        raise

# Inicializar connector (será usado por todas as funções)
_connector: Optional[PlanilhasConnector] = None

def get_connector() -> PlanilhasConnector:
    """Retorna a instância do PlanilhasConnector, criando-a se necessário."""
    global _connector
    if _connector is None:
        if not SPREADSHEET_ID:
            raise EnvironmentError("SPREADSHEET_ID não definido")
        service = get_sheets_service()
        _connector = PlanilhasConnector(
            service=service,
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        )
        logger.info("PlanilhasConnector inicializado")
    return _connector

def reset_connector():
    """Reset o connector (útil para testes)."""
    global _connector
    _connector = None

@server.tool("get_one_task")
def get_one_task(
    project: str,
    task_id: str
) -> Dict:
    """
    Busca uma tarefa específica pelo ID da tarefa e projeto.

    Args:
        project: Nome do Projeto
        task_id: ID único da tarefa

    Returns:
        Dicionário com os dados da tarefa encontrada, ou erro se não encontrada

    Exemplo:
        get_one_task(project="MCP Server", task_id="TASK-001")
    """
    try:
        logger.info(f"Buscando tarefa '{task_id}' do projeto '{project}'")
        connector = get_connector()
        result = connector.get_one(project_id=project, task_id=task_id)

        if "error" in result:
            logger.warning(result["error"])
        else:
            logger.info(f"Tarefa '{task_id}' encontrada")

        return result

    except Exception as e:
        error_msg = f"Erro ao buscar tarefa: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

@server.tool("list_tasks")
def list_tasks(
    filters: Optional[SearchFilters] = None,
    pagination: Optional[PaginationParams] = None
) -> Union[List[Dict], Dict]:
    """
    Lista e busca tarefas da planilha Kanban com filtros avançados e paginação opcional.

    Args:
        filters: Filtros de busca (opcional). Critérios:
            - prioridade: Lista de prioridades (Baixa, Normal, Alta, Urgente)
            - status: Lista de status para filtrar
            - contexto: Filtro por contexto (busca parcial, case-insensitive)
            - projeto: Filtro por projeto (busca parcial, case-insensitive)
            - texto_busca: Busca em Descrição e Detalhado (case-insensitive)
            - task_id: Busca por Task ID específico
            - sprint: Filtro por Sprint
        pagination: Parâmetros de paginação (opcional). Se não fornecido, retorna todas as tarefas.

    Returns:
        Se pagination fornecido:
            Dicionário PaginatedResponse com:
            - tasks: Lista de tarefas da página atual
            - total_count: Total de tarefas encontradas
            - page: Página atual
            - page_size: Itens por página
            - total_pages: Total de páginas
            - has_next: Se existe próxima página
            - has_previous: Se existe página anterior

    """
    try:
        # Se filters não fornecido, criar objeto vazio
        if filters is None:
            filters = SearchFilters()

        # Log dos filtros recebidos
        filters_dict = filters.model_dump(exclude_none=True)
        logger.info(f"Listando tarefas com filtros: {filters_dict}")

        # Converter filtros para formato do connector
        connector_filters = {}
        if filters.prioridade:
            connector_filters['prioridade'] = [p.value if hasattr(p, 'value') else str(p) for p in filters.prioridade]
        if filters.status:
            connector_filters['status'] = [s.value if hasattr(s, 'value') else str(s) for s in filters.status]
        if filters.contexto:
            connector_filters['contexto'] = filters.contexto
        if filters.projeto:
            connector_filters['projeto'] = filters.projeto
        if filters.texto_busca:
            connector_filters['texto_busca'] = filters.texto_busca
        if filters.task_id:
            connector_filters['task_id'] = filters.task_id
        if filters.sprint:
            connector_filters['sprint'] = filters.sprint

        # Converter pagination para formato do connector
        connector_pagination = None
        if pagination:
            connector_pagination = {
                'page': pagination.page,
                'page_size': pagination.page_size
            }

        # Usar connector
        connector = get_connector()
        result = connector.search_for(
            filters=connector_filters if connector_filters else None,
            pagination=connector_pagination
        )

        # Se resultado é lista (sem paginação)
        if isinstance(result, list):
            logger.info(f"{len(result)} tarefa(s) encontrada(s)")
            return result

        # Se resultado é dicionário (com paginação)
        logger.info(
            f"{result['total_count']} tarefa(s) encontrada(s), "
            f"retornando {len(result['tasks'])} da página {result['page']}/{result['total_pages']}"
        )
        return result

    except Exception as e:
        logger.error(f"Erro ao listar tarefas: {e}")
        error_msg = f"Erro ao listar tarefas: {str(e)}"
        # Retornar formato apropriado baseado na presença de pagination
        if pagination:
            return {
                "tasks": [],
                "total_count": 0,
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False,
                "error": error_msg
            }
        return [{"error": error_msg}]

@server.tool("add_task")
def add_task(task: Task) -> str:
    """
    Adiciona uma nova tarefa na planilha.

    Args:
        task: Objeto Task com todos os campos da tarefa
    """
    try:
        logger.info(f"Adicionando tarefa '{task.task_id}'")

        # Gerar data_criacao automaticamente
        data_criacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Converter o modelo Pydantic para lista de valores
        # Ordem das colunas: Nome Projeto, Task ID, Task ID Root, Sprint, Contexto,
        # Descrição, Detalhado, Prioridade, Status, Data Criação, Data Solução
        values = [[
            task.project,
            task.task_id,
            task.task_id_root,
            task.sprint,
            task.contexto,
            task.descricao,
            task.detalhado,
            task.prioridade,  # Já é string devido ao use_enum_values
            task.status,      # Já é string devido ao use_enum_values
            data_criacao,
            ""  # data_solucao vazia por padrão
        ]]

        # Usar connector
        connector = get_connector()
        result = connector.add(new_task_list=values)

        if "error" in result:
            error_msg = result["error"]
            logger.error(error_msg)
            return error_msg

        success_msg = f"Tarefa '{task.task_id}' adicionada com sucesso."
        logger.info(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"Erro ao adicionar tarefa: {str(e)}"
        logger.error(error_msg)
        return error_msg

@server.tool("update_task")
def update_task(task_id: str, updates: TaskUpdateFields) -> str:
    """
    Atualiza uma tarefa existente pelo Task ID.

    Args:
        task_id: ID da tarefa a ser atualizada
        updates: Objeto TaskUpdateFields com os campos a atualizar.
                 Campos válidos: task_id_root, sprint, contexto, descricao,
                 detalhado, prioridade, status

    Exemplo:
        updates = TaskUpdateFields(status="Concluído")

    Nota: data_solucao é automaticamente definida quando o status é alterado
          para "Concluído", "Cancelado" ou "Não Relacionado"
    """
    # Mapeamento de campos Python para nomes de colunas do Google Sheets
    field_to_header = {
        "task_id_root": "Task ID Root",
        "sprint": "Sprint",
        "contexto": "Contexto",
        "descricao": "Descrição",
        "detalhado": "Detalhado",
        "prioridade": "Prioridade",
        "status": "Status"
    }

    # Converter o modelo Pydantic para dict, excluindo valores None
    updates_dict = updates.model_dump(exclude_none=True)

    if not updates_dict:
        error_msg = "Erro: Nenhum campo para atualizar foi fornecido."
        logger.warning(error_msg)
        return error_msg

    # Converter para formato de headers do Google Sheets
    sheet_updates = {field_to_header[k]: v for k, v in updates_dict.items() if k in field_to_header}

    # Verificar se o status está sendo alterado para um estado final
    final_statuses = [TaskStatus.CONCLUIDO.value, TaskStatus.CANCELADO.value, TaskStatus.NAO_RELACIONADO.value]
    if updates.status and updates.status in final_statuses:
        # Adicionar data_solucao automaticamente
        sheet_updates["Data Solução"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        logger.info(f"Atualizando tarefa '{task_id}' com {len(sheet_updates)} campo(s)")

        # Usar connector
        connector = get_connector()
        result = connector.update_one(update_task_list=[{
            'task_id': task_id,
            'updates': sheet_updates
        }])

        if "error" in result:
            error_msg = result["error"]
            logger.error(error_msg)
            return error_msg

        # Verificar resultado
        if result['success_count'] > 0:
            success_msg = f"Tarefa '{task_id}' atualizada com sucesso."
            logger.info(success_msg)
            return success_msg
        else:
            # Pegar mensagem de erro dos detalhes
            error_detail = result['details'][0] if result['details'] else {}
            warning_msg = error_detail.get('message', f"Tarefa '{task_id}' não encontrada.")
            logger.warning(warning_msg)
            return warning_msg

    except Exception as e:
        error_msg = f"Erro ao atualizar tarefa: {str(e)}"
        logger.error(error_msg)
        return error_msg

@server.tool("batch_add_tasks")
def batch_add_tasks(batch: BatchTaskAdd) -> Dict:
    """
    Adiciona múltiplas tarefas em uma única operação.

    Args:
        batch: Objeto BatchTaskAdd contendo lista de tarefas

    Returns:
        Dicionário com:
        - success_count: Número de tarefas adicionadas com sucesso
        - error_count: Número de erros
        - details: Lista com detalhes de cada adição
    """
    try:
        tasks = batch.tasks
        logger.info(f"Iniciando adição em lote de {len(tasks)} tarefa(s)")

        results = []
        rows_to_add = []

        # Converter cada tarefa para lista de valores
        for task in tasks:
            try:
                # Gerar data_criacao automaticamente
                data_criacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                row = [
                    task.project,
                    task.task_id,
                    task.task_id_root,
                    task.sprint,
                    task.contexto,
                    task.descricao,
                    task.detalhado,
                    task.prioridade,  # Já é string devido ao use_enum_values
                    task.status,      # Já é string devido ao use_enum_values
                    data_criacao,
                    ""  # data_solucao vazia por padrão
                ]
                rows_to_add.append(row)
                results.append({
                    "task_id": task.task_id,
                    "status": "success",
                    "message": "Tarefa preparada para adição"
                })
            except Exception as e:
                results.append({
                    "task_id": getattr(task, 'task_id', 'unknown'),
                    "status": "error",
                    "message": f"Erro ao preparar tarefa: {str(e)}"
                })

        # Adicionar todas as tarefas válidas de uma vez usando connector
        if rows_to_add:
            connector = get_connector()
            add_result = connector.add(new_task_list=rows_to_add)

            if "error" in add_result:
                # Se houve erro na adição, marcar todas como erro
                for result in results:
                    if result["status"] == "success":
                        result["status"] = "error"
                        result["message"] = add_result["error"]
            else:
                # Atualizar mensagens de sucesso
                for result in results:
                    if result["status"] == "success":
                        result["message"] = "Tarefa adicionada com sucesso"

        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = sum(1 for r in results if r["status"] == "error")

        summary = {
            "success_count": success_count,
            "error_count": error_count,
            "details": results
        }

        logger.info(f"Adição em lote concluída: {success_count} sucesso(s), {error_count} erro(s)")
        return summary

    except Exception as e:
        error_msg = f"Erro ao executar adição em lote: {str(e)}"
        logger.error(error_msg)
        task_count = len(batch.tasks) if hasattr(batch, 'tasks') else 0
        return {
            "success_count": 0,
            "error_count": task_count,
            "details": [{"task_id": getattr(t, 'task_id', 'unknown'), "status": "error", "message": error_msg} for t in (batch.tasks if hasattr(batch, 'tasks') else [])]
        }

@server.tool("batch_update_tasks")
def batch_update_tasks(batch: BatchTaskUpdate) -> Dict:
    """
    Atualiza múltiplas tarefas em uma única operação.

    Args:
        batch: Objeto BatchTaskUpdate contendo lista de atualizações

    Returns:
        Dicionário com:
        - success_count: Número de tarefas atualizadas com sucesso
        - error_count: Número de erros
        - details: Lista com detalhes de cada atualização
    """
    try:
        updates = batch.updates
        logger.info(f"Iniciando atualização em lote de {len(updates)} tarefa(s)")

        # Mapeamento de campos Python para nomes de colunas do Google Sheets
        field_to_header = {
            "task_id_root": "Task ID Root",
            "sprint": "Sprint",
            "contexto": "Contexto",
            "descricao": "Descrição",
            "detalhado": "Detalhado",
            "prioridade": "Prioridade",
            "status": "Status"
        }

        # Preparar lista de atualizações para o connector
        update_list = []
        for update_item in updates:
            task_id = update_item.task_id
            fields = update_item.fields

            if not task_id:
                continue

            # Converter o modelo Pydantic para dict, excluindo valores None
            fields_dict = fields.model_dump(exclude_none=True)

            if not fields_dict:
                continue

            # Converter para formato de headers do Google Sheets
            sheet_updates = {field_to_header[k]: v for k, v in fields_dict.items() if k in field_to_header}

            # Verificar se o status está sendo alterado para um estado final
            final_statuses = [TaskStatus.CONCLUIDO.value, TaskStatus.CANCELADO.value, TaskStatus.NAO_RELACIONADO.value]
            if fields.status and fields.status in final_statuses:
                # Adicionar data_solucao automaticamente
                sheet_updates["Data Solução"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            update_list.append({
                'task_id': task_id,
                'updates': sheet_updates
            })

        # Usar connector
        connector = get_connector()
        result = connector.update_one(update_task_list=update_list)

        logger.info(f"Atualização em lote concluída: {result['success_count']} sucesso(s), {result['error_count']} erro(s)")
        return result

    except Exception as e:
        error_msg = f"Erro ao executar atualização em lote: {str(e)}"
        logger.error(error_msg)
        update_count = len(batch.updates) if hasattr(batch, 'updates') else 0
        return {
            "success_count": 0,
            "error_count": update_count,
            "details": [{"task_id": getattr(u, 'task_id', 'unknown'), "status": "error", "message": error_msg} for u in (batch.updates if hasattr(batch, 'updates') else [])]
        }

@server.tool("get_valid_configs")
def get_valid_configs() -> Dict[str, List[str]]:
    """
    Retorna as configurações válidas para Status e Prioridade.

    Returns:
        Dicionário contendo:
        - valid_task_status: Lista de status válidos
        - valid_task_priorities: Lista de prioridades válidas
    """
    logger.info("Retornando configurações válidas")
    return {
        'valid_task_status': [status.value for status in TaskStatus],
        'valid_task_priorities': [priority.value for priority in TaskPriority]
    }

if __name__ == "__main__":
    server.run()
