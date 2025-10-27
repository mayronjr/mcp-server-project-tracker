from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from .task_status import TaskStatus
from .task_priority import TaskPriority


class Task(BaseModel):
    """Modelo Pydantic para uma tarefa do Kanban"""
    model_config = ConfigDict(use_enum_values=True)

    project: str = Field(..., description="Nome do Projeto da Atividade")
    task_id: str = Field(..., description="ID único da tarefa")
    contexto: str = Field(..., description="Contexto da tarefa")
    descricao: str = Field(..., description="Descrição da tarefa")
    prioridade: TaskPriority = Field(..., description="Prioridade da tarefa")
    status: TaskStatus = Field(..., description="Status atual da tarefa")
    task_id_root: str = Field(default="", description="ID da tarefa raiz relacionada")
    sprint: str = Field(default="", description="Sprint associada")
    detalhado: str = Field(default="", description="Descrição detalhada")
    data_criacao: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="Data de criação (gerada automaticamente)"
    )
    data_solucao: str = Field(default="", description="Data de solução")


class TaskUpdate(BaseModel):
    """Modelo Pydantic para atualização de uma tarefa"""

    task_id: str = Field(..., description="ID da tarefa a ser atualizada")
    fields: dict = Field(..., description="Campos a serem atualizados")


class BatchTaskUpdate(BaseModel):
    """Modelo Pydantic para atualização em lote de tarefas"""

    updates: list[TaskUpdate] = Field(..., description="Lista de atualizações a serem aplicadas")


class BatchTaskAdd(BaseModel):
    """Modelo Pydantic para adição em lote de tarefas"""

    tasks: list[Task] = Field(..., description="Lista de tarefas a serem adicionadas")


class SearchFilters(BaseModel):
    """Modelo Pydantic para filtros de busca de tarefas"""
    model_config = ConfigDict(use_enum_values=True)

    prioridade: Optional[List[TaskPriority]] = Field(
        default=None,
        description="Lista de prioridades para filtrar (Baixa, Normal, Alta, Urgente)"
    )
    status: Optional[List[TaskStatus]] = Field(
        default=None,
        description="Lista de status para filtrar"
    )
    contexto: Optional[str] = Field(
        default=None,
        description="Filtrar por contexto (busca exata ou parcial)"
    )
    projeto: Optional[str] = Field(
        default=None,
        description="Filtrar por nome do projeto (busca exata ou parcial)"
    )
    texto_busca: Optional[str] = Field(
        default=None,
        description="Texto para buscar em Descrição e Detalhado (case-insensitive)"
    )
    task_id: Optional[str] = Field(
        default=None,
        description="Filtrar por Task ID específico"
    )
    sprint: Optional[str] = Field(
        default=None,
        description="Filtrar por Sprint"
    )


class PaginationParams(BaseModel):
    """Modelo Pydantic para parâmetros de paginação"""

    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (começando em 1)"
    )
    page_size: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Quantidade de itens por página (máximo 500)"
    )


class PaginatedResponse(BaseModel):
    """Modelo Pydantic para resposta paginada de tarefas"""

    tasks: List[dict] = Field(
        description="Lista de tarefas da página atual"
    )
    total_count: int = Field(
        description="Total de tarefas encontradas (antes da paginação)"
    )
    page: int = Field(
        description="Página atual"
    )
    page_size: int = Field(
        description="Quantidade de itens por página"
    )
    total_pages: int = Field(
        description="Total de páginas disponíveis"
    )
    has_next: bool = Field(
        description="Indica se existe próxima página"
    )
    has_previous: bool = Field(
        description="Indica se existe página anterior"
    )
