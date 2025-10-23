from pydantic import BaseModel, Field
from typing import Optional
from .task_status import TaskStatus
from .task_priority import TaskPriority


class Task(BaseModel):
    """Modelo Pydantic para uma tarefa do Kanban"""

    task_id: str = Field(..., description="ID único da tarefa")
    contexto: str = Field(..., description="Contexto da tarefa")
    descricao: str = Field(..., description="Descrição da tarefa")
    prioridade: TaskPriority = Field(..., description="Prioridade da tarefa")
    status: TaskStatus = Field(..., description="Status atual da tarefa")
    task_id_root: str = Field(default="", description="ID da tarefa raiz relacionada")
    sprint: str = Field(default="", description="Sprint associada")
    detalhado: str = Field(default="", description="Descrição detalhada")
    data_criacao: str = Field(default="", description="Data de criação")
    data_solucao: str = Field(default="", description="Data de solução")

    class Config:
        use_enum_values = True  # Usa os valores das enums ao serializar


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
