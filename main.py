import os
import sys
import logging
import math
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
    PaginationParams,
    PaginatedResponse
)

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

        Se pagination não fornecido (comportamento legado):
            Lista simples de dicionários com todas as tarefas (filtradas se filters fornecido)

    Exemplos:
        1. Listar todas (legado):
           list_tasks()

        2. Com paginação:
           list_tasks(pagination={"page": 1, "page_size": 20})

        3. Buscar tarefas de alta prioridade:
           list_tasks(filters={"prioridade": ["Alta", "Urgente"]})

        4. Buscar tarefas em desenvolvimento com paginação:
           list_tasks(
               filters={"status": ["Em Desenvolvimento"]},
               pagination={"page": 1, "page_size": 10}
           )

        5. Buscar por texto na descrição:
           list_tasks(filters={"texto_busca": "implementar API"})

        6. Combinar múltiplos filtros:
           list_tasks(
               filters={
                   "prioridade": ["Alta"],
                   "status": ["Todo", "Em Desenvolvimento"],
                   "contexto": "Backend"
               },
               pagination={"page": 1, "page_size": 25}
           )
    """
    try:
        # Se filters não fornecido, criar objeto vazio
        if filters is None:
            filters = SearchFilters()

        logger.info(f"Listando tarefas da planilha com filtros")
        service = get_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values or len(values) < 2:
            logger.info("Nenhuma tarefa encontrada")
            # Se pagination fornecido, retornar resposta paginada vazia
            if pagination:
                return PaginatedResponse(
                    tasks=[],
                    total_count=0,
                    page=pagination.page,
                    page_size=pagination.page_size,
                    total_pages=0
                ).model_dump()
            # Senão, retornar lista vazia (comportamento legado)
            return []

        headers = values[0]
        all_tasks = [dict(zip(headers, row)) for row in values[1:]]

        # Aplicar filtros
        filtered_tasks = []
        for task in all_tasks:
            # Garantir que task tenha todas as colunas necessárias
            task_id = task.get("Task ID", "")
            prioridade = task.get("Prioridade", "")
            status = task.get("Status", "")
            contexto = task.get("Contexto", "")
            projeto = task.get("Projeto", "")
            descricao = task.get("Descrição", "")
            detalhado = task.get("Detalhado", "")
            sprint = task.get("Sprint", "")

            # Filtro por Task ID (busca exata)
            if filters.task_id and task_id != filters.task_id:
                continue

            # Filtro por prioridade
            if filters.prioridade:
                prioridades_str = [p.value if hasattr(p, 'value') else str(p) for p in filters.prioridade]
                if prioridade not in prioridades_str:
                    continue

            # Filtro por status
            if filters.status:
                status_str = [s.value if hasattr(s, 'value') else str(s) for s in filters.status]
                if status not in status_str:
                    continue

            # Filtro por contexto (busca parcial, case-insensitive)
            if filters.contexto and filters.contexto.lower() not in contexto.lower():
                continue

            # Filtro por projeto (busca parcial, case-insensitive)
            if filters.projeto and filters.projeto.lower() not in projeto.lower():
                continue

            # Filtro por sprint (busca exata)
            if filters.sprint and sprint != filters.sprint:
                continue

            # Filtro por texto em Descrição e Detalhado (case-insensitive)
            if filters.texto_busca:
                texto_lower = filters.texto_busca.lower()
                if texto_lower not in descricao.lower() and texto_lower not in detalhado.lower():
                    continue

            # Se passou por todos os filtros, adicionar à lista
            filtered_tasks.append(task)

        # Se paginação não fornecida, retornar todas as tarefas filtradas (comportamento legado)
        if pagination is None:
            logger.info(f"{len(filtered_tasks)} tarefa(s) encontrada(s)")
            return filtered_tasks

        # Aplicar paginação
        total_count = len(filtered_tasks)
        total_pages = math.ceil(total_count / pagination.page_size) if total_count > 0 else 0

        # Ajustar página se for maior que o total
        current_page = min(pagination.page, total_pages) if total_pages > 0 else 1

        # Calcular índices para slice
        start_idx = (current_page - 1) * pagination.page_size
        end_idx = start_idx + pagination.page_size

        # Obter tarefas da página atual
        paginated_tasks = filtered_tasks[start_idx:end_idx]

        # Construir resposta paginada
        response = PaginatedResponse(
            tasks=paginated_tasks,
            total_count=total_count,
            page=current_page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )

        logger.info(
            f"{total_count} tarefa(s) encontrada(s), "
            f"retornando {len(paginated_tasks)} da página {current_page}/{total_pages}"
        )

        return response.model_dump()

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
        service = get_sheets_service()
        sheet = service.spreadsheets()

        # Gerar data_criacao automaticamente
        data_criacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Converter o modelo Pydantic para lista de valores
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
        body = {"values": values}
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption="RAW",
            body=body
        ).execute()
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
        service = get_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values or len(values) < 2:
            warning_msg = "Nenhuma tarefa encontrada na planilha."
            logger.warning(warning_msg)
            return warning_msg

        headers = values[0]

        for i, row in enumerate(values[1:], start=2):  # linha real começa em 2
            if len(row) > 1 and row[1] == task_id:
                for key, value in sheet_updates.items():
                    if key in headers:
                        idx = headers.index(key)
                        while len(row) <= idx:
                            row.append("")
                        row[idx] = value

                sheet.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{SHEET_NAME}!A{i}:K{i}",
                    valueInputOption="RAW",
                    body={"values": [row]}
                ).execute()
                success_msg = f"Tarefa '{task_id}' atualizada com sucesso."
                logger.info(success_msg)
                return success_msg

        warning_msg = f"Tarefa '{task_id}' não encontrada."
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

        # Adicionar todas as tarefas válidas de uma vez
        if rows_to_add:
            service = get_sheets_service()
            sheet = service.spreadsheets()
            body = {"values": rows_to_add}
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME,
                valueInputOption="RAW",
                body=body
            ).execute()

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
        service = get_sheets_service()
        sheet = service.spreadsheets()

        # Buscar todas as tarefas uma vez
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values or len(values) < 2:
            warning_msg = "Nenhuma tarefa encontrada na planilha."
            logger.warning(warning_msg)
            return {
                "success_count": 0,
                "error_count": len(updates),
                "details": [{"task_id": getattr(u, 'task_id', 'unknown'), "status": "error", "message": warning_msg} for u in updates]
            }

        headers = values[0]
        results = []
        success_count = 0
        error_count = 0
        batch_data = []

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

        # Processar cada atualização
        for update_item in updates:
            task_id = update_item.task_id
            fields = update_item.fields

            if not task_id:
                error_count += 1
                results.append({
                    "task_id": "unknown",
                    "status": "error",
                    "message": "task_id não fornecido"
                })
                continue

            # Converter o modelo Pydantic para dict, excluindo valores None
            fields_dict = fields.model_dump(exclude_none=True)

            if not fields_dict:
                error_count += 1
                results.append({
                    "task_id": task_id,
                    "status": "error",
                    "message": "Nenhum campo para atualizar foi fornecido"
                })
                continue

            # Converter para formato de headers do Google Sheets
            sheet_updates = {field_to_header[k]: v for k, v in fields_dict.items() if k in field_to_header}

            # Verificar se o status está sendo alterado para um estado final
            final_statuses = [TaskStatus.CONCLUIDO.value, TaskStatus.CANCELADO.value, TaskStatus.NAO_RELACIONADO.value]
            if fields.status and fields.status in final_statuses:
                # Adicionar data_solucao automaticamente
                sheet_updates["Data Solução"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Encontrar a tarefa (Task ID está na coluna 1, não 0)
            task_found = False
            for i, row in enumerate(values[1:], start=2):
                if len(row) > 1 and row[1] == task_id:
                    task_found = True
                    # Atualizar campos
                    for key, value in sheet_updates.items():
                        if key in headers:
                            idx = headers.index(key)
                            while len(row) <= idx:
                                row.append("")
                            row[idx] = value

                    # Adicionar ao batch
                    batch_data.append({
                        "range": f"{SHEET_NAME}!A{i}:K{i}",
                        "values": [row]
                    })
                    success_count += 1
                    results.append({
                        "task_id": task_id,
                        "status": "success",
                        "message": f"Tarefa atualizada com sucesso"
                    })
                    break

            if not task_found:
                error_count += 1
                results.append({
                    "task_id": task_id,
                    "status": "error",
                    "message": "Tarefa não encontrada"
                })

        # Executar atualização em lote usando batchUpdate
        if batch_data:
            batch_body = {
                "valueInputOption": "RAW",
                "data": batch_data
            }
            sheet.values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=batch_body
            ).execute()

        summary = {
            "success_count": success_count,
            "error_count": error_count,
            "details": results
        }

        logger.info(f"Atualização em lote concluída: {success_count} sucesso(s), {error_count} erro(s)")
        return summary

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
    logger.info("=" * 60)
    logger.info("Iniciando servidor MCP: kanban-sheets")
    logger.info(f"Planilha ID: {SPREADSHEET_ID}")
    logger.info(f"Aba: {SHEET_NAME}")
    logger.info("Protocolo: STDIO (Standard Input/Output)")
    logger.info("")
    logger.info("Para conectar este servidor MCP, adicione no seu cliente MCP:")
    logger.info("  {")
    logger.info('    "mcpServers": {')
    logger.info('      "kanban-sheets": {')
    logger.info('        "command": "uv",')
    logger.info('        "args": ["run", "main.py"]')
    logger.info("      }")
    logger.info("    }")
    logger.info("  }")
    logger.info("")
    logger.info("Ferramentas disponíveis:")
    logger.info("  - list_tasks: Lista/busca tarefas com filtros e paginação")
    logger.info("  - add_task: Adiciona uma nova tarefa")
    logger.info("  - update_task: Atualiza uma tarefa existente")
    logger.info("  - batch_add_tasks: Adiciona múltiplas tarefas em lote")
    logger.info("  - batch_update_tasks: Atualiza múltiplas tarefas em lote")
    logger.info("  - get_valid_configs: Retorna configurações válidas")
    logger.info("=" * 60)
    server.run()
