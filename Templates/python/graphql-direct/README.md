# GraphQL Direct Query MCP Server

A sophisticated MCP server template that provides direct GraphQL query access, following Block's Linear MCP final evolution pattern.

## Features

- ✅ **Direct GraphQL Access** - Execute queries and mutations directly against GraphQL APIs
- ✅ **Schema Introspection** - Dynamic schema discovery and documentation
- ✅ **Separate Read/Write Tools** - Clear separation between queries and mutations
- ✅ **Minimal Tool Count** - Maximum flexibility with just 3 tools
- ✅ **LLM-Optimized** - GraphQL queries are perfect for LLM generation

## Architecture

```
LLM → GraphQL Query → Direct API → Structured Results
```

This pattern eliminates the need for multiple API endpoint wrappers by giving LLMs direct access to the full GraphQL schema.

## Tools

### `execute_readonly_query`
Execute read-only GraphQL queries for data retrieval:
- User and team information
- Project and issue searching
- Analytics and reporting
- Complex filtering and aggregation

**Safety**: Only allows `query` operations, rejects mutations.

### `execute_mutation_query`
Execute GraphQL mutations for write operations:
- Creating new records
- Updating existing data
- Deleting or archiving items
- Bulk operations

**Security**: Clearly marked as write operations with user approval.

### `get_graphql_schema`
Retrieve comprehensive GraphQL schema documentation:
- Type definitions and field descriptions
- Query and mutation examples
- Input types and enums
- Cached for performance

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit configuration
cp env.example .env
nano .env
```

Required settings:
- `GRAPHQL_ENDPOINT`: Your GraphQL API endpoint
- `GRAPHQL_TIMEOUT`: Request timeout (default: 30 seconds)

### 3. Setup Authentication

```bash
python setup_auth.py setup
```

### 4. Test Schema Access

```bash
python test_schema.py
```

### 5. Run Server

```bash
python server.py
```

## Usage Examples

### Schema Discovery
```
"Show me the GraphQL schema for User types"
```

### Data Queries
```
"Find all issues assigned to john@example.com that are still open"
```

Generates:
```graphql
query FindUserIssues($email: String!) {
  issues(filter: { 
    assignee: { email: { eq: $email } }
    state: { eq: "open" }
  }) {
    nodes {
      id title state priority
      project { name }
      createdAt updatedAt
    }
  }
}
```

### Complex Analytics
```
"Show me team productivity metrics for the last quarter"
```

Generates:
```graphql
query TeamProductivity($teamId: String!, $startDate: DateTime!) {
  team(id: $teamId) {
    name
    members {
      name email
      assignedIssues(filter: { 
        completedAt: { gte: $startDate }
      }) {
        totalCount
      }
    }
    projects {
      nodes {
        name
        completedIssues: issues(filter: { 
          state: { eq: "done" }
          completedAt: { gte: $startDate }
        }) {
          totalCount
        }
      }
    }
  }
}
```

### Data Mutations
```
"Create a new high-priority issue in the Backend project titled 'Fix API rate limiting'"
```

Generates:
```graphql
mutation CreateIssue($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id title state priority
      project { name }
      assignee { name }
    }
  }
}
```

## Design Principles Applied

### ✅ Maximum Flexibility with Minimal Tools
- **Single Query Tool**: Handles all read operations
- **Single Mutation Tool**: Handles all write operations  
- **Schema Tool**: Provides LLM with API documentation
- **Result**: 3 tools instead of 30+ endpoint-specific tools

### ✅ LLM Strengths Leverage
- **GraphQL Generation**: LLMs excel at generating structured queries
- **Schema Understanding**: Natural language to GraphQL translation
- **Complex Queries**: Single query replaces multiple API calls

### ✅ Security by Design
- **Clear Separation**: Read vs write operations clearly separated
- **Permission Management**: Easy approval workflow for mutations
- **Token Security**: Secure credential storage and management

### ✅ Performance Optimization
- **Schema Caching**: Reduces token usage for repeated schema access
- **Direct Queries**: Eliminates multiple API round trips
- **Response Formatting**: Structured markdown for LLM comprehension

## Advanced Features

### Schema Filtering
```
"Show me only the Issue type schema"
```

Uses `type_filter` parameter to focus on specific types.

### Variable Support
All queries support GraphQL variables for dynamic content:

```graphql
query GetProject($id: String!, $includeIssues: Boolean = false) {
  project(id: $id) {
    id name description
    issues @include(if: $includeIssues) {
      nodes { id title state }
    }
  }
}
```

### Error Handling
Comprehensive GraphQL error parsing and reporting:
- Syntax errors with line/column information
- Field validation errors
- Permission and authentication errors
- Rate limiting and quota errors

### Response Optimization
- Large response truncation with summaries
- Structured JSON formatting
- Key metric extraction
- Performance timing information

## Common Query Patterns

### User Management
```graphql
# Get user details
query GetUser($email: String!) {
  user(filter: { email: { eq: $email } }) {
    id name email role
    teams { id name }
    assignedIssues { totalCount }
  }
}

# List team members
query TeamMembers($teamId: String!) {
  team(id: $teamId) {
    members {
      id name email role
      isActive
    }
  }
}
```

### Project Tracking
```graphql
# Project overview
query ProjectOverview($projectId: String!) {
  project(id: $projectId) {
    id name description state
    lead { name email }
    issues {
      totalCount
      nodes {
        id title state priority
        assignee { name }
      }
    }
  }
}

# Cross-project analytics
query CrossProjectStats($teamId: String!) {
  team(id: $teamId) {
    projects {
      nodes {
        name
        totalIssues: issues { totalCount }
        completedIssues: issues(filter: { state: { eq: "done" } }) { totalCount }
      }
    }
  }
}
```

### Issue Management
```graphql
# Create issue
mutation CreateIssue($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id title state priority
      project { name }
    }
  }
}

# Bulk update
mutation BulkUpdateIssues($ids: [String!]!, $input: IssueUpdateInput!) {
  issueBulkUpdate(ids: $ids, input: $input) {
    success
    updatedCount
  }
}
```

## Hosting Options

### Local Development
```bash
python server.py
```

### Docker Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "server.py"]
```

### Serverless Deployment
- AWS Lambda with API Gateway
- Google Cloud Functions
- Azure Functions
- Vercel Functions

### Traditional Server
```bash
# Install dependencies
pip install -r requirements.txt gunicorn

# Run with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app
```

## Testing

### Schema Validation
```bash
python test_schema.py
```

### Query Testing
```bash
# Test read-only queries
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"tool": "execute_readonly_query", "arguments": {"query": "{ __schema { types { name } } }"}}'

# Test mutations
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"tool": "execute_mutation_query", "arguments": {"query": "mutation { ping }"}}'
```

## Troubleshooting

### Schema Access Issues
```bash
# Test direct GraphQL access
curl -X POST $GRAPHQL_ENDPOINT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { queryType { name } } }"}'
```

### Authentication Problems
```bash
# Re-setup authentication
python setup_auth.py remove
python setup_auth.py setup
```

### Query Syntax Errors
- Use `get_graphql_schema` to verify field names
- Check GraphQL syntax with online validators
- Review variable types and required fields

### Performance Issues
- Use schema caching for repeated access
- Limit query depth and breadth
- Implement query complexity analysis

## Extending the Template

### Adding Query Validation
```python
def validate_query_complexity(query: str) -> bool:
    # Implement query complexity analysis
    depth = calculate_query_depth(query)
    return depth <= MAX_QUERY_DEPTH
```

### Custom Schema Processing
```python
def enhance_schema_docs(schema: dict) -> str:
    # Add custom documentation and examples
    # Generate type-specific query templates
    # Create relationship diagrams
```

### Rate Limiting
```python
def rate_limit_check(user_id: str) -> bool:
    # Implement per-user rate limiting
    # Track query complexity scores
    # Manage API quota usage
```

## Resources

- [GraphQL Specification](https://graphql.org/learn/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [Block's Linear MCP Evolution](https://block.xyz/posts/blocks-playbook-for-designing-mcp-servers)
- [GraphQL Schema Design Guide](https://www.apollographql.com/docs/apollo-server/schema/schema/) 