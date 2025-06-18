# MCP Server Templates - Python

Python implementations of MCP server templates based on Block's playbook for designing effective MCP servers.

## Templates

### Google Calendar v1 (`google-calendar-v1/`)
**Pattern**: Problematic thin wrapper (educational)
**Complexity**: ⭐⭐☆☆☆

The "v1" Google Calendar MCP mentioned in Block's playbook that demonstrates common anti-patterns.

**Problems Demonstrated:**
- Bottom-up API endpoint design: Tools simply mirror API endpoints
- No analytics capabilities: Can't answer "How many meetings did I have last month?"
- Painful LLM workflows: Multiple tool calls needed for simple queries
- Verbose, poorly scoped outputs: Returns giant JSON blobs

## Why This Template Exists

This template demonstrates the **wrong way** to build MCP servers, as described in Block's playbook. It shows:

1. **Bottom-up design**: Tools are direct wrappers around Google Calendar API endpoints
2. **Poor LLM experience**: Requires 4-6 tool calls for common workflows
3. **No analytics**: Can't perform any analysis on calendar data
4. **Verbose outputs**: Returns raw API responses that are hard to process

## Comparison: v1 vs v2

### v1 Problems (This Template)
```python
@mcp.tool()
def list_calendars():
    """Lists all user calendars."""
    # Returns raw API response - verbose and hard to use

@mcp.tool() 
def list_calendar_events(calendar_id, time_min, time_max, verbose):
    """Get all events for a specified time period."""
    # Another separate API call required

@mcp.tool()
def retrieve_timezone(calendar_id):
    """Retrieves timezone for a given calendar."""
    # Yet another separate call

@mcp.tool()
def retrieve_calendar_free_busy_slots(time_min, time_max, timezone, calendar_ids):
    """Retrieves free and busy slots."""
    # Raw freebusy data, hard to interpret
```

**Result**: To answer "What does my day look like?" requires multiple tool calls and manual analysis.

### v2 Solution (Analytics-Enhanced)
```python
@mcp.tool()
def query_database(sql, time_min, time_max):
    """Run arbitrary queries against calendars/events in our DuckDB tables."""
    # Single tool with SQL access to analytics-ready data

# Can now answer complex questions with one call:
# "SELECT * FROM free_slots('2025-05-13T09:00:00Z', '2025-05-17T18:00:00Z')"
```

## Setup

### Prerequisites
- Python 3.8+
- pip

### Quick Start

```bash
cd google-calendar-v1/

# Install dependencies
pip install -r requirements.txt

# Setup authentication
python setup_auth.py

# Run server
python server.py
```

## Educational Value

This template helps you understand:

1. **Why workflow-first design matters**
2. **How API wrappers can become painful**
3. **The importance of analytics capabilities**
4. **When to consolidate vs separate tools**

## Tools Provided

### `list_calendars`
Lists all user calendars with basic information.

**Problem**: Returns verbose calendar metadata that LLMs struggle to process.

### `list_calendar_events`
Get events for a time period.

**Problem**: 
- Separate call from calendar listing
- Verbose output with unnecessary details
- No built-in analytics or filtering

### `retrieve_timezone`
Get calendar timezone information.

**Problem**: 
- Yet another separate API call
- Information that could be bundled with calendar listing

### `retrieve_calendar_free_busy_slots`
Get free/busy information.

**Problem**:
- Raw API response format
- Hard to interpret without additional processing
- No intelligent slot finding or recommendations

## Common Workflows and Their Pain Points

### "What does my day look like?"
**v1 Experience**: 
1. Call `list_calendars` to get calendar IDs
2. Call `list_calendar_events` for each calendar
3. LLM must manually parse and combine results
4. No analysis or insights provided

**v2 Solution**: Single SQL query with pre-processed data

### "Find time for a 1-hour meeting"
**v1 Experience**:
1. Call `retrieve_calendar_free_busy_slots`
2. Parse raw busy periods
3. LLM must calculate available slots manually
4. No business hours logic or preferences

**v2 Solution**: `free_slots()` macro with built-in business logic

### "How many meetings did I have last month?"
**v1 Experience**: 
❌ **Impossible** - no analytics capabilities

**v2 Solution**: Simple SQL query on historical data

## Key Learnings

### ❌ Don't Do This
```python
# Separate tools for related operations
def get_user():
    return raw_api_response()

def get_file(): 
    return another_raw_response()

# Result: LLM needs multiple calls and manual processing
```

### ✅ Do This Instead
```python
# Bundled, workflow-focused tool
def upload_file_with_user_context(path, owner):
    # Gets user, uploads file, returns success/error message
    # Single call, clear outcome
```

## Resources

- [Block's MCP Playbook](https://block.xyz/posts/blocks-playbook-for-designing-mcp-servers)
- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) 