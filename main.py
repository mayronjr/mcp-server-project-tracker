import os
import sys
import logging
from typing import List, Dict
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from models import TaskStatus, TaskPriority, Task, TaskUpdate, BatchTaskUpdate, BatchTaskAdd

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
RANGE_NAME = f"{SHEET_NAME}!A:J"

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
def list_tasks() -> List[Dict]:
    """
    Lista todas as tarefas da planilha Kanban.

    Returns:
        Lista de dicionários, onde cada dicionário representa uma tarefa com as colunas:
        - Task ID: ID único da tarefa
        - Task ID Root: ID da tarefa raiz relacionada
        - Sprint: Sprint associada
        - Contexto: Contexto da tarefa
        - Descrição: Descrição breve
        - Detalhado: Descrição detalhada
        - Prioridade: Prioridade da tarefa
        - Status: Status atual
        - Data Criação: Data de criação
        - Data Solução: Data de solução
    """
    try:
        logger.info("Listando tarefas da planilha")
        service = get_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])
        if not values:
            logger.info("Nenhuma tarefa encontrada")
            return []

        headers = values[0]
        tasks = [dict(zip(headers, row)) for row in values[1:]]
        logger.info(f"{len(tasks)} tarefa(s) encontrada(s)")
        return tasks
    except Exception as e:
        logger.error(f"Erro ao listar tarefas: {e}")
        return [{"error": f"Erro ao listar tarefas: {str(e)}"}]

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

        # Converter o modelo Pydantic para lista de valores
        values = [[
            task.task_id,
            task.task_id_root,
            task.sprint,
            task.contexto,
            task.descricao,
            task.detalhado,
            task.prioridade,  # Já é string devido ao use_enum_values
            task.status,      # Já é string devido ao use_enum_values
            task.data_criacao,
            task.data_solucao
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
def update_task(task_id: str, updates: Dict) -> str:
    """
    Atualiza uma tarefa existente pelo Task ID.

    Args:
        task_id: ID da tarefa a ser atualizada
        updates: Dicionário com os campos a atualizar.
                 Campos válidos: Task ID Root, Sprint, Contexto, Descrição,
                 Detalhado, Prioridade, Status, Data Criação, Data Solução

    Exemplo:
        updates = {"Status": "Concluído", "Data Solução": "2025-10-23"}
    """
    # Validar se status está sendo atualizado
    if "Status" in updates and updates["Status"] not in [s.value for s in TaskStatus]:
        error_msg = f"Erro: Status '{updates['Status']}' inválido. Use: {', '.join([s.value for s in TaskStatus])}"
        logger.warning(error_msg)
        return error_msg

    # Validar se prioridade está sendo atualizada
    if "Prioridade" in updates and updates["Prioridade"] not in [p.value for p in TaskPriority]:
        error_msg = f"Erro: Prioridade '{updates['Prioridade']}' inválida. Use: {', '.join([p.value for p in TaskPriority])}"
        logger.warning(error_msg)
        return error_msg

    try:
        logger.info(f"Atualizando tarefa '{task_id}' com {len(updates)} campo(s)")
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
            if len(row) > 0 and row[0] == task_id:
                for key, value in updates.items():
                    if key in headers:
                        idx = headers.index(key)
                        while len(row) <= idx:
                            row.append("")
                        row[idx] = value

                sheet.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{SHEET_NAME}!A{i}:J{i}",
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
def batch_add_tasks(tasks: List[Task]) -> Dict:
    """
    Adiciona múltiplas tarefas em uma única operação.

    Args:
        tasks: Lista de objetos Task

    Returns:
        Dicionário com:
        - success_count: Número de tarefas adicionadas com sucesso
        - error_count: Número de erros
        - details: Lista com detalhes de cada adição
    """
    try:
        logger.info(f"Iniciando adição em lote de {len(tasks)} tarefa(s)")

        results = []
        rows_to_add = []

        # Converter cada tarefa para lista de valores
        for task in tasks:
            try:
                row = [
                    task.task_id,
                    task.task_id_root,
                    task.sprint,
                    task.contexto,
                    task.descricao,
                    task.detalhado,
                    task.prioridade,  # Já é string devido ao use_enum_values
                    task.status,      # Já é string devido ao use_enum_values
                    task.data_criacao,
                    task.data_solucao
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
        return {
            "success_count": 0,
            "error_count": len(tasks),
            "details": [{"task_id": getattr(t, 'task_id', 'unknown'), "status": "error", "message": error_msg} for t in tasks]
        }

@server.tool("batch_update_tasks")
def batch_update_tasks(updates: List[TaskUpdate]) -> Dict:
    """
    Atualiza múltiplas tarefas em uma única operação.

    Args:
        updates: Lista de objetos TaskUpdate

    Returns:
        Dicionário com:
        - success_count: Número de tarefas atualizadas com sucesso
        - error_count: Número de erros
        - details: Lista com detalhes de cada atualização
    """
    try:
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

            # Validar status se estiver sendo atualizado
            if "Status" in fields and fields["Status"] not in [s.value for s in TaskStatus]:
                error_msg = f"Status '{fields['Status']}' inválido"
                logger.warning(f"Tarefa '{task_id}': {error_msg}")
                error_count += 1
                results.append({
                    "task_id": task_id,
                    "status": "error",
                    "message": error_msg
                })
                continue

            # Validar prioridade se estiver sendo atualizada
            if "Prioridade" in fields and fields["Prioridade"] not in [p.value for p in TaskPriority]:
                error_msg = f"Prioridade '{fields['Prioridade']}' inválida"
                logger.warning(f"Tarefa '{task_id}': {error_msg}")
                error_count += 1
                results.append({
                    "task_id": task_id,
                    "status": "error",
                    "message": error_msg
                })
                continue

            # Encontrar a tarefa
            task_found = False
            for i, row in enumerate(values[1:], start=2):
                if len(row) > 0 and row[0] == task_id:
                    task_found = True
                    # Atualizar campos
                    for key, value in fields.items():
                        if key in headers:
                            idx = headers.index(key)
                            while len(row) <= idx:
                                row.append("")
                            row[idx] = value

                    # Adicionar ao batch
                    batch_data.append({
                        "range": f"{SHEET_NAME}!A{i}:J{i}",
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
        return {
            "success_count": 0,
            "error_count": len(updates),
            "details": [{"task_id": getattr(u, 'task_id', 'unknown'), "status": "error", "message": error_msg} for u in updates]
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
    logger.info("  - list_tasks: Lista todas as tarefas")
    logger.info("  - add_task: Adiciona uma nova tarefa")
    logger.info("  - update_task: Atualiza uma tarefa existente")
    logger.info("  - batch_add_tasks: Adiciona múltiplas tarefas em lote")
    logger.info("  - batch_update_tasks: Atualiza múltiplas tarefas em lote")
    logger.info("  - get_valid_configs: Retorna configurações válidas")
    logger.info("=" * 60)
    server.run()
