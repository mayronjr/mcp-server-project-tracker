import os
import sys
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from models import (
    TaskStatus,
    TaskPriority,
    BatchTaskUpdate,
    BatchTaskAdd,
    SearchFilters,
    PaginationParams
)
from utils.local_file_connector import LocalFileConnector

# Configurar logging para stderr (nunca usar stdout em servidores MCP STDIO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("kanban-sheets")

load_dotenv('.env')

# Configuração: variáveis de ambiente
KANBAN_FILE_PATH = os.getenv("KANBAN_FILE_PATH", "kanban.xlsx")
KANBAN_SHEET_NAME = os.getenv("KANBAN_SHEET_NAME")  # Nome da aba (apenas para Excel, opcional)

# Validar caminho do arquivo
if not KANBAN_FILE_PATH:
    raise EnvironmentError("Defina a variável de ambiente KANBAN_FILE_PATH com o caminho do arquivo Kanban.")

# Verificar se o arquivo existe ou pode ser criado
file_dir = os.path.dirname(KANBAN_FILE_PATH)
if file_dir and not os.path.exists(file_dir):
    raise FileNotFoundError(f"Diretório não encontrado: {file_dir}")

# Inicializa o MCP server
server = FastMCP("kanban-sheets")
logger.info("Servidor MCP inicializado: kanban-sheets")

# Inicializar connector (será usado por todas as funções)
_connector: Optional[LocalFileConnector] = None

def get_connector() -> LocalFileConnector:
    """Retorna a instância do LocalFileConnector, criando-a se necessário."""
    global _connector
    if _connector is None:
        _connector = LocalFileConnector(
            file_path=KANBAN_FILE_PATH,
            sheet_name=KANBAN_SHEET_NAME
        )
        logger.info(f"LocalFileConnector inicializado para arquivo: {KANBAN_FILE_PATH}")
    return _connector

def reset_connector():
    """Reset o connector (útil para testes)."""
    global _connector
    _connector = None

@server.tool("get_one_or_more_tasks")
def get_one_or_more_tasks(
    project: str,
    task_id_list: List[str]
) -> List[Dict]:
    """
    Busca uma ou mais tarefas específicas pelos IDs das tarefas e projeto.

    Args:
        project: Nome do Projeto
        task_id_list: Lista de IDs únicos das tarefas

    Returns:
        Lista de dicionários com os dados das tarefas encontradas.
        Tarefas não encontradas ou com erro retornam objeto com campo 'error'.

    Exemplo:
        get_one_or_more_tasks(project="MCP Server", task_id_list=["TASK-001", "TASK-002"])
    """
    if not task_id_list:
        return []

    logger.info(f"Buscando {len(task_id_list)} tarefa(s) do projeto '{project}': {', '.join(task_id_list)}")
    connector = get_connector()
    task_list = []

    for task_id in task_id_list:
        try:
            result = connector.get_one(project_id=project, task_id=task_id)
            if "error" in result:
                logger.warning(f"Tarefa '{task_id}' não encontrada: {result['error']}")
                task_list.append({
                    'task_id': task_id,
                    'project': project,
                    'error': result['error']
                })
            else:
                logger.info(f"Tarefa '{task_id}' encontrada")
                task_list.append(result)
        except Exception as e:
            error_msg = f"Erro ao buscar tarefa '{task_id}': {str(e)}"
            logger.error(error_msg)
            task_list.append({
                'task_id': task_id,
                'project': project,
                'error': error_msg
            })

    logger.info(f"Busca concluída: {sum(1 for t in task_list if 'error' not in t)} tarefa(s) encontrada(s), {sum(1 for t in task_list if 'error' in t)} erro(s)")
    return task_list

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
                connector = get_connector()
                task_x = connector.get_one(project_id=task.project, task_id=task.task_id)
                if task_x.get('error', None):
                    rows_to_add.append(row)
                    results.append({
                        "task_id": task.task_id,
                        "status": "success",
                        "message": "Tarefa preparada para adição"
                    })
                else:
                    results.append({
                        "task_id": getattr(task, 'task_id', 'unknown'),
                        "status": "error",
                        "message": f"Já existe task nesse projeto com o ID fornecido"
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
            project = update_item.project
            task_id = update_item.task_id
            fields = update_item.fields

            if not project or not task_id:
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
                'project': project,
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

@server.tool("get_sprint_stats")
def get_sprint_stats(project: Optional[str] = None) -> Dict:
    """
    Retorna estatísticas de sprints com porcentagem de conclusão das tarefas.

    Args:
        project: Nome do projeto para filtrar sprints (opcional). Se não fornecido, retorna stats de todas as sprints.

    Returns:
        Dicionário com:
        - sprints: Lista de estatísticas por sprint contendo:
            - sprint: Nome da sprint
            - total_tasks: Total de tarefas na sprint
            - completed_tasks: Número de tarefas concluídas
            - completion_percentage: Porcentagem de conclusão (0-100)
            - tasks_by_status: Distribuição de tarefas por status
        - total_sprints: Total de sprints encontradas

    Exemplo:
        get_sprint_stats()
        get_sprint_stats(project="MCP Server")
    """
    try:
        logger.info(f"Calculando estatísticas de sprints" + (f" para o projeto '{project}'" if project else ""))

        connector = get_connector()
        sprint_stats = connector.get_sprint_stats(project=project)

        # Verificar se houve erro
        if sprint_stats and isinstance(sprint_stats, list) and len(sprint_stats) > 0:
            if "error" in sprint_stats[0]:
                logger.error(f"Erro ao calcular estatísticas: {sprint_stats[0]['error']}")
                return {
                    "sprints": [],
                    "total_sprints": 0,
                    "error": sprint_stats[0]['error']
                }

        total_sprints = len(sprint_stats)
        logger.info(f"Estatísticas calculadas para {total_sprints} sprint(s)")

        return {
            "sprints": sprint_stats,
            "total_sprints": total_sprints
        }

    except Exception as e:
        error_msg = f"Erro ao calcular estatísticas de sprints: {str(e)}"
        logger.error(error_msg)
        return {
            "sprints": [],
            "total_sprints": 0,
            "error": error_msg
        }

if __name__ == "__main__":
    server.run()
