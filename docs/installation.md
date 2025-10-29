# Installation Guide

This guide will walk you through setting up the MCP Server for Google Sheets Kanban from scratch.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.13.5 or higher** installed
- **uv** package manager (recommended) or pip
- A **Google Cloud account** with access to create projects
- A **Google Sheets** spreadsheet for your Kanban board

## Step 1: Install Python and uv

### Install Python

Download and install Python 3.13.5+ from [python.org](https://www.python.org/downloads/)

Verify installation:
```bash
python --version
```

### Install uv (Recommended)

uv is a fast Python package manager. Install it using:

**Windows:**
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:
```bash
uv --version
```

## Step 2: Clone or Download the Project

Clone the repository or download the source code:

```bash
git clone https://github.com/yourusername/mcp-server-sheets.git
cd mcp-server-sheets
```

Or download and extract the ZIP file, then navigate to the directory.

## Step 3: Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -r requirements.txt
```

### Install Development Dependencies (Optional)

If you want to run tests:

```bash
uv pip install -r requirements-dev.txt
```

Or with pip:
```bash
pip install -r requirements-dev.txt
```

## Step 4: Set Up Google Cloud Credentials

See the detailed [Google Cloud Setup Guide](google-cloud-setup.md) for instructions on:

1. Creating a Google Cloud project
2. Enabling the Google Sheets API
3. Creating a Service Account
4. Generating and downloading `credentials.json`
5. Sharing your spreadsheet with the service account

**Quick Summary:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "Google Sheets API"
4. Create a Service Account
5. Download the JSON key file and save it as `credentials.json` in your project root
6. Share your Google Sheets with the service account email

## Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
KANBAN_SHEET_ID=your_spreadsheet_id_here
KANBAN_SHEET_NAME=Back-End
```

**Finding your Spreadsheet ID:**

From your Google Sheets URL:
```
https://docs.google.com/spreadsheets/d/1abc123def456ghi789jkl/edit
                                      ^^^^^^^^^^^^^^^^^^^^
                                      This is your Sheet ID
```

## Step 6: Prepare Your Google Sheets Spreadsheet

Your spreadsheet must have the following column structure (columns A-K):

| Column | Header         | Required | Description                     |
|--------|----------------|----------|---------------------------------|
| A      | Projeto        | Yes      | Project name                    |
| B      | Task ID        | Yes      | Unique task identifier          |
| C      | Task ID Root   | No       | Parent task ID (for subtasks)   |
| D      | Sprint         | No       | Sprint name                     |
| E      | Contexto       | Yes      | Task context (e.g., Backend)    |
| F      | Descrição      | Yes      | Brief description               |
| G      | Detalhado      | No       | Detailed description            |
| H      | Prioridade     | Yes      | Priority (see valid values)     |
| I      | Status         | Yes      | Current status (see valid values)|
| J      | Data Criação   | Auto     | Creation date (auto-generated)  |
| K      | Data Solução   | Auto     | Completion date (auto-generated)|

**Valid Priority Values:**
- Baixa
- Normal
- Alta
- Urgente

**Valid Status Values:**
- Todo
- Em Desenvolvimento
- Impedido
- Concluído
- Cancelado
- Não Relacionado
- Pausado

**Example Spreadsheet:**

Create a header row (row 1) with exactly these column names:
```
Projeto | Task ID | Task ID Root | Sprint | Contexto | Descrição | Detalhado | Prioridade | Status | Data Criação | Data Solução
```

## Step 7: Test the Installation

Run a quick test to ensure everything is configured correctly:

```bash
uv run pytest
```

All tests should pass. If you see errors, check:
- Your `.env` file is configured correctly
- `credentials.json` exists in the project root
- Your Google Sheets spreadsheet has the correct column structure

## Step 8: Run the MCP Server

Start the server:

```bash
uv run main.py
```

You should see output like:
```
============================================================
Iniciando servidor MCP: kanban-sheets
Planilha ID: 1abc123def456ghi789jkl
Aba: Back-End
Protocolo: STDIO (Standard Input/Output)
...
============================================================
```

The server is now running and waiting for MCP client connections via STDIO.

## Step 9: Configure Your MCP Client

See the [Usage Guide](usage.md) for instructions on connecting different MCP clients to your server.

For Claude Desktop, add this to your configuration:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "kanban-sheets": {
      "command": "uv",
      "args": ["--directory", "C:/path/to/mcp-server-sheets", "run", "main.py"]
    }
  }
}
```

Replace `C:/path/to/mcp-server-sheets` with the actual path to your project directory.

## Verification

After configuring your MCP client, restart it and verify the connection:

1. Restart your MCP client (e.g., Claude Desktop)
2. Check that the `kanban-sheets` server appears in the available tools
3. Try running the `get_valid_configs` tool to verify connectivity

## Next Steps

- Read the [Usage Guide](usage.md) to learn how to use all available tools
- Check the [API Reference](api-reference.md) for detailed tool documentation
- See [Troubleshooting](troubleshooting.md) if you encounter any issues

## Common Installation Issues

### "Module not found" errors

Make sure you've installed all dependencies:
```bash
uv sync
```

### "credentials.json not found"

Ensure the `credentials.json` file is in the project root directory, not in a subdirectory.

### "KANBAN_SHEET_ID not set"

Check that your `.env` file exists and contains the correct variable names.

### Permission errors with Google Sheets

Make sure you've shared your spreadsheet with the service account email address from your `credentials.json` file.

For more help, see the [Troubleshooting Guide](troubleshooting.md).
