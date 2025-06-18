# Basic API Wrapper MCP Server

A simple MCP server template that demonstrates how to wrap external APIs following Block's design principles.

## Features

- ✅ **Top-down workflow design** - Tools built around user workflows, not API endpoints
- ✅ **Bundled operations** - Related actions combined into single tools
- ✅ **Secure authentication** - OAuth tokens stored in system keyring
- ✅ **Clear error handling** - Comprehensive error messages and fallbacks
- ✅ **LLM-optimized outputs** - Structured Markdown responses instead of raw JSON

## Tools

### `manage_task`
Comprehensive task management tool that handles:
- Create new tasks with title, description, status, and priority
- Update existing tasks 
- Get task details
- List tasks with optional status filtering

**Design Pattern**: Consolidates 4+ API endpoints into a single workflow-focused tool.

### `get_team_overview`
Bundles multiple read-only operations:
- Team member list with availability status
- Active projects summary
- Performance metrics (optional)
- Recent activity

**Design Pattern**: Groups related read operations to minimize tool chaining.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp env.example .env

# Edit configuration
nano .env
```

Required configuration:
- `API_BASE_URL`: Your API endpoint base URL
- `API_TIMEOUT`: Request timeout (default: 30 seconds)

### 3. Setup Authentication

```bash
# Setup API token (stored securely in keyring)
python setup_auth.py setup

# Verify authentication
python setup_auth.py check
```

### 4. Run Server

```bash
# Development mode
python server.py

# Or with uvicorn for production
uvicorn server:app --host 0.0.0.0 --port 8000
```

## Usage Examples

### Creating Tasks
```
"Create a new high-priority task called 'Review Q4 budget' with description 'Need to review all Q4 budget allocations before Friday meeting'"
```

### Team Overview
```
"What's my team working on right now?"
```

### Task Management
```
"Update task T-123 to mark it as completed"
```

## Design Principles Applied

### ✅ Workflow-First Design
- Tools designed around common user workflows
- Minimal tool chaining required
- Combined related operations

### ✅ LLM Optimization
- Structured Markdown outputs (not raw JSON)
- Clear, descriptive tool names and parameters
- Comprehensive error messages

### ✅ Security Best Practices
- OAuth token storage in system keyring
- No credentials in code or config files
- Secure token refresh handling

### ✅ Performance
- Parallel API calls where possible
- Efficient response formatting
- Rate limiting support

## Hosting Options

### Local Development
```bash
python server.py
```

### Docker
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cloud Functions
- Compatible with AWS Lambda, Google Cloud Functions, Azure Functions
- Include `requirements.txt` in deployment package
- Set environment variables in cloud console

## Testing

```bash
# Test authentication
python setup_auth.py check

# Test server locally
curl -X POST http://localhost:8000/tools \
  -H "Content-Type: application/json" \
  -d '{"name": "get_team_overview", "arguments": {}}'
```

## Customization

### Adding New Tools
1. Add tool definition in `_setup_tools()`
2. Implement handler method
3. Update documentation

### API Integration
1. Update `config.py` with new API settings
2. Modify authentication in `setup_auth.py` if needed
3. Update API calls in handler methods

## Troubleshooting

### Authentication Issues
```bash
# Remove and re-setup authentication
python setup_auth.py remove
python setup_auth.py setup
```

### API Connection Issues
- Check `API_BASE_URL` in `.env`
- Verify API token is valid
- Check network connectivity

### Common Errors
- `API token not found`: Run `python setup_auth.py setup`
- `404 Not Found`: Check API base URL configuration
- `401 Unauthorized`: Token may be expired, re-run auth setup

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Block's MCP Playbook](https://block.xyz/posts/blocks-playbook-for-designing-mcp-servers)
- [Python keyring documentation](https://pypi.org/project/keyring/) 