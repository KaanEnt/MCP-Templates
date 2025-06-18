# MCP Server Templates - TypeScript

TypeScript implementations of MCP server templates based on Block's playbook for designing effective MCP servers.

## Templates

### 1. Basic API Wrapper (`basic-api-wrapper/`)
**Pattern**: Simple tool-based MCP server
**Complexity**: ⭐⭐☆☆☆

A straightforward MCP server that wraps external APIs into MCP tools following workflow-first design principles.

**Features:**
- Task management with bundled operations
- Team overview with comprehensive data fetching
- Secure authentication with keychain storage
- TypeScript type safety

### 2. Database-Enhanced Server (`database-enhanced/`)
**Pattern**: Analytics-enabled MCP server with DuckDB
**Complexity**: ⭐⭐⭐⭐☆

An advanced MCP server that syncs data to DuckDB, enabling SQL queries and analytics capabilities.

**Features:**
- DuckDB integration for local analytics
- Data synchronization from external APIs
- SQL query interface for complex analytics
- Smart insights generation

### 3. GraphQL Direct Query (`graphql-direct/`)
**Pattern**: Direct query interface MCP server  
**Complexity**: ⭐⭐⭐☆☆

A sophisticated MCP server that exposes GraphQL directly to the LLM with schema awareness.

**Features:**
- Direct GraphQL query execution
- Schema introspection and caching
- Separate read/write tools for security
- Maximum flexibility with minimal tool count

### 4. Google Calendar v1 (`google-calendar-v1/`)
**Pattern**: Problematic thin wrapper (educational)
**Complexity**: ⭐⭐☆☆☆

The "v1" Google Calendar MCP mentioned in Block's playbook that demonstrates common anti-patterns.

**Problems Demonstrated:**
- Bottom-up API endpoint design
- No analytics capabilities
- Painful LLM workflows requiring multiple tool calls
- Verbose, poorly scoped outputs

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn
- TypeScript

### Quick Start

```bash
# Choose your template
cd basic-api-wrapper/   # or database-enhanced/, graphql-direct/, google-calendar-v1/

# Install dependencies
npm install

# Build TypeScript
npm run build

# Setup authentication
npm run setup-auth

# Run server
npm start
```

## Development

### Build and Watch
```bash
npm run dev      # Watch mode for development
npm run build    # Production build
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

## TypeScript Features

### Type Safety
- Comprehensive interfaces for all API interactions
- Strict type checking for tool arguments
- Runtime validation with proper error handling

### Modern JavaScript
- ES modules with full TypeScript support
- Async/await for all asynchronous operations
- Promise-based architecture

### Development Experience
- Hot reload during development
- Comprehensive error messages
- IntelliSense support in IDEs

## Key Design Principles Applied

### ✅ Workflow-First Design
```typescript
// Good: Bundled operations
interface TaskManagement {
  operation: "create" | "update" | "get" | "list";
  // ... other fields
}

// Bad: Separate tools for each operation
// createTask(), updateTask(), getTask(), listTasks()
```

### ✅ Type Safety
```typescript
// Interfaces ensure compile-time safety
interface EventsListArgs {
  calendar_id?: string;
  time_max?: string;
  time_min?: string;
  verbose?: boolean;
}
```

### ✅ Error Handling
```typescript
try {
  const response = await axios.get(url, { headers });
  return { content: [{ type: "text", text: response.data }] };
} catch (error) {
  if (axios.isAxiosError(error)) {
    return { content: [{ type: "text", text: `❌ API Error: ${error.response?.status}` }] };
  }
  throw error;
}
```

## Authentication

All templates use secure credential storage:

```typescript
import keytar from "keytar";

class AuthManager {
  async getToken(): Promise<string> {
    const token = await keytar.getPassword(service, account);
    if (!token) throw new Error("Token not found");
    return token;
  }
}
```

## Deployment

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist/ ./dist/
CMD ["node", "dist/server.js"]
```

### Cloud Functions
- AWS Lambda with Node.js runtime
- Google Cloud Functions
- Azure Functions
- Vercel Serverless Functions

## Resources

- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Block's MCP Playbook](https://block.xyz/posts/blocks-playbook-for-designing-mcp-servers)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/) 