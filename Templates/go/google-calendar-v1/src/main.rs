/*
 * Google Calendar MCP v1 - Thin API Wrapper (Rust)
 * This represents the initial version mentioned in Block's playbook that served 
 * as a thin wrapper around the external API before the v2 analytics improvements.
 */

use mcp_sdk::{Server, ServerOptions, Tool, ToolSchema, Content, TextContent};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use reqwest::{Client, Error as ReqwestError};
use std::collections::HashMap;
use std::env;
use tokio;
use anyhow::{Result, Context};
use chrono::{DateTime, Utc};

#[derive(Debug, Deserialize)]
struct CalendarListArgs {
    // No arguments needed
}

#[derive(Debug, Deserialize)]
struct EventsListArgs {
    calendar_id: Option<String>,
    time_max: Option<String>,
    time_min: Option<String>,
    verbose: Option<bool>,
}

#[derive(Debug, Deserialize)]
struct TimezoneArgs {
    calendar_id: Option<String>,
}

#[derive(Debug, Deserialize)]
struct FreeBusyArgs {
    time_min: String,
    time_max: String,
    timezone: Option<String>,
    calendar_ids: Option<Vec<String>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Calendar {
    id: Option<String>,
    summary: Option<String>,
    primary: Option<bool>,
    #[serde(rename = "accessRole")]
    access_role: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct CalendarEvent {
    id: Option<String>,
    summary: Option<String>,
    description: Option<String>,
    start: Option<EventDateTime>,
    end: Option<EventDateTime>,
    status: Option<String>,
    creator: Option<EventPerson>,
    organizer: Option<EventPerson>,
    attendees: Option<Vec<EventAttendee>>,
    location: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct EventDateTime {
    #[serde(rename = "dateTime")]
    date_time: Option<String>,
    date: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct EventPerson {
    email: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct EventAttendee {
    email: Option<String>,
    #[serde(rename = "responseStatus")]
    response_status: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct CalendarInfo {
    summary: Option<String>,
    #[serde(rename = "timeZone")]
    time_zone: Option<String>,
    location: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct FreeBusyRequest {
    #[serde(rename = "timeMin")]
    time_min: String,
    #[serde(rename = "timeMax")]
    time_max: String,
    #[serde(rename = "timeZone")]
    time_zone: String,
    items: Vec<FreeBusyRequestItem>,
}

#[derive(Debug, Serialize, Deserialize)]
struct FreeBusyRequestItem {
    id: String,
}

pub struct GoogleCalendarV1MCP {
    server: Server,
    client: Client,
    base_url: String,
}

impl GoogleCalendarV1MCP {
    pub fn new() -> Result<Self> {
        let base_url = "https://www.googleapis.com/calendar/v3".to_string();

        let server = Server::new(ServerOptions {
            name: "google-calendar-v1-rust".to_string(),
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
        // Register list_calendars tool
        let list_calendars_tool = Tool {
            name: "list_calendars".to_string(),
            description: "Lists all user calendars.".to_string(),
            input_schema: ToolSchema {
                schema_type: "object".to_string(),
                properties: HashMap::new(),
                required: vec![],
            },
        };

        // Register list_calendar_events tool
        let list_events_tool = Tool {
            name: "list_calendar_events".to_string(),
            description: "Get all events for a specified time period for a given calendar.".to_string(),
            input_schema: ToolSchema {
                schema_type: "object".to_string(),
                properties: {
                    let mut props = HashMap::new();
                    props.insert("calendar_id".to_string(), json!({
                        "type": "string",
                        "description": "Calendar ID (default: primary)",
                        "default": "primary"
                    }));
                    props.insert("time_max".to_string(), json!({
                        "type": "string",
                        "description": "Upper bound (exclusive) for an event's start time (RFC3339 timestamp)"
                    }));
                    props.insert("time_min".to_string(), json!({
                        "type": "string",
                        "description": "Lower bound (exclusive) for an event's end time (RFC3339 timestamp)"
                    }));
                    props.insert("verbose".to_string(), json!({
                        "type": "boolean",
                        "description": "Include detailed event information",
                        "default": false
                    }));
                    props
                },
                required: vec![],
            },
        };

        // Register retrieve_timezone tool
        let timezone_tool = Tool {
            name: "retrieve_timezone".to_string(),
            description: "Retrieves timezone for a given calendar.".to_string(),
            input_schema: ToolSchema {
                schema_type: "object".to_string(),
                properties: {
                    let mut props = HashMap::new();
                    props.insert("calendar_id".to_string(), json!({
                        "type": "string",
                        "description": "Calendar ID (default: primary)",
                        "default": "primary"
                    }));
                    props
                },
                required: vec![],
            },
        };

        // Register retrieve_calendar_free_busy_slots tool
        let freebusy_tool = Tool {
            name: "retrieve_calendar_free_busy_slots".to_string(),
            description: "Retrieves free and busy slots from the calendars of the calendar_ids list.".to_string(),
            input_schema: ToolSchema {
                schema_type: "object".to_string(),
                properties: {
                    let mut props = HashMap::new();
                    props.insert("time_min".to_string(), json!({
                        "type": "string",
                        "description": "Lower bound for the query (RFC3339 timestamp)"
                    }));
                    props.insert("time_max".to_string(), json!({
                        "type": "string",
                        "description": "Upper bound for the query (RFC3339 timestamp)"
                    }));
                    props.insert("timezone".to_string(), json!({
                        "type": "string",
                        "description": "Timezone to use for the query",
                        "default": "UTC"
                    }));
                    props.insert("calendar_ids".to_string(), json!({
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of calendar IDs to query",
                        "default": ["primary"]
                    }));
                    props
                },
                required: vec!["time_min".to_string(), "time_max".to_string()],
            },
        };

        self.server.register_tool(list_calendars_tool)?;
        self.server.register_tool(list_events_tool)?;
        self.server.register_tool(timezone_tool)?;
        self.server.register_tool(freebusy_tool)?;

        Ok(())
    }

    async fn get_api_token(&self) -> Result<String> {
        // In a real implementation, you'd use a secure credential store
        env::var("GOOGLE_ACCESS_TOKEN")
            .context("Google access token not found. Please set GOOGLE_ACCESS_TOKEN environment variable.")
    }

    async fn handle_list_calendars(&self, _args: Value) -> Result<Vec<Content>> {
        let token = self.get_api_token().await?;
        let auth_header = format!("Bearer {}", token);

        let response = self.client
            .get(&format!("{}/users/me/calendarList", self.base_url))
            .header("Authorization", auth_header)
            .send()
            .await?;

        let data: Value = response.json().await?;

        // Return raw API response as text
        let mut calendars_text = "**Calendars List**\n\n".to_string();
        
        if let Some(items) = data.get("items").and_then(|v| v.as_array()) {
            for calendar in items {
                let summary = calendar.get("summary")
                    .and_then(|v| v.as_str())
                    .unwrap_or("Unknown");
                let id = calendar.get("id")
                    .and_then(|v| v.as_str())
                    .unwrap_or("Unknown");
                let primary = calendar.get("primary")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);
                let access_role = calendar.get("accessRole")
                    .and_then(|v| v.as_str())
                    .unwrap_or("Unknown");

                calendars_text.push_str(&format!(
                    "• **{}** (ID: {})\n  - Primary: {}\n  - Access Role: {}\n\n",
                    summary, id, primary, access_role
                ));
            }
        }

        Ok(vec![Content::Text(TextContent {
            text: calendars_text,
        })])
    }

    async fn handle_list_calendar_events(&self, args: Value) -> Result<Vec<Content>> {
        let events_args: EventsListArgs = serde_json::from_value(args)
            .context("Failed to parse events list arguments")?;

        let calendar_id = events_args.calendar_id.unwrap_or_else(|| "primary".to_string());
        let verbose = events_args.verbose.unwrap_or(false);
        
        let token = self.get_api_token().await?;
        let auth_header = format!("Bearer {}", token);

        let mut url = format!("{}/calendars/{}/events", self.base_url, calendar_id);
        let mut params = vec![];
        
        if let Some(time_max) = &events_args.time_max {
            params.push(("timeMax", time_max.as_str()));
        }
        if let Some(time_min) = &events_args.time_min {
            params.push(("timeMin", time_min.as_str()));
        }

        let response = self.client
            .get(&url)
            .query(&params)
            .header("Authorization", auth_header)
            .send()
            .await?;

        let data: Value = response.json().await?;

        // Return verbose API response - this gets unwieldy quickly
        let events = data.get("items").and_then(|v| v.as_array()).unwrap_or(&vec![]);
        
        if events.is_empty() {
            return Ok(vec![Content::Text(TextContent {
                text: "No events found for the specified time period.".to_string(),
            })]);
        }

        let mut events_text = format!("**Calendar Events** ({} found)\n\n", events.len());

        for event in events.iter().take(20) { // Limit to prevent overwhelming output
            let summary = event.get("summary")
                .and_then(|v| v.as_str())
                .unwrap_or("No title");
            
            events_text.push_str(&format!("### {}\n", summary));

            // Start time
            if let Some(start) = event.get("start") {
                let start_time = start.get("dateTime")
                    .or_else(|| start.get("date"))
                    .and_then(|v| v.as_str())
                    .unwrap_or("Unknown");
                events_text.push_str(&format!("**Start**: {}\n", start_time));
            }

            // End time
            if let Some(end) = event.get("end") {
                let end_time = end.get("dateTime")
                    .or_else(|| end.get("date"))
                    .and_then(|v| v.as_str())
                    .unwrap_or("Unknown");
                events_text.push_str(&format!("**End**: {}\n", end_time));
            }

            if verbose {
                // Include all the verbose details that make this painful to use
                let id = event.get("id").and_then(|v| v.as_str()).unwrap_or("Unknown");
                let status = event.get("status").and_then(|v| v.as_str()).unwrap_or("Unknown");
                let creator_email = event.get("creator")
                    .and_then(|c| c.get("email"))
                    .and_then(|v| v.as_str())
                    .unwrap_or("Unknown");
                let organizer_email = event.get("organizer")
                    .and_then(|o| o.get("email"))
                    .and_then(|v| v.as_str())
                    .unwrap_or("Unknown");

                events_text.push_str(&format!(
                    "**ID**: {}\n**Status**: {}\n**Creator**: {}\n**Organizer**: {}\n",
                    id, status, creator_email, organizer_email
                ));

                if let Some(attendees) = event.get("attendees").and_then(|v| v.as_array()) {
                    events_text.push_str(&format!("**Attendees** ({}):\n", attendees.len()));
                    for attendee in attendees {
                        let email = attendee.get("email").and_then(|v| v.as_str()).unwrap_or("Unknown");
                        let status = attendee.get("responseStatus").and_then(|v| v.as_str()).unwrap_or("Unknown");
                        events_text.push_str(&format!("  - {} ({})\n", email, status));
                    }
                }

                if let Some(description) = event.get("description").and_then(|v| v.as_str()) {
                    events_text.push_str(&format!("**Description**: {}\n", description));
                }

                if let Some(location) = event.get("location").and_then(|v| v.as_str()) {
                    events_text.push_str(&format!("**Location**: {}\n", location));
                }
            }

            events_text.push_str("\n---\n\n");
        }

        // This response can become extremely long and unwieldy
        if events_text.len() > 8000 {
            events_text.truncate(8000);
            events_text.push_str("\n\n*[Response truncated - too much data]*");
        }

        Ok(vec![Content::Text(TextContent { text: events_text })])
    }

    async fn handle_retrieve_timezone(&self, args: Value) -> Result<Vec<Content>> {
        let timezone_args: TimezoneArgs = serde_json::from_value(args)
            .context("Failed to parse timezone arguments")?;

        let calendar_id = timezone_args.calendar_id.unwrap_or_else(|| "primary".to_string());
        
        let token = self.get_api_token().await?;
        let auth_header = format!("Bearer {}", token);

        let response = self.client
            .get(&format!("{}/calendars/{}", self.base_url, calendar_id))
            .header("Authorization", auth_header)
            .send()
            .await?;

        let data: Value = response.json().await?;

        let summary = data.get("summary").and_then(|v| v.as_str()).unwrap_or("Unknown");
        let timezone = data.get("timeZone").and_then(|v| v.as_str()).unwrap_or("Unknown");
        let location = data.get("location").and_then(|v| v.as_str()).unwrap_or("Not specified");

        let timezone_text = format!(
            "**Calendar Timezone Information**\n\n**Calendar**: {}\n**Timezone**: {}\n**Location**: {}\n",
            summary, timezone, location
        );

        Ok(vec![Content::Text(TextContent { text: timezone_text })])
    }

    async fn handle_retrieve_free_busy_slots(&self, args: Value) -> Result<Vec<Content>> {
        let freebusy_args: FreeBusyArgs = serde_json::from_value(args)
            .context("Failed to parse free/busy arguments")?;

        let timezone = freebusy_args.timezone.unwrap_or_else(|| "UTC".to_string());
        let calendar_ids = freebusy_args.calendar_ids.unwrap_or_else(|| vec!["primary".to_string()]);

        let token = self.get_api_token().await?;
        let auth_header = format!("Bearer {}", token);

        let payload = FreeBusyRequest {
            time_min: freebusy_args.time_min.clone(),
            time_max: freebusy_args.time_max.clone(),
            time_zone: timezone.clone(),
            items: calendar_ids.iter().map(|id| FreeBusyRequestItem { id: id.clone() }).collect(),
        };

        let response = self.client
            .post(&format!("{}/freeBusy", self.base_url))
            .header("Authorization", auth_header)
            .header("Content-Type", "application/json")
            .json(&payload)
            .send()
            .await?;

        let data: Value = response.json().await?;

        // Return raw API response - hard to interpret without additional processing
        let mut freebusy_text = format!(
            "**Free/Busy Information**\n\n**Time Range**: {} to {}\n**Timezone**: {}\n\n",
            freebusy_args.time_min, freebusy_args.time_max, timezone
        );

        if let Some(calendars) = data.get("calendars").and_then(|v| v.as_object()) {
            for (calendar_id, calendar_data) in calendars {
                freebusy_text.push_str(&format!("### Calendar: {}\n", calendar_id));

                if let Some(busy_times) = calendar_data.get("busy").and_then(|v| v.as_array()) {
                    if !busy_times.is_empty() {
                        freebusy_text.push_str("**Busy periods**:\n");
                        for busy in busy_times {
                            let start = busy.get("start").and_then(|v| v.as_str()).unwrap_or("Unknown");
                            let end = busy.get("end").and_then(|v| v.as_str()).unwrap_or("Unknown");
                            freebusy_text.push_str(&format!("  - {} to {}\n", start, end));
                        }
                    } else {
                        freebusy_text.push_str("**No busy periods found**\n");
                    }
                }

                if let Some(errors) = calendar_data.get("errors").and_then(|v| v.as_array()) {
                    if !errors.is_empty() {
                        freebusy_text.push_str("**Errors**:\n");
                        for error in errors {
                            let reason = error.get("reason").and_then(|v| v.as_str()).unwrap_or("Unknown error");
                            freebusy_text.push_str(&format!("  - {}\n", reason));
                        }
                    }
                }

                freebusy_text.push('\n');
            }
        }

        Ok(vec![Content::Text(TextContent { text: freebusy_text })])
    }

    pub async fn run(&mut self) -> Result<()> {
        self.setup_tools().await?;
        
        self.server.set_tool_handler("list_calendars", |args| async move {
            self.handle_list_calendars(args).await
        });

        self.server.set_tool_handler("list_calendar_events", |args| async move {
            self.handle_list_calendar_events(args).await
        });

        self.server.set_tool_handler("retrieve_timezone", |args| async move {
            self.handle_retrieve_timezone(args).await
        });

        self.server.set_tool_handler("retrieve_calendar_free_busy_slots", |args| async move {
            self.handle_retrieve_free_busy_slots(args).await
        });

        println!("Google Calendar v1 MCP Server (Rust) running on stdio");
        self.server.run().await?;
        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let mut server = GoogleCalendarV1MCP::new()?;
    server.run().await?;
    Ok(())
} 