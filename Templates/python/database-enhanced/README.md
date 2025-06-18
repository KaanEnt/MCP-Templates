# Database-Enhanced MCP Server

An advanced MCP server template that demonstrates DuckDB integration for analytics, following Block's Google Calendar v2 pattern.

## Features

- ✅ **DuckDB Integration** - Local analytics database with SQL query capabilities
- ✅ **Data Synchronization** - Automatic sync from external APIs to local database
- ✅ **Analytics Views** - Pre-built views and macros for common queries
- ✅ **LLM-Optimized Schema** - Denormalized data for easy querying
- ✅ **Smart Insights** - Automated analytics and recommendations

## Architecture

```
External API → Data Sync → DuckDB → SQL Queries → LLM Analysis
```

### Key Components

1. **Data Sync Engine**: Fetches and transforms API data into analytics-friendly format
2. **DuckDB Database**: Local database optimized for analytical queries
3. **SQL Query Interface**: Direct SQL access for complex analytics
4. **Smart Macros**: Pre-built functions for common operations (e.g., finding free time slots)

## Tools

### `query_database`
Execute SQL queries against the analytics database with:
- `events` table: Denormalized calendar events
- `daily_summary` view: Daily meeting statistics  
- `free_slots()` macro: Find available time slots

### `sync_calendar_data`
Sync external calendar data to local DuckDB:
- Incremental or full sync options
- Data transformation and deduplication
- Comprehensive sync statistics

### `generate_meeting_insights`
AI-powered meeting analytics:
- Meeting patterns analysis
- Time utilization breakdown
- Productivity recommendations

## Database Schema

### Events Table (Denormalized for LLM Queries)
```sql
CREATE TABLE events (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    attendees_count INTEGER,
    meeting_type VARCHAR,  -- 'internal', 'external', 'personal'
    creator_email VARCHAR,
    status VARCHAR,        -- 'confirmed', 'tentative', 'cancelled'
    location VARCHAR,
    is_recurring BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Available Macros

#### Free Slots Finder
```sql
-- Find 60-minute slots between 9 AM - 5 PM on weekdays
SELECT * FROM free_slots('2024-01-15 09:00', '2024-01-15 17:00', 60);
```

#### Daily Summary View
```sql
-- Get daily meeting statistics
SELECT * FROM daily_summary WHERE date >= '2024-01-01';
```

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
- `API_BASE_URL`: Calendar API endpoint
- `COMPANY_DOMAIN`: Your company domain for meeting type detection
- `DB_PATH`: DuckDB database file path (optional)

### 3. Setup Authentication

```bash
python setup_auth.py setup
```

### 4. Initialize Database

```bash
python init_database.py
```

### 5. Run Server

```bash
python server.py
```

## Usage Examples

### Initial Data Sync
```
"Sync the last 30 days of calendar data"
```

### Analytics Queries
```
"Show me my meeting statistics for this month"
```

```sql
SELECT 
    meeting_type,
    COUNT(*) as meetings,
    SUM(duration_minutes)/60.0 as hours,
    AVG(attendees_count) as avg_attendees
FROM events 
WHERE start_time >= '2024-01-01'
GROUP BY meeting_type
```

### Finding Free Time
```
"Find 2-hour blocks available this week for a project workshop"
```

```sql
SELECT * FROM free_slots('2024-01-15 09:00', '2024-01-19 17:00', 120);
```

### Custom Analytics
```sql
-- Busiest days analysis
SELECT 
    DATE(start_time) as date,
    COUNT(*) as meetings,
    SUM(duration_minutes) as total_minutes
FROM events 
WHERE start_time >= DATE('now', '-30 days')
GROUP BY DATE(start_time)
ORDER BY total_minutes DESC;
```

## Design Principles Applied

### ✅ DuckDB for LLM Analytics
- **Strength**: LLMs excel at generating SQL queries
- **Schema**: Denormalized, self-describing table and column names
- **Performance**: Local database eliminates API rate limits

### ✅ Data Transformation
- **API to Analytics**: Transform verbose API responses to analysis-friendly format
- **Meeting Classification**: Automatic internal/external/personal categorization
- **Time Calculations**: Pre-calculated durations and business metrics

### ✅ Workflow-Optimized Tools
- **Bundled Operations**: Single tool for complex analytics workflows
- **Smart Defaults**: Reasonable defaults for common use cases
- **Error Recovery**: Graceful handling of API and database errors

## Advanced Features

### Custom Macros
Add domain-specific analysis functions:

```sql
-- Create custom productivity macro
CREATE MACRO productivity_score(start_date, end_date) AS (
    SELECT 
        AVG(CASE WHEN meeting_type = 'internal' THEN 0.8
                 WHEN meeting_type = 'external' THEN 0.6  
                 ELSE 1.0 END) as score
    FROM events 
    WHERE start_time BETWEEN start_date AND end_date
);
```

### Automated Insights
The insights generator provides:
- Meeting load analysis
- Pattern recognition
- Optimization recommendations
- Time management suggestions

### Performance Optimization
- Incremental sync to reduce API calls
- Indexed queries for fast analytics
- Configurable result limits
- Efficient data transformation pipeline

## Hosting Options

### Local Development
```bash
python server.py
```

### Docker with Persistent Database
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
VOLUME ["/app/data"]
CMD ["python", "server.py"]
```

### Cloud Deployment
- Mount persistent volume for DuckDB file
- Set environment variables for API configuration
- Use health checks to ensure database connectivity

## Troubleshooting

### Database Issues
```bash
# Check database status
python -c "import duckdb; print(duckdb.connect('data/analytics.duckdb').execute('SELECT COUNT(*) FROM events').fetchone())"

# Reset database
rm data/analytics.duckdb
python init_database.py
```

### Sync Problems
```bash
# Force full re-sync
python -c "
from server import DatabaseEnhancedMCP
server = DatabaseEnhancedMCP()
# Manually trigger sync
"
```

### Query Performance
- Limit result sets with `LIMIT` clause
- Use `daily_summary` view for aggregated data
- Create indexes for frequently queried columns

## Extending the Template

### Adding New Data Sources
1. Create sync method in `server.py`
2. Add transformation logic
3. Update database schema as needed
4. Create relevant views/macros

### Custom Analytics
1. Add SQL views for common queries
2. Create macros for complex calculations
3. Update tool descriptions with new capabilities

## Resources

- [DuckDB Documentation](https://duckdb.org/docs/)
- [SQL for Analytics Best Practices](https://docs.getdbt.com/guides/best-practices)
- [Block's Calendar MCP Case Study](https://block.xyz/posts/blocks-playbook-for-designing-mcp-servers) 