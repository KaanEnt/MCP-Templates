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
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types
from pydantic import AnyUrl
import mcp.server.stdio


class GraphQLDirectMCP:
    """MCP server with direct GraphQL query interface.
    
    Demonstrates Block's Linear MCP final pattern:
    - Direct GraphQL query execution
    - Schema awareness and documentation
    - Separate read-only and mutation tools
    - Minimal tool count with maximum flexibility
    """
    
    def __init__(self):
        self.server = Server("graphql-direct-mcp")
        self.base_url = os.getenv("GRAPHQL_ENDPOINT", "https://api.example.com/graphql")
        self.session_created = datetime.now(timezone.utc).isoformat()
        
        # Cache for schema (reduces token usage)
        self._schema_cache = None
        
        self._setup_tools()
        
    def _get_api_token(self) -> str:
        """Secure token retrieval from keyring."""
        token = keyring.get_password("graphql-direct-mcp", "api_token")
        if not token:
            raise ValueError("API token not found. Please run setup_auth.py first.")
        return token
    
    def _setup_tools(self):
        """Register MCP tools for GraphQL operations."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="execute_readonly_query",
                    description="""Execute read-only GraphQL queries for data retrieval and analysis.
                    
                    This tool provides direct access to the GraphQL API for queries that only read data.
                    Perfect for:
                    - Fetching user information, projects, issues, etc.
                    - Complex filtering and searching
                    - Analytics and reporting
                    - Data exploration
                    
                    Key Features:
                    - Direct GraphQL query execution
                    - Support for variables and fragments
                    - Comprehensive error handling
                    - Rate limit aware
                    
                    Common Query Patterns:
                    
                    # Get user information
                    query GetUser($email: String!) {
                        user(filter: { email: { eq: $email } }) {
                            id name email
                            teams { id name }
                        }
                    }
                    
                    # Search issues
                    query SearchIssues($query: String!) {
                        issues(filter: { title: { contains: $query } }) {
                            nodes {
                                id title state
                                assignee { name email }
                                project { name }
                            }
                        }
                    }
                    
                    # Get team projects
                    query TeamProjects($teamId: String!) {
                        team(id: $teamId) {
                            name
                            projects {
                                nodes {
                                    id name state
                                    issues { nodes { id title state } }
                                }
                            }
                        }
                    }
                    """,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "GraphQL query string"
                            },
                            "variables": {
                                "type": "object",
                                "description": "Variables for the GraphQL query",
                                "additionalProperties": True
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="execute_mutation_query",
                    description="""Execute GraphQL mutations for creating, updating, and deleting data.
                    
                    This tool handles all write operations through GraphQL mutations.
                    Use for:
                    - Creating new issues, projects, comments
                    - Updating existing records
                    - Deleting or archiving items
                    - Bulk operations
                    
                    Security Note: This tool performs write operations. Use with caution.
                    
                    Common Mutation Patterns:
                    
                    # Create issue
                    mutation CreateIssue($input: IssueCreateInput!) {
                        issueCreate(input: $input) {
                            success
                            issue {
                                id title state
                                project { name }
                            }
                        }
                    }
                    
                    # Update issue
                    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
                        issueUpdate(id: $id, input: $input) {
                            success
                            issue { id title state }
                        }
                    }
                    
                    # Add comment
                    mutation AddComment($issueId: String!, $body: String!) {
                        commentCreate(input: { issueId: $issueId, body: $body }) {
                            success
                            comment { id body createdAt }
                        }
                    }
                    """,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "GraphQL mutation string"
                            },
                            "variables": {
                                "type": "object", 
                                "description": "Variables for the GraphQL mutation",
                                "additionalProperties": True
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="get_graphql_schema",
                    description="""Retrieve the GraphQL schema documentation.
                    
                    This tool fetches the complete GraphQL schema including:
                    - Available types and their fields
                    - Query and mutation definitions
                    - Input types and enums
                    - Field descriptions and examples
                    
                    Use this tool when you need to:
                    - Understand available fields and types
                    - Check query syntax and structure
                    - Explore the API capabilities
                    - Build complex queries
                    
                    The schema is cached to reduce token usage in subsequent requests.
                    """,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "type_filter": {
                                "type": "string",
                                "description": "Optional filter to show only specific types (e.g., 'User', 'Issue')"
                            },
                            "include_descriptions": {
                                "type": "boolean",
                                "description": "Include field descriptions (default: true)",
                                "default": True
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls with comprehensive error handling."""
            
            if name == "execute_readonly_query":
                return await self._handle_readonly_query(arguments)
            elif name == "execute_mutation_query":
                return await self._handle_mutation_query(arguments)
            elif name == "get_graphql_schema":
                return await self._handle_get_schema(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_readonly_query(self, args: dict) -> list[types.TextContent]:
        """Execute read-only GraphQL queries."""
        query = args.get("query", "").strip()
        variables = args.get("variables", {})
        
        if not query:
            return [types.TextContent(
                type="text",
                text="❌ GraphQL query is required"
            )]
        
        # Validate this is a read-only query
        if self._contains_mutation(query):
            return [types.TextContent(
                type="text",
                text="❌ This tool only supports read-only queries. Use execute_mutation_query for mutations."
            )]
        
        try:
            headers = {
                "Authorization": f"Bearer {self._get_api_token()}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                return await self._format_graphql_response(result, query, "Query")
                
        except httpx.HTTPStatusError as e:
            return [types.TextContent(
                type="text",
                text=f"❌ GraphQL API Error: {e.response.status_code}\n\n{e.response.text}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error executing query: {str(e)}"
            )]
    
    async def _handle_mutation_query(self, args: dict) -> list[types.TextContent]:
        """Execute GraphQL mutations."""
        query = args.get("query", "").strip()
        variables = args.get("variables", {})
        
        if not query:
            return [types.TextContent(
                type="text",
                text="❌ GraphQL mutation is required"
            )]
        
        # Validate this is a mutation
        if not self._contains_mutation(query):
            return [types.TextContent(
                type="text",
                text="⚠️ This query doesn't appear to be a mutation. Use execute_readonly_query for read operations."
            )]
        
        try:
            headers = {
                "Authorization": f"Bearer {self._get_api_token()}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                return await self._format_graphql_response(result, query, "Mutation")
                
        except httpx.HTTPStatusError as e:
            return [types.TextContent(
                type="text",
                text=f"❌ GraphQL API Error: {e.response.status_code}\n\n{e.response.text}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error executing mutation: {str(e)}"
            )]
    
    async def _handle_get_schema(self, args: dict) -> list[types.TextContent]:
        """Get GraphQL schema documentation."""
        type_filter = args.get("type_filter")
        include_descriptions = args.get("include_descriptions", True)
        
        try:
            # Use cached schema if available
            if self._schema_cache is None:
                schema_query = """
                {
                    __schema {
                        types {
                            name
                            kind
                            description
                            fields {
                                name
                                type {
                                    name
                                    kind
                                    ofType {
                                        name
                                        kind
                                    }
                                }
                                description
                                args {
                                    name
                                    type {
                                        name
                                        kind
                                    }
                                    description
                                }
                            }
                        }
                        queryType { name }
                        mutationType { name }
                    }
                }
                """
                
                headers = {
                    "Authorization": f"Bearer {self._get_api_token()}",
                    "Content-Type": "application/json"
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.base_url,
                        json={"query": schema_query},
                        headers=headers,
                        timeout=30
                    )
                    response.raise_for_status()
                    self._schema_cache = response.json()
            
            # Format schema documentation
            schema_data = self._schema_cache.get("data", {}).get("__schema", {})
            
            # Filter types if requested
            types_to_show = schema_data.get("types", [])
            if type_filter:
                types_to_show = [t for t in types_to_show if type_filter.lower() in t.get("name", "").lower()]
            
            # Build formatted schema
            schema_doc = "# GraphQL Schema Documentation\n\n"
            
            # Query and Mutation root types
            query_type = schema_data.get("queryType", {}).get("name", "Query")
            mutation_type = schema_data.get("mutationType", {}).get("name", "Mutation")
            
            schema_doc += f"**Root Types:**\n- Query: `{query_type}`\n- Mutation: `{mutation_type}`\n\n"
            
            # Filter out introspection types
            filtered_types = [
                t for t in types_to_show 
                if not t.get("name", "").startswith("__")
                and t.get("kind") in ["OBJECT", "INPUT_OBJECT", "ENUM", "INTERFACE"]
            ]
            
            schema_doc += f"## Available Types ({len(filtered_types)} found)\n\n"
            
            for type_def in filtered_types[:20]:  # Limit to prevent token overflow
                name = type_def.get("name", "Unknown")
                kind = type_def.get("kind", "OBJECT")
                description = type_def.get("description", "")
                
                schema_doc += f"### {name} ({kind})\n"
                
                if include_descriptions and description:
                    schema_doc += f"{description}\n\n"
                
                fields = type_def.get("fields", [])
                if fields:
                    schema_doc += "**Fields:**\n"
                    for field in fields[:10]:  # Limit fields shown
                        field_name = field.get("name", "")
                        field_type = self._format_graphql_type(field.get("type", {}))
                        field_desc = field.get("description", "")
                        
                        schema_doc += f"- `{field_name}`: {field_type}"
                        if include_descriptions and field_desc:
                            schema_doc += f" - {field_desc}"
                        schema_doc += "\n"
                    
                    if len(fields) > 10:
                        schema_doc += f"  *... and {len(fields) - 10} more fields*\n"
                
                schema_doc += "\n"
            
            if len(filtered_types) > 20:
                schema_doc += f"\n*Showing first 20 of {len(filtered_types)} types. Use type_filter to narrow results.*\n"
            
            schema_doc += "\n## Example Queries\n\n"
            schema_doc += "```graphql\n"
            schema_doc += "# Basic query structure\n"
            schema_doc += "query GetItems($filter: String) {\n"
            schema_doc += "  items(filter: $filter) {\n"
            schema_doc += "    id\n"
            schema_doc += "    name\n"
            schema_doc += "    createdAt\n"
            schema_doc += "  }\n"
            schema_doc += "}\n\n"
            schema_doc += "# Basic mutation structure\n"
            schema_doc += "mutation CreateItem($input: ItemInput!) {\n"
            schema_doc += "  itemCreate(input: $input) {\n"
            schema_doc += "    success\n"
            schema_doc += "    item { id name }\n"
            schema_doc += "  }\n"
            schema_doc += "}\n"
            schema_doc += "```\n"
            
            return [types.TextContent(type="text", text=schema_doc)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error fetching schema: {str(e)}"
            )]
    
    def _contains_mutation(self, query: str) -> bool:
        """Check if GraphQL query contains mutations."""
        # Simple check for mutation keywords
        query_lower = query.lower().strip()
        return (
            query_lower.startswith("mutation") or
            "mutation " in query_lower or
            any(word in query_lower for word in ["create", "update", "delete", "remove", "insert", "upsert"])
        )
    
    def _format_graphql_type(self, type_info: dict) -> str:
        """Format GraphQL type information for display."""
        if not type_info:
            return "Unknown"
        
        kind = type_info.get("kind", "")
        name = type_info.get("name")
        
        if kind == "NON_NULL":
            of_type = type_info.get("ofType", {})
            return f"{self._format_graphql_type(of_type)}!"
        elif kind == "LIST":
            of_type = type_info.get("ofType", {})
            return f"[{self._format_graphql_type(of_type)}]"
        elif name:
            return name
        else:
            return "Unknown"
    
    async def _format_graphql_response(self, result: dict, query: str, operation_type: str) -> list[types.TextContent]:
        """Format GraphQL response for LLM consumption."""
        
        # Check for errors
        if "errors" in result:
            error_text = f"❌ GraphQL {operation_type} Errors:\n\n"
            for error in result["errors"]:
                error_text += f"• {error.get('message', 'Unknown error')}\n"
                if 'locations' in error:
                    locations = error['locations']
                    error_text += f"  At line {locations[0].get('line', '?')}, column {locations[0].get('column', '?')}\n"
            
            error_text += f"\n**Query:**\n```graphql\n{query}\n```"
            return [types.TextContent(type="text", text=error_text)]
        
        # Format successful response
        data = result.get("data", {})
        
        if not data:
            return [types.TextContent(
                type="text",
                text=f"✅ {operation_type} executed successfully - No data returned"
            )]
        
        # Format response as structured markdown
        response_text = f"## {operation_type} Results ✅\n\n"
        
        # Pretty print the JSON response
        formatted_data = json.dumps(data, indent=2, default=str)
        
        # For large responses, truncate and provide summary
        if len(formatted_data) > 3000:
            # Try to provide a summary for large responses
            summary = self._summarize_graphql_data(data)
            response_text += summary + "\n\n"
            response_text += "**Response Data (truncated):**\n"
            response_text += f"```json\n{formatted_data[:2000]}...\n```\n"
            response_text += "\n*Response truncated - use more specific queries for detailed results*"
        else:
            response_text += "**Response Data:**\n"
            response_text += f"```json\n{formatted_data}\n```"
        
        return [types.TextContent(type="text", text=response_text)]
    
    def _summarize_graphql_data(self, data: dict) -> str:
        """Create a summary of GraphQL response data."""
        summary = "**Response Summary:**\n"
        
        for key, value in data.items():
            if isinstance(value, list):
                summary += f"- `{key}`: {len(value)} items\n"
                if value and isinstance(value[0], dict):
                    # Show field names from first item
                    first_item = value[0]
                    field_names = list(first_item.keys())[:5]
                    summary += f"  Fields: {', '.join(field_names)}\n"
            elif isinstance(value, dict):
                summary += f"- `{key}`: Object with {len(value)} fields\n"
                field_names = list(value.keys())[:5]
                summary += f"  Fields: {', '.join(field_names)}\n"
            else:
                summary += f"- `{key}`: {type(value).__name__}\n"
        
        return summary


async def main():
    """Run the MCP server."""
    graphql_server = GraphQLDirectMCP()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await graphql_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="graphql-direct-mcp",
                server_version="1.0.0",
                capabilities=graphql_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main()) 