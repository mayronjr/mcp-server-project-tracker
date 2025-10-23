import os
import sys
import logging
from typing import List, Dict
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from models import TaskStatus, TaskPriority

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
def add_task(
    task_id: str,
    contexto: str,
    descricao: str,
    prioridade: str,
    status: str,
    task_id_root: str = "",
    sprint: str = "",
    detalhado: str = "",
    data_criacao: str = "",
    data_solucao: str = ""
) -> str:
    """
    Adiciona uma nova tarefa na planilha.

    Colunas: Task ID, Task ID Root, Sprint, Contexto, Descrição, Detalhado,
             Prioridade, Status, Data Criação, Data Solução

    Args:
        task_id: ID único da tarefa (obrigatório)
        contexto: Contexto da tarefa (obrigatório)
        descricao: Descrição da tarefa (obrigatório)
        prioridade: Prioridade (Baixa, Normal, Alta, Urgente)
        status: Status da tarefa (Todo, Em Desenvolvimento, etc)
        task_id_root: ID da tarefa raiz relacionada
        sprint: Sprint associada
        detalhado: Descrição detalhada
        data_criacao: Data de criação
        data_solucao: Data de solução
    """
    # Validar prioridade
    if prioridade not in [p.value for p in TaskPriority]:
        error_msg = f"Erro: Prioridade '{prioridade}' inválida. Use: {', '.join([p.value for p in TaskPriority])}"
        logger.warning(error_msg)
        return error_msg

    # Validar status
    if status not in [s.value for s in TaskStatus]:
        error_msg = f"Erro: Status '{status}' inválido. Use: {', '.join([s.value for s in TaskStatus])}"
        logger.warning(error_msg)
        return error_msg

    try:
        logger.info(f"Adicionando tarefa '{task_id}'")
        service = get_sheets_service()
        sheet = service.spreadsheets()
        values = [[
            task_id,
            task_id_root,
            sprint,
            contexto,
            descricao,
            detalhado,
            prioridade,
            status,
            data_criacao,
            data_solucao
        ]]
        body = {"values": values}
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption="RAW",
            body=body
        ).execute()
        success_msg = f"Tarefa '{task_id}' adicionada com sucesso."
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
