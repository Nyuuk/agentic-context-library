# Agentix Context Library - Engine Components

This directory contains the core engine components of the Agentix Context Library.
Each component is maintained as a separate git submodule to allow for independent versioning and reuse.

## Components

### 1. MCP Server (`mcp-server`)
- **Path:** `engine/mcp-server`
- **Repository:** `../mcp-enginee` (Relative path in local development)
- **Description:** A Model Context Protocol (MCP) server that provides context retrieval tools for AI agents.
- **Key Features:**
  - `search_context`: Semantic search over the vector database.
  - `read_content`: Retrieve full content chunks.
  - `list_directory`: Explore the context registry.
  - `get_metadata`: Get detailed metadata for context items.

### 2. Sync Engine (`sync-enginee`)
- **Path:** `engine/sync-enginee`
- **Repository:** `../sync-enginee` (Relative path in local development)
- **Description:** A synchronization engine that indexes documentation and code into the vector database.
- **Key Features:**
  - Automatic file scanning and chunking.
  - **Full Content Storage:** Stores original markdown content in Vector DB (Chunk 0).
  - Embeddings generation using BGE-M3.
  - Qdrant vector database integration.
  - Incremental updates support.

### 3. Architecture Transition (Feb 2026)
Moved from Hybrid (File + Vector) to **Pure Vector DB** architecture.
- **Sync Engine:** responsible for "hydrating" the Vector DB with both semantic chunks and full document content.
- **MCP Server:** completely stateless and filesystem-agnostic. Retrieves content solely from Qdrant payload.

## Working with Submodules

This project uses Git Submodules. Here are the common commands you'll need:

### Initial Setup (Cloning)
When cloning this repository for the first time, use the recursive flag:
```bash
git clone --recursive <repository-url>
```
If you already cloned without recursive:
```bash
git submodule update --init --recursive
```

### Pulling Updates
To pull updates for the main repository AND all submodules:
```bash
git pull --recurse-submodules
```

### Making Changes to Components

1.  **Enter the component directory:**
    ```bash
    cd engine/mcp-server
    ```
2.  **Make your changes, commit, and push:**
    ```bash
    git add .
    git commit -m "Your feature message"
    git push origin main
    ```
3.  **Update the reference in the main repository:**
    ```bash
    cd ../..
    git add engine/mcp-server
    git commit -m "Update mcp-server submodule reference"
    git push origin main
    ```

> **Note:** Always ensure you push the submodule changes BEFORE pushing the main repository changes, otherwise other users won't be able to pull your updates.
