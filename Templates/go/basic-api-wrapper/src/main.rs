use mcp_sdk::{Server, ServerOptions, Tool, ToolSchema, Content, TextContent};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use reqwest::{Client, Error as ReqwestError};
use std::collections::HashMap;
use std::env;
use tokio;
use anyhow::{Result, Context};

#[derive(Debug, Deserialize)]
struct TaskOperation {
    operation: String,
    task_id: Option<String>,
    title: Option<String>,
    description: Option<String>,
    status: Option<String>,
    priority: Option<String>,
}

#[derive(Debug, Deserialize)]
struct TeamOverview {
    team_id: Option<String>,
    include_metrics: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Task {
    id: String,
    title: String,
    description: Option<String>,
    status: String,
    priority: String,
    created_at: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct TeamMember {
    name: String,
    role: String,
    available: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Project {
    name: String,
    status: String,
    progress: Option<u32>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Team {
    name: String,
}

pub struct BasicApiWrapperMcp {
    server: Server,
    client: Client,
    base_url: String,
}

impl BasicApiWrapperMcp {
    pub fn new() -> Result<Self> {
        let base_url = env::var("API_BASE_URL")
            .unwrap_or_else(|_| "https://api.example.com".to_string());

        let server = Server::new(ServerOptions {
            name: "basic-api-wrapper-rust".to_string(),
            version: "1.0.0".to_string(),
        })?;

        let client = Client::new();

        Ok(Self {
            server,
            client,
            base_url,
        })
    }

    pub async fn setup_tools(&mut self) -> Result<()> {
        // Register manage_task tool
        let manage_task_tool = Tool {
            name: "manage_task".to_string(),
            description: r#"Comprehensive task management tool that handles create, update, and read operations.
            
            Use this for common workflows like:
            - Creating new tasks with details
            - Updating task status or details
            - Getting task information
            
            Operation types:
            - 'create': Create new task (title required)
            - 'update': Update existing task (task_id required)
            - 'get': Get task details (task_id required)
            - 'list': List tasks (optional: status filter)"#.to_string(),
            input_schema: ToolSchema {
                schema_type: "object".to_string(),
                properties: {
                    let mut props = HashMap::new();
                    props.insert("operation".to_string(), json!({
                        "type": "string",
                        "enum": ["create", "update", "get", "list"],
                        "description": "The operation to perform"
                    }));
                    props.insert("task_id".to_string(), json!({
                        "type": "string",
                        "description": "Task ID (required for update/get operations)"
                    }));
                    props.insert("title".to_string(), json!({
                        "type": "string",
                        "description": "Task title (required for create operation)"
                    }));
                    props.insert("description".to_string(), json!({
                        "type": "string",
                        "description": "Task description (optional)"
                    }));
                    props.insert("status".to_string(), json!({
                        "type": "string",
                        "enum": ["todo", "in_progress", "done"],
                        "description": "Task status"
                    }));
                    props.insert("priority".to_string(), json!({
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Task priority"
                    }));
                    props
                },
                required: vec!["operation".to_string()],
            },
        };

        // Register get_team_overview tool
        let team_overview_tool = Tool {
            name: "get_team_overview".to_string(),
            description: r#"Get comprehensive team information including members, projects, and recent activity.
            
            This tool bundles multiple read-only operations:
            - Team member list with roles
            - Active projects summary
            - Recent team activity
            - Team performance metrics
            
            Perfect for questions like "What's my team working on?" or "Who's available for new tasks?""#.to_string(),
            input_schema: ToolSchema {
                schema_type: "object".to_string(),
                properties: {
                    let mut props = HashMap::new();
                    props.insert("team_id".to_string(), json!({
                        "type": "string",
                        "description": "Team identifier (optional, defaults to user's primary team)"
                    }));
                    props.insert("include_metrics".to_string(), json!({
                        "type": "boolean",
                        "description": "Include performance metrics (default: true)"
                    }));
                    props
                },
                required: vec![],
            },
        };

        self.server.register_tool(manage_task_tool)?;
        self.server.register_tool(team_overview_tool)?;

        Ok(())
    }

    async fn get_api_token(&self) -> Result<String> {
        // In a real implementation, you'd use a secure credential store
        env::var("API_TOKEN")
            .context("API token not found. Please set API_TOKEN environment variable.")
    }

    async fn handle_task_management(&self, args: Value) -> Result<Vec<Content>> {
        let task_op: TaskOperation = serde_json::from_value(args)
            .context("Failed to parse task operation arguments")?;

        let token = self.get_api_token().await?;
        let auth_header = format!("Bearer {}", token);

        match task_op.operation.as_str() {
            "create" => {
                let title = task_op.title
                    .ok_or_else(|| anyhow::anyhow!("title is required for create operations"))?;

                let payload = json!({
                    "title": title,
                    "description": task_op.description.unwrap_or_default(),
                    "status": task_op.status.unwrap_or_else(|| "todo".to_string()),
                    "priority": task_op.priority.unwrap_or_else(|| "medium".to_string())
                });

                let response = self.client
                    .post(&format!("{}/tasks", self.base_url))
                    .header("Authorization", auth_header)
                    .header("Content-Type", "application/json")
                    .json(&payload)
                    .send()
                    .await?;

                let task: Task = response.json().await?;

                Ok(vec![Content::Text(TextContent {
                    text: format!(
                        "✅ Task created successfully!\n\n**Task ID**: {}\n**Title**: {}\n**Status**: {}\n**Priority**: {}",
                        task.id, task.title, task.status, task.priority
                    ),
                })])
            }
            "update" => {
                let task_id = task_op.task_id
                    .ok_or_else(|| anyhow::anyhow!("task_id is required for update operations"))?;

                let mut payload = json!({});
                if let Some(title) = task_op.title {
                    payload["title"] = json!(title);
                }
                if let Some(description) = task_op.description {
                    payload["description"] = json!(description);
                }
                if let Some(status) = task_op.status {
                    payload["status"] = json!(status);
                }
                if let Some(priority) = task_op.priority {
                    payload["priority"] = json!(priority);
                }

                let response = self.client
                    .patch(&format!("{}/tasks/{}", self.base_url, task_id))
                    .header("Authorization", auth_header)
                    .header("Content-Type", "application/json")
                    .json(&payload)
                    .send()
                    .await?;

                let task: Task = response.json().await?;

                Ok(vec![Content::Text(TextContent {
                    text: format!(
                        "✅ Task updated successfully!\n\n**Task ID**: {}\n**Title**: {}\n**Status**: {}\n**Priority**: {}",
                        task.id, task.title, task.status, task.priority
                    ),
                })])
            }
            "get" => {
                let task_id = task_op.task_id
                    .ok_or_else(|| anyhow::anyhow!("task_id is required for get operations"))?;

                let response = self.client
                    .get(&format!("{}/tasks/{}", self.base_url, task_id))
                    .header("Authorization", auth_header)
                    .send()
                    .await?;

                let task: Task = response.json().await?;

                Ok(vec![Content::Text(TextContent {
                    text: format!(
                        "**Task Details**\n\n**ID**: {}\n**Title**: {}\n**Description**: {}\n**Status**: {}\n**Priority**: {}\n**Created**: {}",
                        task.id,
                        task.title,
                        task.description.unwrap_or_else(|| "No description".to_string()),
                        task.status,
                        task.priority,
                        task.created_at.unwrap_or_else(|| "Unknown".to_string())
                    ),
                })])
            }
            "list" => {
                let mut url = format!("{}/tasks", self.base_url);
                if let Some(status) = task_op.status {
                    url = format!("{}?status={}", url, status);
                }

                let response = self.client
                    .get(&url)
                    .header("Authorization", auth_header)
                    .send()
                    .await?;

                let tasks: Vec<Task> = response.json().await?;

                if tasks.is_empty() {
                    return Ok(vec![Content::Text(TextContent {
                        text: "No tasks found.".to_string(),
                    })]);
                }

                let mut task_list = "**Task List**\n\n".to_string();
                for task in tasks.iter().take(10) {
                    task_list.push_str(&format!(
                        "• **{}** (ID: {}) - {} - {} priority\n",
                        task.title, task.id, task.status, task.priority
                    ));
                }

                if tasks.len() > 10 {
                    task_list.push_str(&format!("\n*Showing first 10 of {} tasks*", tasks.len()));
                }

                Ok(vec![Content::Text(TextContent { text: task_list })])
            }
            _ => Err(anyhow::anyhow!("Unknown operation: {}", task_op.operation)),
        }
    }

    async fn handle_team_overview(&self, args: Value) -> Result<Vec<Content>> {
        let team_args: TeamOverview = serde_json::from_value(args)
            .context("Failed to parse team overview arguments")?;

        let token = self.get_api_token().await?;
        let auth_header = format!("Bearer {}", token);
        let team_id = team_args.team_id.unwrap_or_else(|| "default".to_string());
        let include_metrics = team_args.include_metrics.unwrap_or(true);

        // Parallel API calls for efficiency
        let team_url = format!("{}/teams/{}", self.base_url, team_id);
        let members_url = format!("{}/teams/{}/members", self.base_url, team_id);
        let projects_url = format!("{}/teams/{}/projects", self.base_url, team_id);

        let (team_response, members_response, projects_response) = tokio::try_join!(
            self.client.get(&team_url).header("Authorization", &auth_header).send(),
            self.client.get(&members_url).header("Authorization", &auth_header).send(),
            self.client.get(&projects_url).header("Authorization", &auth_header).send()
        )?;

        let team: Team = team_response.json().await?;
        let members: Vec<TeamMember> = members_response.json().await?;
        let projects: Vec<Project> = projects_response.json().await?;

        let mut overview = format!("# Team Overview: {}\n\n", team.name);

        // Team members
        overview.push_str("## Team Members\n");
        for member in &members {
            let status = if member.available.unwrap_or(true) { "🟢" } else { "🔴" };
            overview.push_str(&format!("• {} **{}** - {}\n", status, member.name, member.role));
        }

        // Active projects
        overview.push_str("\n## Active Projects\n");
        let active_projects: Vec<&Project> = projects.iter()
            .filter(|p| p.status == "active")
            .collect();

        if !active_projects.is_empty() {
            for project in active_projects {
                let progress = project.progress.map(|p| p.to_string()).unwrap_or_else(|| "N/A".to_string());
                overview.push_str(&format!("• **{}** - {}% complete\n", project.name, progress));
            }
        } else {
            overview.push_str("No active projects\n");
        }

        // Metrics if requested
        if include_metrics {
            if let Ok(metrics_response) = self.client
                .get(&format!("{}/teams/{}/metrics", self.base_url, team_id))
                .header("Authorization", &auth_header)
                .send()
                .await
            {
                if let Ok(metrics) = metrics_response.json::<Value>().await {
                    overview.push_str("\n## Team Metrics\n");
                    overview.push_str(&format!(
                        "• Tasks completed this week: {}\n• Average completion time: {}\n• Team velocity: {}\n",
                        metrics.get("tasks_completed").and_then(|v| v.as_str()).unwrap_or("N/A"),
                        metrics.get("avg_completion_time").and_then(|v| v.as_str()).unwrap_or("N/A"),
                        metrics.get("velocity").and_then(|v| v.as_str()).unwrap_or("N/A")
                    ));
                }
            }
        }

        let now = chrono::Utc::now().format("%Y-%m-%d %H:%M UTC");
        overview.push_str(&format!("\n*Retrieved at: {}*", now));

        Ok(vec![Content::Text(TextContent { text: overview })])
    }

    pub async fn run(&mut self) -> Result<()> {
        self.setup_tools().await?;
        
        self.server.set_tool_handler("manage_task", |args| async move {
            self.handle_task_management(args).await
        });

        self.server.set_tool_handler("get_team_overview", |args| async move {
            self.handle_team_overview(args).await
        });

        println!("Basic API Wrapper MCP Server (Rust) running on stdio");
        self.server.run().await?;
        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let mut server = BasicApiWrapperMcp::new()?;
    server.run().await?;
    Ok(())
} 