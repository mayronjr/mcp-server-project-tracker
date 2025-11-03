from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Union
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


class TaskUpdateFields(BaseModel):
    """Modelo Pydantic para os campos que podem ser atualizados em uma tarefa"""
    model_config = ConfigDict(use_enum_values=True)

    task_id_root: Optional[str] = Field(default=None, description="ID da tarefa raiz relacionada")
    sprint: Optional[str] = Field(default=None, description="Sprint associada")
    contexto: Optional[str] = Field(default=None, description="Contexto da tarefa")
    descricao: Optional[str] = Field(default=None, description="Descrição da tarefa")
    detalhado: Optional[str] = Field(default=None, description="Descrição detalhada")
    prioridade: Optional[Union[TaskPriority, str]] = Field(default=None, description="Prioridade da tarefa")
    status: Optional[Union[TaskStatus, str]] = Field(default=None, description="Status atual da tarefa")

    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Valida e converte strings para TaskStatus"""
        if v is None or isinstance(v, TaskStatus):
            return v
        if isinstance(v, str):
            # Tentar encontrar o enum pelo valor
            for status in TaskStatus:
                if status.value == v:
                    return status
            # Se não encontrar, lançar erro de validação
            valid_values = ', '.join([s.value for s in TaskStatus])
            raise ValueError(f"Status '{v}' inválido. Use: {valid_values}")
        return v

    @field_validator('prioridade', mode='before')
    @classmethod
    def validate_prioridade(cls, v):
        """Valida e converte strings para TaskPriority"""
        if v is None or isinstance(v, TaskPriority):
            return v
        if isinstance(v, str):
            # Tentar encontrar o enum pelo valor
            for priority in TaskPriority:
                if priority.value == v:
                    return priority
            # Se não encontrar, lançar erro de validação
            valid_values = ', '.join([p.value for p in TaskPriority])
            raise ValueError(f"Prioridade '{v}' inválida. Use: {valid_values}")
        return v


class TaskUpdate(BaseModel):
    """Modelo Pydantic para atualização de uma tarefa"""

    project: str = Field(..., description="Nome do Projeto da Atividade")
    task_id: str = Field(..., description="ID da tarefa a ser atualizada")
    fields: TaskUpdateFields = Field(..., description="Campos a serem atualizados")


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