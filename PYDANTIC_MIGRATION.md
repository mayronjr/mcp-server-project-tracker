# Migração para Pydantic Models

## Resumo das Mudanças

Este documento descreve a migração do sistema de tipos de dicionários Python simples para modelos Pydantic, tornando o código mais robusto, type-safe e autodocumentado.

## Novos Modelos Criados

### 1. Task (models/task.py)
Modelo principal que representa uma tarefa do Kanban.

**Campos:**
- `task_id`: str (obrigatório) - ID único da tarefa
- `contexto`: str (obrigatório) - Contexto da tarefa
- `descricao`: str (obrigatório) - Descrição da tarefa
- `prioridade`: TaskPriority (obrigatório) - Enum com valores: Baixa, Normal, Alta, Urgente
- `status`: TaskStatus (obrigatório) - Enum com valores: Todo, Em Desenvolvimento, Impedido, Concluído, Cancelado, Não Relacionado, Pausado
- `task_id_root`: str (opcional) - ID da tarefa raiz relacionada
- `sprint`: str (opcional) - Sprint associada
- `detalhado`: str (opcional) - Descrição detalhada
- `data_criacao`: str (opcional) - Data de criação
- `data_solucao`: str (opcional) - Data de solução

**Configuração:**
- `use_enum_values = True`: Os enums são automaticamente convertidos para seus valores string

### 2. TaskUpdate (models/task.py)
Modelo para atualização de tarefas.

**Campos:**
- `task_id`: str (obrigatório) - ID da tarefa a ser atualizada
- `fields`: dict (obrigatório) - Dicionário com os campos a atualizar

### 3. BatchTaskUpdate (models/task.py)
Modelo para operações de atualização em lote.

**Campos:**
- `updates`: List[TaskUpdate] - Lista de atualizações

### 4. BatchTaskAdd (models/task.py)
Modelo para operações de adição em lote.

**Campos:**
- `tasks`: List[Task] - Lista de tarefas

## Funções Atualizadas

### add_task
**Antes:**
```python
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
) -> str
```

**Depois:**
```python
def add_task(task: Task) -> str
```

### batch_add_tasks
**Antes:**
```python
def batch_add_tasks(tasks: List[Dict]) -> Dict
```

**Depois:**
```python
def batch_add_tasks(tasks: List[Task]) -> Dict
```

### batch_update_tasks
**Antes:**
```python
def batch_update_tasks(updates: List[Dict]) -> Dict
```

**Depois:**
```python
def batch_update_tasks(updates: List[TaskUpdate]) -> Dict
```

## Benefícios da Migração

1. **Validação Automática**: Pydantic valida automaticamente os tipos e valores dos campos
2. **Type Safety**: Melhor suporte para IDEs e ferramentas de análise estática
3. **Documentação**: Os modelos servem como documentação viva do schema
4. **Validação de Enums**: Status e Prioridade são validados automaticamente
5. **Mensagens de Erro Claras**: Erros de validação são mais informativos
6. **Serialização/Deserialização**: Conversão automática entre Python objects e JSON
7. **Menos Código**: Eliminação de validações manuais repetitivas

## Exemplo de Uso

### Criar uma tarefa
```python
from models import Task, TaskPriority, TaskStatus

task = Task(
    task_id="TASK-001",
    contexto="Backend",
    descricao="Implementar API de usuários",
    prioridade=TaskPriority.ALTA,
    status=TaskStatus.TODO,
    sprint="Sprint 1"
)
```

### Criar múltiplas tarefas
```python
tasks = [
    Task(
        task_id="TASK-001",
        contexto="Backend",
        descricao="Implementar API",
        prioridade=TaskPriority.ALTA,
        status=TaskStatus.TODO
    ),
    Task(
        task_id="TASK-002",
        contexto="Frontend",
        descricao="Criar tela",
        prioridade=TaskPriority.NORMAL,
        status=TaskStatus.TODO
    )
]
```

### Atualizar tarefas
```python
from models import TaskUpdate

updates = [
    TaskUpdate(
        task_id="TASK-001",
        fields={"Status": "Em Desenvolvimento"}
    ),
    TaskUpdate(
        task_id="TASK-002",
        fields={"Prioridade": "Alta", "Status": "Em Desenvolvimento"}
    )
]
```

## Compatibilidade

- ✅ Totalmente compatível com o protocolo MCP
- ✅ FastMCP suporta modelos Pydantic nativamente
- ✅ Serialização automática para JSON
- ✅ Validação em tempo de execução

## Testes Realizados

1. ✅ Importação dos modelos
2. ✅ Criação de instâncias Task
3. ✅ Validação de enums (TaskPriority e TaskStatus)
4. ✅ Serialização para dicionários
5. ✅ Inicialização do servidor MCP
6. ✅ Listagem de ferramentas disponíveis

## Próximos Passos

- Considerar adicionar validadores customizados para campos específicos
- Adicionar exemplos JSON schema para documentação da API
- Implementar testes unitários para os modelos
