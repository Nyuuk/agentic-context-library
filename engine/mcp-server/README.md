# Agentix Context Library - MCP Server

An **Model Context Protocol (MCP)** server that provides AI agents with semantic search and access to the organizational knowledge base (Context Library).

This server connects to a **Qdrant** vector database to perform semantic searches and reads directly from the **Context Registry** (Git repository) to retrieve full document content.

## 🏗️ Architecture

As defined in the [PRD](../../docs/prd.md), the MCP Server is a persistent service that:
1.  **Searches**: Queries Qdrant for relevant document chunks (using `BAAI/bge-m3` embeddings).
2.  **Reads**: Accesses the mounted `context-registry` volume to read full Markdown files.
3.  **Exposes**: Standard MCP tools (`search_context`, `read_content`, `list_directory`, `get_metadata`) via **FastMCP**.
4.  **Secures**: Enforces Bearer Token authentication via `MCP_API_KEY`.

## 🚀 Prerequisites

- **Docker** & **Docker Compose**
- **Qdrant** instance (running and populated by Sync Engine)
- **Context Registry** (cloned locally)

## 🛠️ Configuration

The server is configured via environment variables.

| Variable | Default | Description |
|---|---|---|
| `QDRANT_URL` | `http://localhost:6333` | URL of the Qdrant instance. |
| `COLLECTION_NAME` | `context_library` | Name of the Qdrant collection. |
| `CONTEXT_ROOT` | `/data/context-registry` | Path where the Context Registry is mounted. |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Embedding model (MUST match Sync Engine). |
| `MCP_API_KEY` | *Required* | Secret key for Bearer Token authentication. |
| `LOG_LEVEL` | `INFO` | Logging level. |

## 📦 Usage

### 1. Connect to Claude Desktop

Configure `claude_desktop_config.json`:

**Path:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**

```json
{
  "mcpServers": {
    "agentix-context": {
      "url": "http://your-mcp-server-url:8000/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer <YOUR_MCP_API_KEY>"
      }
    }
  }
}
```

### 2. Connect to Cursor

Cursor supports MCP via `~/.cursor/mcp.json`. Use the following configuration:

**Configuration:**

```json
{
  "mcpServers": {
    "agentix-context": {
      "url": "http://your-mcp-server-url:8000/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer <YOUR_MCP_API_KEY>"
      }
    }
  }
}
```

### 3. Connect to Google Antigravity

For Antigravity Agents, add to your MCP configuration file:

**Configuration:**

```json
{
  "mcpServers": {
    "agentix-context": {
      "serverUrl": "http://your-mcp-server-url:8000/sse",
      "headers": {
         "Authorization": "Bearer <YOUR_MCP_API_KEY>"
      }
    }
  }
}
```

> **Note:** Replace `http://your-mcp-server-url:8000` with the actual URL where the MCP server is deployed.

### 4. Running Locally (For Development/Testing)

If you need to run it locally for development, use Docker Compose:

```bash
docker compose up -d mcp-server
```

## 🔍 Available Tools

| Tool | Description |
|---|---|
| **`search_context`** | Semantically search for relevant document chunks. Supports filtering by status, directory, language, and tags. |
| **`read_content`** | Read the full content of a specific Markdown document. |
| **`list_directory`** | List files and subdirectories within a specific folder. |
| **`get_metadata`** | Retrieve metadata for a document or directory. |

## 🧪 Testing

You can test the server health endpoint:

```bash
# Health check (requires auth or returns 401)
curl -H "Authorization: Bearer <MCP_API_KEY>" http://localhost:8000/mcp
```

Or perform a manual tool call using `curl`:

```bash
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <MCP_API_KEY>" \
  -d '{
    "name": "search_context",
    "arguments": {
      "query": "deployment strategy"
    }
  }'
```
