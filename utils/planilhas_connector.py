import math
from typing import Any, Dict, List, Optional, Union
from pandas import DataFrame


class PlanilhasConnector:
    """
    Connector para Google Sheets com cache local usando pandas DataFrame.

    Carrega os dados da planilha uma vez e mantém em memória para consultas rápidas.
    Recarrega automaticamente após operações de add/update.

    Estrutura esperada das colunas:
    Nome Projeto | Task ID | Task ID Root | Sprint | Contexto | Descrição |
    Detalhado | Prioridade | Status | Data Criação | Data Solução
    """

    service: Any
    spreadsheetId: str
    range: str
    df: DataFrame
    sheet_name: str

    def __init__(self, service: Any, spreadsheetId: str, range: str) -> None:
        """
        Inicializa o connector e carrega os dados da planilha.

        Args:
            service: Serviço autenticado do Google Sheets API
            spreadsheetId: ID da planilha do Google Sheets
            range: Range no formato "SheetName!A:K"
        """
        self.service = service
        self.spreadsheetId = spreadsheetId
        self.range = range
        # Extrair nome da aba do range (ex: "Back-End!A:K" -> "Back-End")
        self.sheet_name = range.split('!')[0] if '!' in range else 'Sheet1'

        self.__load_data()

    def __load_data(self) -> None:
        """Carrega dados da planilha remota para o DataFrame local."""
        sheet = self.service.spreadsheets()
        result: dict = (
            sheet.values()
            .get(spreadsheetId=self.spreadsheetId, range=self.range)
            .execute()
        )
        values: list = result.get('values', [])

        if not values:
            # Planilha vazia - criar DataFrame vazio com colunas esperadas
            self.df = DataFrame(columns=[
                'Nome-Projeto', 'Task-ID', 'Task-ID-Root', 'Sprint', 'Contexto',
                'Descrição', 'Detalhado', 'Prioridade', 'Status',
                'Data-Criação', 'Data-Solução'
            ])
            return

        header: list = values.pop(0)
        # Normalizar nomes das colunas: substituir espaços por hífens
        normalized_columns = {
            i: header[i].replace(' ', '-')
            for i in range(len(header))
        }
        self.df = DataFrame(values).rename(columns=normalized_columns)

    def get_one(self, project_id: str, task_id: str) -> Dict:
        """
        Busca uma tarefa específica pelo projeto e task_id.

        Args:
            project_id: Nome do projeto
            task_id: ID da tarefa

        Returns:
            Dicionário com os dados da tarefa ou erro se não encontrada
        """
        # Verificar se DataFrame está vazio
        if self.df.empty:
            return {
                "error": f"Tarefa '{task_id}' não encontrada no projeto '{project_id}'"
            }

        # Filtrar DataFrame
        try:
            mask = (self.df['Nome-Projeto'] == project_id) & (self.df['Task-ID'] == task_id)
            result = self.df[mask]
        except KeyError:
            # Colunas não existem no DataFrame
            return {
                "error": f"Tarefa '{task_id}' não encontrada no projeto '{project_id}'"
            }

        if result.empty:
            return {
                "error": f"Tarefa '{task_id}' não encontrada no projeto '{project_id}'"
            }

        # Converter primeira linha para dicionário
        # Usar os nomes originais das colunas (com espaços) para compatibilidade
        task_dict = result.iloc[0].to_dict()

        # Converter nomes de volta para formato original (com espaços)
        original_format = {
            k.replace('-', ' '): v
            for k, v in task_dict.items()
        }

        return original_format

    def search_for(
        self,
        filters: Optional[Dict] = None,
        pagination: Optional[Dict] = None
    ) -> Union[List[Dict], Dict]:
        """
        Busca tarefas com filtros avançados e paginação opcional.

        Args:
            filters: Dicionário com filtros (opcional):
                - prioridade: Lista de prioridades
                - status: Lista de status
                - contexto: Filtro por contexto (busca parcial)
                - projeto: Filtro por projeto (busca parcial)
                - texto_busca: Busca em Descrição e Detalhado
                - task_id: Busca por Task ID específico
                - sprint: Filtro por Sprint
            pagination: Dicionário com paginação (opcional):
                - page: Número da página (começa em 1)
                - page_size: Tamanho da página

        Returns:
            Lista de dicionários com tarefas (se sem paginação)
            ou PaginatedResponse (se com paginação)
        """
        df_filtered = self.df.copy()

        # Aplicar filtros se fornecidos
        if filters:
            # Filtro por task_id (busca exata)
            if 'task_id' in filters and filters['task_id']:
                df_filtered = df_filtered[df_filtered['Task-ID'] == filters['task_id']]

            # Filtro por prioridade
            if 'prioridade' in filters and filters['prioridade']:
                df_filtered = df_filtered[df_filtered['Prioridade'].isin(filters['prioridade'])]

            # Filtro por status
            if 'status' in filters and filters['status']:
                df_filtered = df_filtered[df_filtered['Status'].isin(filters['status'])]

            # Filtro por contexto (busca parcial, case-insensitive)
            if 'contexto' in filters and filters['contexto']:
                df_filtered = df_filtered[
                    df_filtered['Contexto'].str.contains(filters['contexto'], case=False, na=False)
                ]

            # Filtro por projeto (busca parcial, case-insensitive)
            if 'projeto' in filters and filters['projeto']:
                df_filtered = df_filtered[
                    df_filtered['Nome-Projeto'].str.contains(filters['projeto'], case=False, na=False)
                ]

            # Filtro por sprint (busca exata)
            if 'sprint' in filters and filters['sprint']:
                df_filtered = df_filtered[df_filtered['Sprint'] == filters['sprint']]

            # Filtro por texto em Descrição e Detalhado
            if 'texto_busca' in filters and filters['texto_busca']:
                texto = filters['texto_busca'].lower()
                mask = (
                    df_filtered['Descrição'].str.lower().str.contains(texto, na=False) |
                    df_filtered['Detalhado'].str.lower().str.contains(texto, na=False)
                )
                df_filtered = df_filtered[mask]

        # Converter para lista de dicionários com nomes originais
        tasks = [
            {k.replace('-', ' '): v for k, v in row.to_dict().items()}
            for _, row in df_filtered.iterrows()
        ]

        # Se não há paginação, retornar lista simples
        if not pagination:
            return tasks

        # Aplicar paginação
        total_count = len(tasks)
        page = pagination.get('page', 1)
        page_size = pagination.get('page_size', 10)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

        # Ajustar página se for maior que o total
        current_page = min(page, total_pages) if total_pages > 0 else 1

        # Calcular índices
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size

        # Obter tarefas da página
        paginated_tasks = tasks[start_idx:end_idx]

        return {
            "tasks": paginated_tasks,
            "total_count": total_count,
            "page": current_page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": current_page < total_pages,
            "has_previous": current_page > 1
        }

    def add(self, new_task_list: List[List]) -> Dict:
        """
        Adiciona novas tarefas na planilha remota e recarrega o cache.

        Args:
            new_task_list: Lista de listas com valores das tarefas.
                Cada linha deve ter 11 valores na ordem:
                [Nome Projeto, Task ID, Task ID Root, Sprint, Contexto, Descrição,
                 Detalhado, Prioridade, Status, Data Criação, Data Solução]

        Returns:
            Dicionário com resultado da operação
        """
        try:
            if not new_task_list:
                return {"error": "Lista de tarefas vazia"}

            sheet = self.service.spreadsheets()
            body = {"values": new_task_list}

            sheet.values().append(
                spreadsheetId=self.spreadsheetId,
                range=self.range,
                valueInputOption="RAW",
                body=body
            ).execute()

            # Recarregar dados
            self.__load_data()

            return {
                "success": True,
                "message": f"{len(new_task_list)} tarefa(s) adicionada(s) com sucesso"
            }

        except Exception as e:
            return {"error": f"Erro ao adicionar tarefas: {str(e)}"}

    def update_one(self, update_task_list: List[Dict]) -> Dict:
        """
        Atualiza tarefas na planilha remota e recarrega o cache.

        Args:
            update_task_list: Lista de dicionários com:
                - project: Nome do projeto (obrigatório)
                - task_id: ID da tarefa a atualizar (obrigatório)
                - updates: Dicionário com campos a atualizar (nomes originais com espaços)

        Returns:
            Dicionário com resultado da operação (success_count, error_count, details)
        """
        try:
            if not update_task_list:
                return {"error": "Lista de atualizações vazia"}

            sheet = self.service.spreadsheets()

            # Buscar dados atuais da planilha
            result = sheet.values().get(
                spreadsheetId=self.spreadsheetId,
                range=self.range
            ).execute()
            values = result.get("values", [])

            if not values or len(values) < 2:
                return {"error": "Nenhuma tarefa encontrada na planilha"}

            headers = values[0]
            batch_data = []
            results = []
            success_count = 0
            error_count = 0

            # Processar cada atualização
            for update_item in update_task_list:
                project = update_item.get('project')
                task_id = update_item.get('task_id')
                updates = update_item.get('updates', {})

                # Validar campos obrigatórios
                if not project:
                    error_count += 1
                    results.append({
                        "task_id": task_id or "unknown",
                        "status": "error",
                        "message": "project não fornecido"
                    })
                    continue

                if not task_id:
                    error_count += 1
                    results.append({
                        "task_id": "unknown",
                        "status": "error",
                        "message": "task_id não fornecido"
                    })
                    continue

                # Encontrar a tarefa (Nome Projeto está no índice 0, Task ID está no índice 1)
                task_found = False
                for i, row in enumerate(values[1:], start=2):
                    # Garantir que row tem comprimento suficiente
                    extended_row = row + [''] * (len(headers) - len(row))

                    if len(extended_row) > 1 and extended_row[0] == project and extended_row[1] == task_id:
                        task_found = True

                        # Atualizar campos
                        for key, value in updates.items():
                            if key in headers:
                                idx = headers.index(key)
                                extended_row[idx] = value

                        # Adicionar ao batch
                        batch_data.append({
                            "range": f"{self.sheet_name}!A{i}:K{i}",
                            "values": [extended_row]
                        })
                        success_count += 1
                        results.append({
                            "task_id": task_id,
                            "status": "success",
                            "message": "Tarefa atualizada com sucesso"
                        })
                        break

                if not task_found:
                    error_count += 1
                    results.append({
                        "task_id": task_id,
                        "status": "error",
                        "message": f"Tarefa '{task_id}' não encontrada no projeto '{project}'"
                    })

            # Executar batch update se houver atualizações
            if batch_data:
                batch_body = {
                    "valueInputOption": "RAW",
                    "data": batch_data
                }
                sheet.values().batchUpdate(
                    spreadsheetId=self.spreadsheetId,
                    body=batch_body
                ).execute()

                # Recarregar dados
                self.__load_data()

            return {
                "success_count": success_count,
                "error_count": error_count,
                "details": results
            }

        except Exception as e:
            return {
                "success_count": 0,
                "error_count": len(update_task_list),
                "details": [{"error": f"Erro ao atualizar tarefas: {str(e)}"}]
            }