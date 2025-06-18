#!/usr/bin/env python3

"""
Google Calendar MCP v1 - Thin API Wrapper
This represents the initial version mentioned in Block's playbook that served 
as a thin wrapper around the external API before the v2 analytics improvements.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import keyring
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types
from pydantic import AnyUrl
import mcp.server.stdio


class GoogleCalendarV1MCP:
    """
    Google Calendar MCP v1 - The problematic first version.
    
    Problems with this approach (as noted in Block's playbook):
    - Bottom-up design: Tools simply mirror API endpoints
    - No analytics capabilities: Can't answer "How many meetings did I have last month?"
    - Painful for LLM workflows: Multiple tool calls needed for simple queries
    - Limited insight generation
    """
    
    def __init__(self):
        self.server = Server("google-calendar-v1")
        self.base_url = "https://www.googleapis.com/calendar/v3"
        
        self._setup_tools()
        
    def _get_api_token(self) -> str:
        """Get Google API token from keyring."""
        token = keyring.get_password("google-calendar-v1", "access_token")
        if not token:
            raise ValueError("Google API token not found. Please run setup_auth.py first.")
        return token
    
    def _setup_tools(self):
        """Register MCP tools - direct API endpoint wrappers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="list_calendars",
                    description="Lists all user calendars.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                ),
                types.Tool(
                    name="list_calendar_events",
                    description="Get all events for a specified time period for a given calendar.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "calendar_id": {
                                "type": "string",
                                "description": "Calendar ID (default: primary)",
                                "default": "primary"
                            },
                            "time_max": {
                                "type": "string",
                                "description": "Upper bound (exclusive) for an event's start time (RFC3339 timestamp)"
                            },
                            "time_min": {
                                "type": "string",
                                "description": "Lower bound (exclusive) for an event's end time (RFC3339 timestamp)"
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "Include detailed event information",
                                "default": False
                            }
                        }
                    }
                ),
                types.Tool(
                    name="retrieve_timezone",
                    description="Retrieves timezone for a given calendar.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "calendar_id": {
                                "type": "string",
                                "description": "Calendar ID (default: primary)",
                                "default": "primary"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="retrieve_calendar_free_busy_slots",
                    description="Retrieves free and busy slots from the calendars of the calendar_ids list.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "time_min": {
                                "type": "string",
                                "description": "Lower bound for the query (RFC3339 timestamp)"
                            },
                            "time_max": {
                                "type": "string",
                                "description": "Upper bound for the query (RFC3339 timestamp)"
                            },
                            "timezone": {
                                "type": "string",
                                "description": "Timezone to use for the query",
                                "default": "UTC"
                            },
                            "calendar_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of calendar IDs to query",
                                "default": ["primary"]
                            }
                        },
                        "required": ["time_min", "time_max"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls - direct API wrappers."""
            
            if name == "list_calendars":
                return await self._list_calendars(arguments)
            elif name == "list_calendar_events":
                return await self._list_calendar_events(arguments)
            elif name == "retrieve_timezone":
                return await self._retrieve_timezone(arguments)
            elif name == "retrieve_calendar_free_busy_slots":
                return await self._retrieve_free_busy_slots(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _list_calendars(self, args: dict) -> list[types.TextContent]:
        """Direct wrapper for calendars.list API."""
        try:
            headers = {"Authorization": f"Bearer {self._get_api_token()}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/users/me/calendarList",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                # Return raw API response as JSON text
                calendars_text = "**Calendars List**\n\n"
                for calendar in data.get("items", []):
                    calendars_text += f"• **{calendar.get('summary', 'Unknown')}** (ID: {calendar.get('id', 'Unknown')})\n"
                    calendars_text += f"  - Primary: {calendar.get('primary', False)}\n"
                    calendars_text += f"  - Access Role: {calendar.get('accessRole', 'Unknown')}\n\n"
                
                return [types.TextContent(type="text", text=calendars_text)]
                
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error listing calendars: {str(e)}"
            )]
    
    async def _list_calendar_events(self, args: dict) -> list[types.TextContent]:
        """Direct wrapper for events.list API."""
        try:
            calendar_id = args.get("calendar_id", "primary")
            time_max = args.get("time_max")
            time_min = args.get("time_min")
            verbose = args.get("verbose", False)
            
            headers = {"Authorization": f"Bearer {self._get_api_token()}"}
            params = {}
            
            if time_max:
                params["timeMax"] = time_max
            if time_min:
                params["timeMin"] = time_min
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/calendars/{calendar_id}/events",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Return verbose API response - this gets unwieldy quickly
                events = data.get("items", [])
                if not events:
                    return [types.TextContent(
                        type="text",
                        text="No events found for the specified time period."
                    )]
                
                events_text = f"**Calendar Events** ({len(events)} found)\n\n"
                
                for event in events:
                    events_text += f"### {event.get('summary', 'No title')}\n"
                    
                    # Start time
                    start = event.get('start', {})
                    start_time = start.get('dateTime', start.get('date', 'Unknown'))
                    events_text += f"**Start**: {start_time}\n"
                    
                    # End time
                    end = event.get('end', {})
                    end_time = end.get('dateTime', end.get('date', 'Unknown'))
                    events_text += f"**End**: {end_time}\n"
                    
                    if verbose:
                        # Include all the verbose details that make this painful to use
                        events_text += f"**ID**: {event.get('id', 'Unknown')}\n"
                        events_text += f"**Status**: {event.get('status', 'Unknown')}\n"
                        events_text += f"**Creator**: {event.get('creator', {}).get('email', 'Unknown')}\n"
                        events_text += f"**Organizer**: {event.get('organizer', {}).get('email', 'Unknown')}\n"
                        
                        attendees = event.get('attendees', [])
                        if attendees:
                            events_text += f"**Attendees** ({len(attendees)}):\n"
                            for attendee in attendees:
                                events_text += f"  - {attendee.get('email', 'Unknown')} ({attendee.get('responseStatus', 'Unknown')})\n"
                        
                        if event.get('description'):
                            events_text += f"**Description**: {event.get('description')}\n"
                        
                        if event.get('location'):
                            events_text += f"**Location**: {event.get('location')}\n"
                    
                    events_text += "\n---\n\n"
                
                # This response can become extremely long and unwieldy
                if len(events_text) > 8000:
                    events_text = events_text[:8000] + "\n\n*[Response truncated - too much data]*"
                
                return [types.TextContent(type="text", text=events_text)]
                
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error listing events: {str(e)}"
            )]
    
    async def _retrieve_timezone(self, args: dict) -> list[types.TextContent]:
        """Direct wrapper for calendars.get API (timezone info)."""
        try:
            calendar_id = args.get("calendar_id", "primary")
            headers = {"Authorization": f"Bearer {self._get_api_token()}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/calendars/{calendar_id}",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                timezone_text = f"**Calendar Timezone Information**\n\n"
                timezone_text += f"**Calendar**: {data.get('summary', 'Unknown')}\n"
                timezone_text += f"**Timezone**: {data.get('timeZone', 'Unknown')}\n"
                timezone_text += f"**Location**: {data.get('location', 'Not specified')}\n"
                
                return [types.TextContent(type="text", text=timezone_text)]
                
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error retrieving timezone: {str(e)}"
            )]
    
    async def _retrieve_free_busy_slots(self, args: dict) -> list[types.TextContent]:
        """Direct wrapper for freebusy.query API."""
        try:
            time_min = args["time_min"]
            time_max = args["time_max"]
            timezone = args.get("timezone", "UTC")
            calendar_ids = args.get("calendar_ids", ["primary"])
            
            headers = {"Authorization": f"Bearer {self._get_api_token()}"}
            payload = {
                "timeMin": time_min,
                "timeMax": time_max,
                "timeZone": timezone,
                "items": [{"id": cal_id} for cal_id in calendar_ids]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/freeBusy",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Return raw API response - hard to interpret without additional processing
                freebusy_text = f"**Free/Busy Information**\n\n"
                freebusy_text += f"**Time Range**: {time_min} to {time_max}\n"
                freebusy_text += f"**Timezone**: {timezone}\n\n"
                
                calendars = data.get("calendars", {})
                for calendar_id, calendar_data in calendars.items():
                    freebusy_text += f"### Calendar: {calendar_id}\n"
                    
                    busy_times = calendar_data.get("busy", [])
                    if busy_times:
                        freebusy_text += "**Busy periods**:\n"
                        for busy in busy_times:
                            freebusy_text += f"  - {busy.get('start')} to {busy.get('end')}\n"
                    else:
                        freebusy_text += "**No busy periods found**\n"
                    
                    errors = calendar_data.get("errors", [])
                    if errors:
                        freebusy_text += "**Errors**:\n"
                        for error in errors:
                            freebusy_text += f"  - {error.get('reason', 'Unknown error')}\n"
                    
                    freebusy_text += "\n"
                
                return [types.TextContent(type="text", text=freebusy_text)]
                
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error retrieving free/busy information: {str(e)}"
            )]


async def main():
    """Run the Google Calendar v1 MCP server."""
    calendar_server = GoogleCalendarV1MCP()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await calendar_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="google-calendar-v1",
                server_version="1.0.0",
                capabilities=calendar_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main()) 