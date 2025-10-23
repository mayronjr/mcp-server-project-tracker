import os
from typing import List, Dict
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from mcp import MCPServer

# Configuração: variável de ambiente com o ID da planilha
SPREADSHEET_ID = os.getenv("KANBAN_SHEET_ID")
RANGE_NAME = "Sheet1!A:E"  # Ajuste se sua aba tiver outro nome

if not SPREADSHEET_ID:
    raise EnvironmentError("Defina a variável de ambiente KANBAN_SHEET_ID com o ID da planilha.")

# Inicializa o MCP server
server = MCPServer("kanban-sheets")

# Autenticação via Service Account (arquivo credentials.json)
def get_sheets_service():
    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)

@server.command("list_tasks")
def list_tasks() -> List[Dict]:
    """Lista todas as tarefas na planilha."""
    service = get_sheets_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])
    if not values:
        return []

    headers = values[0]
    tasks = [dict(zip(headers, row)) for row in values[1:]]
    return tasks

@server.command("add_task")
def add_task(task: Dict) -> str:
    """Adiciona uma nova tarefa."""
    service = get_sheets_service()
    sheet = service.spreadsheets()
    values = [[
        task.get("ID", ""),
        task.get("Contexto", ""),
        task.get("Prioridade", ""),
        task.get("Situação", ""),
        task.get("Resumo", "")
    ]]
    body = {"values": values}
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="RAW",
        body=body
    ).execute()
    return f"Tarefa {task.get('ID', '(sem ID)')} adicionada com sucesso."

@server.command("update_task")
def update_task(task_id: str, updates: Dict) -> str:
    """Atualiza uma tarefa existente."""
    service = get_sheets_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])
    headers = values[0]

    for i, row in enumerate(values[1:], start=2):  # linha real começa em 2
        if row[0] == task_id:
            for key, value in updates.items():
                if key in headers:
                    idx = headers.index(key)
                    while len(row) <= idx:
                        row.append("")
                    row[idx] = value
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"Sheet1!A{i}:E{i}",
                valueInputOption="RAW",
                body={"values": [row]}
            ).execute()
            return f"Tarefa {task_id} atualizada com sucesso."

    return f"Tarefa {task_id} não encontrada."

if __name__ == "__main__":
    server.run()
