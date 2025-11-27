import math
import os
from typing import Dict, List, Optional, Union
import pandas as pd
from pandas import DataFrame


class LocalFileConnector:
    """
    Connector para arquivos locais (Excel ou CSV) com cache local usando pandas DataFrame.

    Carrega os dados do arquivo uma vez e mantém em memória para consultas rápidas.
    Salva automaticamente após operações de add/update.

    Estrutura esperada das colunas:
    Nome Projeto | Task ID | Task ID Root | Sprint | Contexto | Descrição |
    Detalhado | Prioridade | Status | Data Criação | Data Solução
    """

    file_path: str
    file_type: str  # 'excel' ou 'csv'
    df: DataFrame
    sheet_name: Optional[str]  # Usado apenas para Excel

    def __init__(self, file_path: str, sheet_name: Optional[str] = None) -> None:
        """
        Inicializa o connector e carrega os dados do arquivo.

        Args:
            file_path: Caminho para o arquivo Excel (.xlsx) ou CSV (.csv)
            sheet_name: Nome da aba (apenas para Excel, padrão: primeira aba)
        """
        self.file_path = file_path
        self.sheet_name = sheet_name

        # Determinar tipo de arquivo
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            self.file_type = 'excel'
        elif file_path.endswith('.csv'):
            self.file_type = 'csv'
        else:
            raise ValueError("Formato de arquivo não suportado. Use .xlsx, .xls ou .csv")

        self.__load_data()

    def __load_data(self) -> None:
        """Carrega dados do arquivo local para o DataFrame."""
        # Verificar se o arquivo existe
        if not os.path.exists(self.file_path):
            # Criar arquivo vazio com estrutura esperada
            self.df = DataFrame(columns=[
                'Nome-Projeto', 'Task-ID', 'Task-ID-Root', 'Sprint', 'Contexto',
                'Descrição', 'Detalhado', 'Prioridade', 'Status',
                'Data-Criação', 'Data-Solução'
            ])
            self.__save_data()
            return

        # Carregar arquivo existente
        try:
            if self.file_type == 'excel':
                # Ler arquivo Excel
                df = pd.read_excel(self.file_path, sheet_name=self.sheet_name or 0)
            else:  # CSV
                # Ler arquivo CSV
                df = pd.read_csv(self.file_path)

            # Normalizar nomes das colunas: substituir espaços por hífens
            df.columns = [col.replace(' ', '-') for col in df.columns]
            self.df = df

        except Exception as e:
            raise RuntimeError(f"Erro ao carregar arquivo {self.file_path}: {str(e)}")

    def __save_data(self) -> None:
        """Salva o DataFrame de volta ao arquivo."""
        try:
            # Converter nomes de colunas de volta para formato com espaços
            df_to_save = self.df.copy()
            df_to_save.columns = [col.replace('-', ' ') for col in df_to_save.columns]

            if self.file_type == 'excel':
                # Salvar como Excel
                with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='w') as writer:
                    df_to_save.to_excel(
                        writer,
                        sheet_name=self.sheet_name or 'Sheet1',
                        index=False
                    )
            else:  # CSV
                # Salvar como CSV
                df_to_save.to_csv(self.file_path, index=False)

        except Exception as e:
            raise RuntimeError(f"Erro ao salvar arquivo {self.file_path}: {str(e)}")

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
        Adiciona novas tarefas ao arquivo local e recarrega o cache.

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

            # Criar DataFrame com novas tarefas
            new_df = DataFrame(new_task_list, columns=[
                'Nome-Projeto', 'Task-ID', 'Task-ID-Root', 'Sprint', 'Contexto',
                'Descrição', 'Detalhado', 'Prioridade', 'Status',
                'Data-Criação', 'Data-Solução'
            ])

            # Adicionar ao DataFrame existente
            self.df = pd.concat([self.df, new_df], ignore_index=True)

            # Salvar no arquivo
            self.__save_data()

            return {
                "success": True,
                "message": f"{len(new_task_list)} tarefa(s) adicionada(s) com sucesso"
            }

        except Exception as e:
            return {"error": f"Erro ao adicionar tarefas: {str(e)}"}

    def update_one(self, update_task_list: List[Dict]) -> Dict:
        """
        Atualiza tarefas no arquivo local e salva.

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

                # Encontrar a tarefa no DataFrame
                mask = (self.df['Nome-Projeto'] == project) & (self.df['Task-ID'] == task_id)
                task_indices = self.df.index[mask].tolist()

                if not task_indices:
                    error_count += 1
                    results.append({
                        "task_id": task_id,
                        "status": "error",
                        "message": f"Tarefa '{task_id}' não encontrada no projeto '{project}'"
                    })
                    continue

                # Atualizar campos (converter nomes com espaços para hífens)
                idx = task_indices[0]
                for key, value in updates.items():
                    col_name = key.replace(' ', '-')
                    if col_name in self.df.columns:
                        self.df.at[idx, col_name] = value

                success_count += 1
                results.append({
                    "task_id": task_id,
                    "status": "success",
                    "message": "Tarefa atualizada com sucesso"
                })

            # Salvar alterações se houve atualizações
            if success_count > 0:
                self.__save_data()

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

    def get_sprint_stats(self, project: Optional[str] = None) -> List[Dict]:
        """
        Calcula estatísticas de sprints com porcentagem de conclusão.

        Args:
            project: Nome do projeto para filtrar (opcional). Se não fornecido, retorna stats de todas as sprints.

        Returns:
            Lista de dicionários com estatísticas por sprint:
            - sprint: Nome da sprint
            - total_tasks: Total de tarefas na sprint
            - completed_tasks: Número de tarefas concluídas
            - completion_percentage: Porcentagem de conclusão (0-100)
            - tasks_by_status: Distribuição de tarefas por status
        """
        try:
            df_filtered = self.df.copy()

            # Filtrar por projeto se fornecido
            if project:
                df_filtered = df_filtered[df_filtered['Nome-Projeto'] == project]

            # Remover linhas sem sprint definida
            df_filtered = df_filtered[df_filtered['Sprint'].notna() & (df_filtered['Sprint'] != '')]

            if df_filtered.empty:
                return []

            # Agrupar por sprint
            sprint_groups = df_filtered.groupby('Sprint')

            sprint_stats = []
            for sprint_name, sprint_df in sprint_groups:
                total_tasks = len(sprint_df)

                # Contar tarefas concluídas (Status = "Concluído")
                completed_tasks = len(sprint_df[sprint_df['Status'] == 'Concluído'])

                # Calcular porcentagem de conclusão
                completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

                # Contar tarefas por status
                tasks_by_status = sprint_df['Status'].value_counts().to_dict()

                sprint_stats.append({
                    'sprint': sprint_name,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'completion_percentage': round(completion_percentage, 2),
                    'tasks_by_status': tasks_by_status
                })

            # Ordenar por nome da sprint
            sprint_stats.sort(key=lambda x: x['sprint'])

            return sprint_stats

        except Exception as e:
            return [{"error": f"Erro ao calcular estatísticas de sprints: {str(e)}"}]
