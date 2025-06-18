# MCP Server Templates - Rust

Rust implementations of MCP server templates based on Block's playbook for designing effective MCP servers.

## Templates

### 1. Basic API Wrapper (`basic-api-wrapper/`)
**Pattern**: Simple tool-based MCP server
**Complexity**: ⭐⭐☆☆☆

A straightforward MCP server that wraps external APIs into MCP tools following workflow-first design principles.

**Features:**
- Task management with bundled operations
- Team overview with comprehensive data fetching
- Secure authentication with system keyring
- Memory safety and performance

### 2. Database-Enhanced Server (`database-enhanced/`)
**Pattern**: Analytics-enabled MCP server with DuckDB
**Complexity**: ⭐⭐⭐⭐☆

An advanced MCP server that syncs data to DuckDB, enabling SQL queries and analytics capabilities.

**Features:**
- DuckDB integration for local analytics
- Data synchronization from external APIs
- SQL query interface for complex analytics
- High-performance concurrent operations

### 3. GraphQL Direct Query (`graphql-direct/`)
**Pattern**: Direct query interface MCP server  
**Complexity**: ⭐⭐⭐☆☆

A sophisticated MCP server that exposes GraphQL directly to the LLM with schema awareness.

**Features:**
- Direct GraphQL query execution
- Schema introspection and caching
- Separate read/write tools for security
- Zero-cost abstractions

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
- Rust 1.70+
- Cargo
- System dependencies for keyring (platform-specific)

### Quick Start

```bash
# Choose your template
cd basic-api-wrapper/   # or database-enhanced/, graphql-direct/, google-calendar-v1/

# Build
cargo build --release

# Setup authentication (if required)
cargo run --bin setup-auth

# Run server
cargo run --release
```

## Development

### Build and Test
```bash
cargo build          # Debug build
cargo build --release # Optimized build
cargo test           # Run tests
cargo clippy         # Linting
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

## Rust Features

### Memory Safety
- Zero-cost abstractions with compile-time guarantees
- No null pointer dereferences or buffer overflows
- Thread safety without data races

### Performance
- Minimal runtime overhead
- Efficient async/await with Tokio
- Memory-efficient data structures

### Type System
```rust
// Strong typing prevents errors at compile time
#[derive(Debug, Deserialize)]
struct TaskOperation {
    operation: String,
    task_id: Option<String>,
    title: Option<String>,
    status: Option<String>,
}
```

## Key Design Principles Applied

### ✅ Workflow-First Design
```rust
// Good: Bundled operations with enum
enum TaskOperation {
    Create { title: String, description: Option<String> },
    Update { id: String, changes: TaskChanges },
    Get { id: String },
    List { filter: Option<String> },
}
```

### ✅ Error Handling
```rust
// Rust's Result type for explicit error handling
async fn handle_task_management(&self, args: Value) -> Result<Vec<Content>, anyhow::Error> {
    let task_op: TaskOperation = serde_json::from_value(args)
        .context("Failed to parse task operation arguments")?;
    
    match task_op.operation.as_str() {
        "create" => self.create_task(task_op).await,
        "update" => self.update_task(task_op).await,
        _ => Err(anyhow::anyhow!("Unknown operation")),
    }
}
```

### ✅ Concurrent Operations
```rust
// Parallel API calls with tokio::try_join!
let (team_response, members_response, projects_response) = tokio::try_join!(
    self.client.get(&team_url).send(),
    self.client.get(&members_url).send(),
    self.client.get(&projects_url).send()
)?;
```

## Authentication

Secure credential storage using the keyring crate:

```rust
use keyring::Entry;

fn get_api_token() -> Result<String, keyring::Error> {
    let entry = Entry::new("mcp-server", "api_token")?;
    entry.get_password()
}
```

## Performance Benefits

### Compile-Time Optimizations
- Dead code elimination
- Inline expansion
- LLVM optimizations

### Runtime Efficiency
- Zero-cost abstractions
- Minimal allocations
- Efficient async runtime

### Memory Usage
- Stack allocation by default
- Predictable memory patterns
- No garbage collector overhead

## Deployment

### Static Binary
```bash
# Build static binary
cargo build --release --target x86_64-unknown-linux-musl

# Docker multi-stage build
FROM rust:1.70 as builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bullseye-slim
COPY --from=builder /app/target/release/mcp-server /usr/local/bin/
CMD ["mcp-server"]
```

### Cross-Compilation
```bash
# Install target
rustup target add x86_64-pc-windows-gnu

# Build for Windows
cargo build --target x86_64-pc-windows-gnu --release
```

## Dependencies

### Core Libraries
- `tokio` - Async runtime
- `serde` - Serialization
- `reqwest` - HTTP client
- `anyhow` - Error handling
- `mcp-sdk` - MCP protocol implementation

### Optional Features
- `duckdb` - Analytics database (database-enhanced template)
- `keyring` - Secure credential storage
- `chrono` - Date/time handling

## Testing

```bash
# Unit tests
cargo test

# Integration tests
cargo test --test integration

# Benchmark tests
cargo bench
```

## Resources

- [Rust MCP SDK](https://github.com/modelcontextprotocol/rust-sdk)
- [Block's MCP Playbook](https://block.xyz/posts/blocks-playbook-for-designing-mcp-servers)
- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [Tokio Documentation](https://tokio.rs/) 