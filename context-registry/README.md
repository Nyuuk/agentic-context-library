# Agentix Context Registry

Centralized storage and management for Agentix context data.

## Structure

The registry is divided into high-level domains (Divisions) and shared resources.

-   **`engineering/`**: Context for software development, infrastructure, and operations.
    -   **`rules/`**: Engineering standards (Code Style, PR Guidelines).
    -   **`projects/`**: Project-specific documentation (PRDs, Architecture).
-   **`product/`**: Context for product management.
    -   **`rules/`**: Product standards (PRD Templates, DoD).
    -   **`roadmaps/`**: Product roadmaps and strategy.
-   **`it-ops/`**: Context for IT Operations and Infrastructure.
    -   **`rules/`**: Operational policies (Backups, Access Control).
    -   **`infrastructure/`**: Standard infrastructure definitions (Keycloak, DBs, Docker).
-   **`general/`**: Shared company-wide context.
    -   **`rules/`**: Global rules (Security, Ethics).
    -   **`glossary/`**: Company terminology.

## Usage

This repository is primarily used as a data source and configuration store for the Agentix ecosystem.

### Integration

-   **Sync Engine**: Scans this registry to index markdown documents into the Vector Database.
-   **MCP Engine**: Reads from this registry to provide context to AI agents.

## Development

When adding new context:
1.  Navigate to the appropriate domain folder (e.g., `engineering/projects/`).
2.  Create a new directory for your project/topic.
3.  Add an `index.md` with appropriate frontmatter (see below).
4.  Add markdown documents.

### Documentation Placement Guidelines

For new projects (e.g., `new-digital-identity/datarepo-service`), place documentation as follows:

-   **PRDs & Architecture**: Place in `engineering/projects/<category>/<project>/`.
    -   Example: `engineering/projects/digital-identity/datarepo-service/prd.md`
-   **Infrastructure Definitions**: Place in `it-ops/infrastructure/<component>/`.
    -   Example: `it-ops/infrastructure/keycloak/v24-standard.md` (for Docker Compose, Configs)
-   **Technical Implementation Details**: Keep in the service repository (`README.md`).

### Metadata Requirement (`index.md`)

Every folder MUST have an `index.md` file with the following frontmatter:

```yaml
---
title: "Title of the Folder/Topic"
version: "1.0.0"
status: stable  # draft | stable | deprecated
language: en    # en | id
tags: [tag1, tag2]
---
```
