# MCP Server - Google Sheets Kanban

Servidor MCP (Model Context Protocol) para gerenciamento de tarefas em um quadro Kanban utilizando Google Sheets como backend.

## Características

- **Integração com Google Sheets**: Usa Google Sheets API v4 para armazenamento de dados
- **Modelos Pydantic**: Validação de dados com Pydantic v2
- **Operações em Lote**: Suporte para adicionar e atualizar múltiplas tarefas de uma vez
- **Busca Avançada**: Filtros por prioridade, status, contexto, projeto e texto
- **Paginação**: Suporte completo para navegação paginada de resultados
- **Protocolo MCP**: Compatível com clientes MCP via STDIO

## Ferramentas Disponíveis

### 1. `list_tasks` - Listar e Buscar Tarefas

Lista e busca tarefas da planilha com filtros avançados e paginação opcional.

**Parâmetros:**
- `filters` (opcional): Objeto com critérios de busca
  - `prioridade`: Lista de prioridades (Baixa, Normal, Alta, Urgente)
  - `status`: Lista de status para filtrar
  - `contexto`: Filtro por contexto (busca parcial, case-insensitive)
  - `projeto`: Filtro por projeto (busca parcial, case-insensitive)
  - `texto_busca`: Busca em Descrição e Detalhado (case-insensitive)
  - `task_id`: Busca por Task ID específico
  - `sprint`: Filtro por Sprint
- `pagination` (opcional): Objeto com `page` (número da página) e `page_size` (itens por página)

**Exemplos:**

```json
// 1. Listar todas as tarefas (comportamento legado)
{}

// 2. Com paginação
{
  "pagination": {
    "page": 1,
    "page_size": 20
  }
}

// 3. Buscar tarefas de alta prioridade
{
  "filters": {
    "prioridade": ["Alta", "Urgente"]
  }
}

// 4. Buscar tarefas em desenvolvimento com paginação
{
  "filters": {
    "status": ["Em Desenvolvimento"]
  },
  "pagination": {
    "page": 1,
    "page_size": 10
  }
}

// 5. Buscar por texto na descrição
{
  "filters": {
    "texto_busca": "implementar API"
  }
}

// 6. Combinar múltiplos filtros
{
  "filters": {
    "prioridade": ["Alta"],
    "status": ["Todo", "Em Desenvolvimento"],
    "contexto": "Backend",
    "projeto": "MCP Server"
  },
  "pagination": {
    "page": 1,
    "page_size": 25
  }
}
```

**Retorno (sem paginação):**
```json
[
  {
    "Task ID": "TASK-001",
    "Contexto": "Backend",
    "Descrição": "...",
    ...
  },
  ...
]
```

**Retorno (com paginação):**
```json
{
  "tasks": [...],
  "total_count": 45,
  "page": 1,
  "page_size": 25,
  "total_pages": 2,
  "has_next": true,
  "has_previous": false
}
```

---

### 2. `add_task` - Adicionar Tarefa

Adiciona uma nova tarefa na planilha.

**Parâmetros:**
- `task`: Objeto Task com todos os campos

**Exemplo:**
```json
{
  "task": {
    "project": "MCP Server Sheets",
    "task_id": "TASK-001",
    "contexto": "Backend",
    "descricao": "Implementar busca avançada",
    "prioridade": "Alta",
    "status": "Todo",
    "task_id_root": "",
    "sprint": "Sprint 1",
    "detalhado": "Adicionar filtros por prioridade, status e contexto",
    "data_criacao": "2025-10-24",
    "data_solucao": ""
  }
}
```

---

### 3. `update_task` - Atualizar Tarefa

Atualiza uma tarefa existente pelo Task ID.

**Parâmetros:**
- `task_id`: ID da tarefa a ser atualizada
- `updates`: Dicionário com campos a atualizar

**Exemplo:**
```json
{
  "task_id": "TASK-001",
  "updates": {
    "Status": "Concluído",
    "Data Solução": "2025-10-24"
  }
}
```

---

### 4. `batch_add_tasks` - Adicionar Múltiplas Tarefas

Adiciona múltiplas tarefas em uma única operação.

**Parâmetros:**
- `batch`: Objeto BatchTaskAdd contendo lista de tarefas

**Exemplo:**
```json
{
  "batch": {
    "tasks": [
      {
        "project": "MCP Server",
        "task_id": "TASK-001",
        "contexto": "Backend",
        "descricao": "Tarefa 1",
        "prioridade": "Alta",
        "status": "Todo"
      },
      {
        "project": "MCP Server",
        "task_id": "TASK-002",
        "contexto": "Frontend",
        "descricao": "Tarefa 2",
        "prioridade": "Normal",
        "status": "Todo"
      }
    ]
  }
}
```

**Retorno:**
```json
{
  "success_count": 2,
  "error_count": 0,
  "details": [
    {
      "task_id": "TASK-001",
      "status": "success",
      "message": "Tarefa adicionada com sucesso"
    },
    {
      "task_id": "TASK-002",
      "status": "success",
      "message": "Tarefa adicionada com sucesso"
    }
  ]
}
```

---

### 5. `batch_update_tasks` - Atualizar Múltiplas Tarefas

Atualiza múltiplas tarefas em uma única operação.

**Parâmetros:**
- `batch`: Objeto BatchTaskUpdate contendo lista de atualizações

**Exemplo:**
```json
{
  "batch": {
    "updates": [
      {
        "task_id": "TASK-001",
        "fields": {"Status": "Concluído"}
      },
      {
        "task_id": "TASK-002",
        "fields": {"Prioridade": "Alta"}
      }
    ]
  }
}
```

**Retorno:**
```json
{
  "success_count": 2,
  "error_count": 0,
  "details": [
    {
      "task_id": "TASK-001",
      "status": "success",
      "message": "Tarefa atualizada com sucesso"
    },
    {
      "task_id": "TASK-002",
      "status": "success",
      "message": "Tarefa atualizada com sucesso"
    }
  ]
}
```

---

### 6. `get_valid_configs` - Obter Configurações Válidas

Retorna os valores válidos para Status e Prioridade.

**Retorno:**
```json
{
  "valid_task_status": [
    "Todo",
    "Em Desenvolvimento",
    "Impedido",
    "Concluído",
    "Cancelado",
    "Não Relacionado",
    "Pausado"
  ],
  "valid_task_priorities": [
    "Baixa",
    "Normal",
    "Alta",
    "Urgente"
  ]
}
```

---

## Modelos de Dados

### Task
```python
{
  "project": str,          # Nome do Projeto (obrigatório)
  "task_id": str,          # ID único da tarefa (obrigatório)
  "contexto": str,         # Contexto da tarefa (obrigatório)
  "descricao": str,        # Descrição breve (obrigatório)
  "prioridade": str,       # Prioridade (obrigatório)
  "status": str,           # Status atual (obrigatório)
  "task_id_root": str,     # ID da tarefa raiz (opcional)
  "sprint": str,           # Sprint associada (opcional)
  "detalhado": str,        # Descrição detalhada (opcional)
  "data_criacao": str,     # Data de criação (opcional)
  "data_solucao": str      # Data de solução (opcional)
}
```

### BatchTaskAdd
```python
{
  "tasks": List[Task]      # Lista de tarefas a serem adicionadas
}
```

### BatchTaskUpdate
```python
{
  "updates": List[TaskUpdate]  # Lista de atualizações
}
```

Onde **TaskUpdate** é:
```python
{
  "task_id": str,          # ID da tarefa
  "fields": dict           # Campos a atualizar
}
```

### SearchFilters
```python
{
  "prioridade": List[str],      # Lista de prioridades
  "status": List[str],          # Lista de status
  "contexto": str,              # Filtro de contexto
  "projeto": str,               # Filtro de projeto
  "texto_busca": str,           # Busca de texto
  "task_id": str,               # ID específico
  "sprint": str                 # Filtro de sprint
}
```

### PaginationParams
```python
{
  "page": int,           # Número da página (mínimo: 1)
  "page_size": int       # Itens por página (1-500)
}
```

### PaginatedResponse
```python
{
  "tasks": List[Dict],   # Tarefas da página
  "total_count": int,    # Total de tarefas
  "page": int,           # Página atual
  "page_size": int,      # Itens por página
  "total_pages": int,    # Total de páginas
  "has_next": bool,      # Existe próxima página
  "has_previous": bool   # Existe página anterior
}
```

---

## Configuração

### Pré-requisitos

1. Python 3.13.5 ou superior
2. Conta Google Cloud com Google Sheets API habilitada
3. Arquivo `credentials.json` com credenciais de Service Account

### Variáveis de Ambiente

Crie um arquivo `.env` com:

```env
KANBAN_SHEET_ID=seu_id_da_planilha_aqui
KANBAN_SHEET_NAME=Back-End  # Nome da aba (padrão: "Back-End")
```

### Instalação

```bash
# Instalar dependências
uv sync

# Executar servidor
uv run main.py
```

### Configuração do Cliente MCP

Adicione ao seu cliente MCP:

```json
{
  "mcpServers": {
    "kanban-sheets": {
      "command": "uv",
      "args": ["run", "main.py"]
    }
  }
}
```

---

## Estrutura da Planilha

A planilha deve ter as seguintes colunas (A até J):

| Coluna | Nome           | Descrição                  |
|--------|----------------|----------------------------|
| A      | Task ID        | ID único da tarefa         |
| B      | Task ID Root   | ID da tarefa raiz          |
| C      | Sprint         | Sprint associada           |
| D      | Contexto       | Contexto da tarefa         |
| E      | Descrição      | Descrição breve            |
| F      | Detalhado      | Descrição detalhada        |
| G      | Prioridade     | Prioridade da tarefa       |
| H      | Status         | Status atual               |
| I      | Data Criação   | Data de criação            |
| J      | Data Solução   | Data de solução            |

---

## Exemplos de Uso Avançado

### Buscar todas as tarefas urgentes pendentes

```json
{
  "filters": {
    "prioridade": ["Urgente"],
    "status": ["Todo", "Em Desenvolvimento"]
  }
}
```

### Listar tarefas de um projeto específico com paginação

```json
{
  "filters": {
    "projeto": "MCP Server"
  },
  "pagination": {
    "page": 1,
    "page_size": 50
  }
}
```

### Buscar tarefas impedidas ou pausadas

```json
{
  "filters": {
    "status": ["Impedido", "Pausado"]
  }
}
```

### Buscar por palavra-chave na descrição

```json
{
  "filters": {
    "texto_busca": "API REST"
  }
}
```

---

## Tecnologias Utilizadas

- **FastMCP**: Framework para servidores MCP
- **Pydantic**: Validação de dados (v2.12.3)
- **Google API Python Client**: Integração com Google Sheets
- **google-auth**: Autenticação com Google Cloud

---

## Documentação Adicional

- [Migração para Pydantic](PYDANTIC_MIGRATION.md)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Model Context Protocol](https://modelcontextprotocol.io)

---

## Licença

Este projeto é um servidor MCP para gerenciamento de tarefas em Google Sheets.
