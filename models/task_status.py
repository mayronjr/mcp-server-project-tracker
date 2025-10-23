from enum import Enum

class TaskStatus(str, Enum):
    TODO="Todo"
    EM_PROGRESSO="Em Desenvolvimento"
    IMPEDIDO="Impedido"
    CONCLUIDO="Concluído"
    CANCELADO="Cancelado"
    NAO_RELACIONADO="Não Relacionado"
    PAUSADO="Pausado"