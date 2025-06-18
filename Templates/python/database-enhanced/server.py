#!/usr/bin/env python3

import json
import os
import asyncio
import duckdb
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import keyring
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types
from pydantic import AnyUrl
import mcp.server.stdio
from pathlib import Path


class DatabaseEnhancedMCP:
    """MCP server with DuckDB integration for analytics.
    
    Demonstrates Block's Calendar v2 pattern:
    - Sync external data to local DuckDB
    - Enable SQL queries for analytics
    - Provide macros for common complex queries
    - LLM-friendly schema design
    """
    
    def __init__(self):
        self.server = Server("database-enhanced-mcp")
        self.base_url = os.getenv("API_BASE_URL", "https://api.example.com")
        
        # Initialize DuckDB
        self.db_path = Path("data/analytics.duckdb")
        self.db_path.parent.mkdir(exist_ok=True)
        self.db = duckdb.connect(str(self.db_path))
        
        self._setup_database()
        self._setup_tools()
        
    def _setup_database(self):
        """Initialize DuckDB with analytics-friendly schema."""
        
        # Create events table (denormalized for easy querying)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS events (
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
        """)
        
        # Create analytics views
        self.db.execute("""
            CREATE OR REPLACE VIEW daily_summary AS
            SELECT 
                DATE(start_time) as date,
                COUNT(*) as total_meetings,
                SUM(duration_minutes) as total_minutes,
                SUM(CASE WHEN meeting_type = 'external' THEN 1 ELSE 0 END) as external_meetings,
                SUM(CASE WHEN meeting_type = 'internal' THEN 1 ELSE 0 END) as internal_meetings,
                AVG(attendees_count) as avg_attendees
            FROM events 
            WHERE status = 'confirmed'
            GROUP BY DATE(start_time)
            ORDER BY date
        """)
        
        # Free slots macro for calendar scheduling
        self.db.execute("""
            CREATE OR REPLACE MACRO free_slots(start_date, end_date, duration_minutes := 60) AS TABLE (
                WITH RECURSIVE time_slots AS (
                    SELECT start_date::TIMESTAMP as slot_start
                    UNION ALL
                    SELECT slot_start + INTERVAL '30 minutes'
                    FROM time_slots 
                    WHERE slot_start + INTERVAL '30 minutes' < end_date::TIMESTAMP
                ),
                busy_times AS (
                    SELECT start_time, end_time
                    FROM events 
                    WHERE status = 'confirmed'
                    AND start_time >= start_date::TIMESTAMP 
                    AND end_time <= end_date::TIMESTAMP
                )
                SELECT 
                    slot_start,
                    slot_start + INTERVAL (duration_minutes || ' minutes') as slot_end
                FROM time_slots
                WHERE NOT EXISTS (
                    SELECT 1 FROM busy_times 
                    WHERE busy_times.start_time < slot_start + INTERVAL (duration_minutes || ' minutes')
                    AND busy_times.end_time > slot_start
                )
                AND EXTRACT(hour FROM slot_start) BETWEEN 9 AND 17  -- Business hours
                AND EXTRACT(dow FROM slot_start) BETWEEN 1 AND 5    -- Weekdays
            )
        """)
        
    def _get_api_token(self) -> str:
        """Secure token retrieval from keyring."""
        token = keyring.get_password("database-enhanced-mcp", "api_token")
        if not token:
            raise ValueError("API token not found. Please run setup_auth.py first.")
        return token
    
    def _setup_tools(self):
        """Register MCP tools for database operations and sync."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="query_database",
                    description="""Execute SQL queries against the analytics database.
                    
                    The database contains:
                    - `events` table: All calendar events with analytics-friendly schema
                    - `daily_summary` view: Daily meeting statistics
                    - `free_slots(start_date, end_date, duration_minutes)` macro: Find available time slots
                    
                    Schema for events table:
                    - id, title, description
                    - start_time, end_time, duration_minutes
                    - attendees_count, meeting_type ('internal'/'external'/'personal')
                    - creator_email, status ('confirmed'/'tentative'/'cancelled')
                    - location, is_recurring
                    
                    Example queries:
                    - "SELECT * FROM daily_summary WHERE date >= '2024-01-01'"
                    - "SELECT * FROM free_slots('2024-01-15 09:00', '2024-01-15 17:00', 60)"
                    - "SELECT meeting_type, COUNT(*) FROM events GROUP BY meeting_type"
                    """,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL query to execute"
                            }
                        },
                        "required": ["sql"]
                    }
                ),
                types.Tool(
                    name="sync_calendar_data",
                    description="""Sync calendar events from external API to local database.
                    
                    This tool:
                    - Fetches recent events from the API
                    - Transforms data into analytics-friendly format
                    - Upserts into DuckDB for querying
                    - Returns sync statistics
                    
                    Automatically handles:
                    - Data deduplication
                    - Date range optimization
                    - Schema transformation
                    """,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days_back": {
                                "type": "integer",
                                "description": "Number of days to sync (default: 30)",
                                "default": 30
                            },
                            "force_full_sync": {
                                "type": "boolean",
                                "description": "Force full re-sync instead of incremental",
                                "default": False
                            }
                        }
                    }
                ),
                types.Tool(
                    name="generate_meeting_insights",
                    description="""Generate comprehensive meeting analytics and insights.
                    
                    Provides:
                    - Meeting patterns analysis
                    - Time utilization breakdown
                    - Productivity recommendations
                    - Calendar optimization suggestions
                    
                    Perfect for questions like:
                    - "How much time do I spend in meetings?"
                    - "What are my meeting patterns?"
                    - "When am I most/least busy?"
                    """,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "time_period": {
                                "type": "string",
                                "enum": ["week", "month", "quarter"],
                                "description": "Analysis time period",
                                "default": "month"
                            },
                            "include_recommendations": {
                                "type": "boolean",
                                "description": "Include optimization recommendations",
                                "default": True
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls with comprehensive error handling."""
            
            if name == "query_database":
                return await self._handle_database_query(arguments)
            elif name == "sync_calendar_data":
                return await self._handle_sync_data(arguments)
            elif name == "generate_meeting_insights":
                return await self._handle_generate_insights(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_database_query(self, args: dict) -> list[types.TextContent]:
        """Execute SQL queries against DuckDB."""
        sql = args.get("sql", "").strip()
        
        if not sql:
            return [types.TextContent(
                type="text",
                text="❌ SQL query is required"
            )]
        
        try:
            # Execute query
            result = self.db.execute(sql).fetchall()
            columns = [desc[0] for desc in self.db.description]
            
            if not result:
                return [types.TextContent(
                    type="text",
                    text="✅ Query executed successfully - No results found"
                )]
            
            # Format results as markdown table
            response = f"## Query Results\n\n"
            response += f"**Query**: `{sql}`\n\n"
            
            # Create table
            header = "| " + " | ".join(columns) + " |"
            separator = "|" + "|".join([" --- " for _ in columns]) + "|"
            response += header + "\n" + separator + "\n"
            
            for row in result[:50]:  # Limit to 50 rows for readability
                formatted_row = []
                for cell in row:
                    if cell is None:
                        formatted_row.append("NULL")
                    elif isinstance(cell, (datetime, str)) and len(str(cell)) > 30:
                        formatted_row.append(str(cell)[:27] + "...")
                    else:
                        formatted_row.append(str(cell))
                response += "| " + " | ".join(formatted_row) + " |\n"
            
            if len(result) > 50:
                response += f"\n*Showing first 50 of {len(result)} results*"
            
            response += f"\n\n**Rows returned**: {len(result)}"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ SQL Error: {str(e)}\n\n**Query**: `{sql}`"
            )]
    
    async def _handle_sync_data(self, args: dict) -> list[types.TextContent]:
        """Sync calendar data from API to DuckDB."""
        days_back = args.get("days_back", 30)
        force_full_sync = args.get("force_full_sync", False)
        
        try:
            headers = {"Authorization": f"Bearer {self._get_api_token()}"}
            
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            sync_stats = {
                "fetched": 0,
                "updated": 0,
                "inserted": 0,
                "errors": 0
            }
            
            async with httpx.AsyncClient() as client:
                # Fetch events from API
                response = await client.get(
                    f"{self.base_url}/calendar/events",
                    params={
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                        "limit": 1000
                    },
                    headers=headers
                )
                response.raise_for_status()
                events_data = response.json()
                
                sync_stats["fetched"] = len(events_data.get("events", []))
                
                # Transform and upsert events
                for event in events_data.get("events", []):
                    try:
                        # Transform API data to analytics schema
                        transformed = self._transform_event_data(event)
                        
                        # Check if event exists
                        existing = self.db.execute(
                            "SELECT id FROM events WHERE id = ?", 
                            [transformed["id"]]
                        ).fetchone()
                        
                        if existing:
                            # Update existing event
                            self.db.execute("""
                                UPDATE events SET 
                                    title = ?, description = ?, start_time = ?, end_time = ?,
                                    duration_minutes = ?, attendees_count = ?, meeting_type = ?,
                                    creator_email = ?, status = ?, location = ?, is_recurring = ?,
                                    updated_at = ?
                                WHERE id = ?
                            """, [
                                transformed["title"], transformed["description"],
                                transformed["start_time"], transformed["end_time"],
                                transformed["duration_minutes"], transformed["attendees_count"],
                                transformed["meeting_type"], transformed["creator_email"],
                                transformed["status"], transformed["location"],
                                transformed["is_recurring"], datetime.now(timezone.utc),
                                transformed["id"]
                            ])
                            sync_stats["updated"] += 1
                        else:
                            # Insert new event
                            self.db.execute("""
                                INSERT INTO events (
                                    id, title, description, start_time, end_time,
                                    duration_minutes, attendees_count, meeting_type,
                                    creator_email, status, location, is_recurring,
                                    created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, [
                                transformed["id"], transformed["title"], transformed["description"],
                                transformed["start_time"], transformed["end_time"],
                                transformed["duration_minutes"], transformed["attendees_count"],
                                transformed["meeting_type"], transformed["creator_email"],
                                transformed["status"], transformed["location"],
                                transformed["is_recurring"], datetime.now(timezone.utc),
                                datetime.now(timezone.utc)
                            ])
                            sync_stats["inserted"] += 1
                            
                    except Exception as e:
                        sync_stats["errors"] += 1
                        print(f"Error processing event {event.get('id', 'unknown')}: {e}")
            
            # Generate response
            response_text = f"""## Calendar Data Sync Complete ✅

**Sync Statistics:**
- 📥 Events fetched: {sync_stats['fetched']}
- 🆕 Events inserted: {sync_stats['inserted']}
- 🔄 Events updated: {sync_stats['updated']}
- ❌ Errors: {sync_stats['errors']}

**Time Range:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({days_back} days)

**Database Status:**
- Total events in database: {self.db.execute('SELECT COUNT(*) FROM events').fetchone()[0]}
- Last sync: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

You can now run analytics queries on the synchronized data."""
            
            return [types.TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Sync Error: {str(e)}"
            )]
    
    def _transform_event_data(self, event: dict) -> dict:
        """Transform API event data to analytics-friendly format."""
        start_time = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))
        duration = int((end_time - start_time).total_seconds() / 60)
        
        # Determine meeting type based on attendees
        attendees = event.get("attendees", [])
        external_domains = {attendee.get("email", "").split("@")[1] for attendee in attendees if "@" in attendee.get("email", "")}
        company_domain = "example.com"  # Replace with actual company domain
        
        if len(external_domains - {company_domain}) > 0:
            meeting_type = "external"
        elif len(attendees) > 1:
            meeting_type = "internal"
        else:
            meeting_type = "personal"
        
        return {
            "id": event["id"],
            "title": event.get("title", "No title"),
            "description": event.get("description", ""),
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": duration,
            "attendees_count": len(attendees),
            "meeting_type": meeting_type,
            "creator_email": event.get("creator", {}).get("email", ""),
            "status": event.get("status", "confirmed"),
            "location": event.get("location", ""),
            "is_recurring": event.get("recurring", False)
        }
    
    async def _handle_generate_insights(self, args: dict) -> list[types.TextContent]:
        """Generate comprehensive meeting insights and analytics."""
        time_period = args.get("time_period", "month")
        include_recommendations = args.get("include_recommendations", True)
        
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            if time_period == "week":
                start_date = end_date - timedelta(days=7)
                period_name = "Past Week"
            elif time_period == "month":
                start_date = end_date - timedelta(days=30)
                period_name = "Past Month"
            else:  # quarter
                start_date = end_date - timedelta(days=90)
                period_name = "Past Quarter"
            
            # Execute analytics queries
            total_meetings = self.db.execute("""
                SELECT COUNT(*) FROM events 
                WHERE start_time >= ? AND start_time <= ? AND status = 'confirmed'
            """, [start_date, end_date]).fetchone()[0]
            
            total_hours = self.db.execute("""
                SELECT COALESCE(SUM(duration_minutes), 0) / 60.0 FROM events 
                WHERE start_time >= ? AND start_time <= ? AND status = 'confirmed'
            """, [start_date, end_date]).fetchone()[0]
            
            meeting_breakdown = self.db.execute("""
                SELECT meeting_type, COUNT(*), SUM(duration_minutes) / 60.0 as hours
                FROM events 
                WHERE start_time >= ? AND start_time <= ? AND status = 'confirmed'
                GROUP BY meeting_type
                ORDER BY hours DESC
            """, [start_date, end_date]).fetchall()
            
            busiest_days = self.db.execute("""
                SELECT DATE(start_time) as date, COUNT(*) as meetings, SUM(duration_minutes) / 60.0 as hours
                FROM events 
                WHERE start_time >= ? AND start_time <= ? AND status = 'confirmed'
                GROUP BY DATE(start_time)
                ORDER BY hours DESC
                LIMIT 5
            """, [start_date, end_date]).fetchall()
            
            # Build insights report
            insights = f"""# Meeting Insights - {period_name}

## 📊 Overview
- **Total Meetings**: {total_meetings}
- **Total Hours**: {total_hours:.1f} hours
- **Average per Day**: {total_hours / (end_date - start_date).days:.1f} hours
- **Average Meeting Length**: {(total_hours * 60 / total_meetings) if total_meetings > 0 else 0:.0f} minutes

## 🏷️ Meeting Breakdown"""
            
            for meeting_type, count, hours in meeting_breakdown:
                percentage = (hours / total_hours * 100) if total_hours > 0 else 0
                insights += f"\n- **{meeting_type.title()}**: {count} meetings, {hours:.1f}h ({percentage:.1f}%)"
            
            insights += "\n\n## 📅 Busiest Days"
            for date, meetings, hours in busiest_days:
                insights += f"\n- **{date}**: {meetings} meetings, {hours:.1f} hours"
            
            if include_recommendations and total_hours > 0:
                insights += "\n\n## 💡 Recommendations"
                
                if total_hours > 20:  # More than 4h/day average
                    insights += "\n- 🔴 **High meeting load** - Consider consolidating or declining non-essential meetings"
                
                external_percentage = sum(hours for _, _, hours in meeting_breakdown if _ == "external") / total_hours * 100
                if external_percentage > 60:
                    insights += "\n- 🌐 **High external meeting ratio** - Ensure adequate time for internal collaboration"
                
                avg_meeting_length = (total_hours * 60 / total_meetings) if total_meetings > 0 else 0
                if avg_meeting_length > 45:
                    insights += "\n- ⏱️ **Long average meeting duration** - Consider shorter, more focused meetings"
                
                insights += "\n- 📋 **Schedule review** - Use `free_slots()` macro to find optimal meeting times"
            
            insights += f"\n\n*Analysis generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"
            
            return [types.TextContent(type="text", text=insights)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Insights Error: {str(e)}"
            )]


async def main():
    """Run the MCP server."""
    enhanced_server = DatabaseEnhancedMCP()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await enhanced_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="database-enhanced-mcp",
                server_version="1.0.0",
                capabilities=enhanced_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main()) 