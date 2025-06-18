#!/usr/bin/env python3

import json
import os
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import keyring
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource
)
import mcp.types as types
from pydantic import AnyUrl
import mcp.server.stdio


class BasicAPIWrapper:
    """Example MCP server that wraps a hypothetical task management API.
    
    Demonstrates Block's best practices:
    - Design top-down from workflows
    - Bundle related operations
    - Secure credential management
    - Clear tool descriptions
    """
    
    def __init__(self):
        self.server = Server("basic-api-wrapper")
        self.base_url = os.getenv("API_BASE_URL", "https://api.example.com")
        self.session_created = datetime.now(timezone.utc).isoformat()
        
        # Setup tools
        self._setup_tools()
        
    def _get_api_token(self) -> str:
        """Secure token retrieval from keyring."""
        token = keyring.get_password("basic-api-wrapper", "api_token")
        if not token:
            raise ValueError("API token not found. Please run setup_auth.py first.")
        return token
    
    def _setup_tools(self):
        """Register MCP tools following Block's design principles."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="manage_task",
                    description="""Comprehensive task management tool that handles create, update, and read operations.
                    
                    Use this for common workflows like:
                    - Creating new tasks with details
                    - Updating task status or details
                    - Getting task information
                    
                    Operation types:
                    - 'create': Create new task (title required)
                    - 'update': Update existing task (task_id required)
                    - 'get': Get task details (task_id required)
                    - 'list': List tasks (optional: status filter)
                    """,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["create", "update", "get", "list"],
                                "description": "The operation to perform"
                            },
                            "task_id": {
                                "type": "string",
                                "description": "Task ID (required for update/get operations)"
                            },
                            "title": {
                                "type": "string",
                                "description": "Task title (required for create operation)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Task description (optional)"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["todo", "in_progress", "done"],
                                "description": "Task status"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "Task priority"
                            }
                        },
                        "required": ["operation"]
                    }
                ),
                types.Tool(
                    name="get_team_overview",
                    description="""Get comprehensive team information including members, projects, and recent activity.
                    
                    This tool bundles multiple read-only operations:
                    - Team member list with roles
                    - Active projects summary
                    - Recent team activity
                    - Team performance metrics
                    
                    Perfect for questions like "What's my team working on?" or "Who's available for new tasks?"
                    """,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "team_id": {
                                "type": "string",
                                "description": "Team identifier (optional, defaults to user's primary team)"
                            },
                            "include_metrics": {
                                "type": "boolean",
                                "description": "Include performance metrics (default: true)"
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls with comprehensive error handling."""
            
            if name == "manage_task":
                return await self._handle_task_management(arguments)
            elif name == "get_team_overview":
                return await self._handle_team_overview(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_task_management(self, args: dict) -> list[types.TextContent]:
        """Handle all task-related operations in a single tool."""
        operation = args.get("operation")
        
        try:
            headers = {"Authorization": f"Bearer {self._get_api_token()}"}
            
            async with httpx.AsyncClient() as client:
                if operation == "create":
                    payload = {
                        "title": args["title"],
                        "description": args.get("description", ""),
                        "status": args.get("status", "todo"),
                        "priority": args.get("priority", "medium")
                    }
                    response = await client.post(
                        f"{self.base_url}/tasks",
                        json=payload,
                        headers=headers
                    )
                    response.raise_for_status()
                    task = response.json()
                    
                    return [types.TextContent(
                        type="text",
                        text=f"✅ Task created successfully!\n\n**Task ID**: {task['id']}\n**Title**: {task['title']}\n**Status**: {task['status']}\n**Priority**: {task['priority']}"
                    )]
                
                elif operation == "update":
                    task_id = args.get("task_id")
                    if not task_id:
                        raise ValueError("task_id is required for update operations")
                    
                    payload = {}
                    if "title" in args:
                        payload["title"] = args["title"]
                    if "description" in args:
                        payload["description"] = args["description"]
                    if "status" in args:
                        payload["status"] = args["status"]
                    if "priority" in args:
                        payload["priority"] = args["priority"]
                    
                    response = await client.patch(
                        f"{self.base_url}/tasks/{task_id}",
                        json=payload,
                        headers=headers
                    )
                    response.raise_for_status()
                    task = response.json()
                    
                    return [types.TextContent(
                        type="text",
                        text=f"✅ Task updated successfully!\n\n**Task ID**: {task['id']}\n**Title**: {task['title']}\n**Status**: {task['status']}\n**Priority**: {task['priority']}"
                    )]
                
                elif operation == "get":
                    task_id = args.get("task_id")
                    if not task_id:
                        raise ValueError("task_id is required for get operations")
                    
                    response = await client.get(
                        f"{self.base_url}/tasks/{task_id}",
                        headers=headers
                    )
                    response.raise_for_status()
                    task = response.json()
                    
                    return [types.TextContent(
                        type="text",
                        text=f"**Task Details**\n\n**ID**: {task['id']}\n**Title**: {task['title']}\n**Description**: {task.get('description', 'No description')}\n**Status**: {task['status']}\n**Priority**: {task['priority']}\n**Created**: {task.get('created_at', 'Unknown')}"
                    )]
                
                elif operation == "list":
                    params = {}
                    if "status" in args:
                        params["status"] = args["status"]
                    
                    response = await client.get(
                        f"{self.base_url}/tasks",
                        params=params,
                        headers=headers
                    )
                    response.raise_for_status()
                    tasks = response.json()
                    
                    if not tasks:
                        return [types.TextContent(
                            type="text",
                            text="No tasks found."
                        )]
                    
                    task_list = "**Task List**\n\n"
                    for task in tasks[:10]:  # Limit to first 10 for readability
                        task_list += f"• **{task['title']}** (ID: {task['id']}) - {task['status']} - {task['priority']} priority\n"
                    
                    if len(tasks) > 10:
                        task_list += f"\n*Showing first 10 of {len(tasks)} tasks*"
                    
                    return [types.TextContent(type="text", text=task_list)]
                
                else:
                    raise ValueError(f"Unknown operation: {operation}")
        
        except httpx.HTTPStatusError as e:
            return [types.TextContent(
                type="text",
                text=f"❌ API Error: {e.response.status_code} - {e.response.text}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error: {str(e)}"
            )]
    
    async def _handle_team_overview(self, args: dict) -> list[types.TextContent]:
        """Get comprehensive team overview - bundles multiple read operations."""
        try:
            headers = {"Authorization": f"Bearer {self._get_api_token()}"}
            team_id = args.get("team_id", "default")
            include_metrics = args.get("include_metrics", True)
            
            async with httpx.AsyncClient() as client:
                # Parallel API calls for efficiency
                team_response, members_response, projects_response = await asyncio.gather(
                    client.get(f"{self.base_url}/teams/{team_id}", headers=headers),
                    client.get(f"{self.base_url}/teams/{team_id}/members", headers=headers),
                    client.get(f"{self.base_url}/teams/{team_id}/projects", headers=headers)
                )
                
                team_response.raise_for_status()
                members_response.raise_for_status()
                projects_response.raise_for_status()
                
                team = team_response.json()
                members = members_response.json()
                projects = projects_response.json()
                
                # Build comprehensive overview
                overview = f"# Team Overview: {team['name']}\n\n"
                
                # Team members
                overview += "## Team Members\n"
                for member in members:
                    status = "🟢" if member.get('available', True) else "🔴"
                    overview += f"• {status} **{member['name']}** - {member['role']}\n"
                
                # Active projects
                overview += "\n## Active Projects\n"
                active_projects = [p for p in projects if p.get('status') == 'active']
                if active_projects:
                    for project in active_projects:
                        overview += f"• **{project['name']}** - {project.get('progress', 'N/A')}% complete\n"
                else:
                    overview += "No active projects\n"
                
                # Metrics if requested
                if include_metrics:
                    metrics_response = await client.get(
                        f"{self.base_url}/teams/{team_id}/metrics",
                        headers=headers
                    )
                    if metrics_response.status_code == 200:
                        metrics = metrics_response.json()
                        overview += "\n## Team Metrics\n"
                        overview += f"• Tasks completed this week: {metrics.get('tasks_completed', 'N/A')}\n"
                        overview += f"• Average completion time: {metrics.get('avg_completion_time', 'N/A')}\n"
                        overview += f"• Team velocity: {metrics.get('velocity', 'N/A')}\n"
                
                overview += f"\n*Retrieved at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"
                
                return [types.TextContent(type="text", text=overview)]
        
        except httpx.HTTPStatusError as e:
            return [types.TextContent(
                type="text",
                text=f"❌ API Error: {e.response.status_code} - {e.response.text}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error: {str(e)}"
            )]


async def main():
    """Run the MCP server."""
    wrapper = BasicAPIWrapper()
    
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await wrapper.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="basic-api-wrapper",
                server_version="1.0.0",
                capabilities=wrapper.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main()) 