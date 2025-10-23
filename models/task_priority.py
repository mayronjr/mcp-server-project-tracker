from enum import Enum

class TaskPriority(str, Enum):
    BAIXA="Baixa"
    NORMAL="Normal"
    ALTA="Alta"
    URGENTE="Urgente"