# MCP Server Templates

This directory contains 3 different MCP server templates based on Block's playbook for designing effective MCP servers. Each template demonstrates different design patterns and complexity levels.

## Templates Overview

### 1. Basic API Wrapper (`basic-api-wrapper/`)
**Pattern**: Simple tool-based MCP server
**Use Case**: When you need to expose external APIs with minimal transformation
**Complexity**: ⭐⭐☆☆☆

A straightforward MCP server that wraps external APIs into MCP tools. Good starting point for simple integrations.

### 2. Database-Enhanced Server (`database-enhanced/`)
**Pattern**: Analytics-enabled MCP server with DuckDB
**Use Case**: When you need to perform analytics, queries, and data analysis
**Complexity**: ⭐⭐⭐⭐☆

An advanced MCP server that syncs data to DuckDB, enabling SQL queries and analytics capabilities.

### 3. GraphQL Direct Query (`graphql-direct/`)
**Pattern**: Direct query interface MCP server
**Use Case**: When you have complex APIs and want maximum flexibility
**Complexity**: ⭐⭐⭐☆☆

A sophisticated MCP server that exposes GraphQL directly to the LLM with schema awareness.

## Key Design Principles (Block's Playbook)

### ✅ Best Practices

1. **Design Top-Down from Workflows**
   - Start with user workflows, not API endpoints
   - Combine multiple API calls into single high-level tools
   - Minimize tool chaining requirements

2. **Optimize for LLM Strengths**
   - **Good at**: SQL queries, Markdown/Mermaid diagrams, structured text
   - **Weak at**: Multi-step planning, strict JSON formatting, long identifiers

3. **Authentication & Security**
   - Use OAuth whenever possible
   - Store tokens in secure keyring/credential manager
   - Request minimum necessary scopes
   - Handle token refresh gracefully

4. **Performance Optimization**
   - Use prompt prefix caching
   - Avoid dynamic timestamps in instructions
   - Keep tool descriptions stable

5. **Permission Management**
   - Group tools by risk level (read-only vs write)
   - Use clear tool annotations (`readOnlyHint`)
   - Bundle related read-only operations

### ❌ Anti-Patterns

1. **Don't**: Expose raw, granular API endpoints
2. **Don't**: Mix read/write operations in same tool (when avoidable)
3. **Don't**: Store credentials in plaintext
4. **Don't**: Design for >20 tool call chains
5. **Don't**: Use complex JSON schemas when Markdown/XML suffices

## Quick Start

Choose the template that best fits your use case:

```bash
# For simple API integration
cd basic-api-wrapper/
python -m pip install -r requirements.txt
python server.py

# For analytics and data queries
cd database-enhanced/
python -m pip install -r requirements.txt
python server.py

# For complex GraphQL APIs
cd graphql-direct/
python -m pip install -r requirements.txt
python server.py
```

## Hosting Options

### Local Development
- Use `uvicorn` for development server
- Enable auto-reload for development
- Use environment variables for configuration

### Production Hosting

#### Option 1: Docker Container
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Option 2: Cloud Functions
- AWS Lambda with function URLs
- Google Cloud Functions
- Azure Functions

#### Option 3: VPS/Server
- Use nginx as reverse proxy
- Enable HTTPS with Let's Encrypt
- Set up systemd service for auto-restart

## Configuration

Each template includes:
- `config.py` - Configuration management
- `.env.example` - Environment variable template
- `requirements.txt` - Python dependencies
- `README.md` - Specific setup instructions

## Testing

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Test MCP connection
mcp-client-test --server-url http://localhost:8000
```

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Block's MCP Playbook](https://block.xyz/posts/blocks-playbook-for-designing-mcp-servers)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) 