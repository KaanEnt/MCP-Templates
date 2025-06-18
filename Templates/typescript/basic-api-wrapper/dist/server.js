#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema, } from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import { config } from "./config.js";
import { AuthManager } from "./auth.js";
class BasicAPIWrapperMCP {
    server;
    baseUrl;
    authManager;
    constructor() {
        this.server = new Server({
            name: config.serverName, // Use from config
            version: config.serverVersion, // Use from config
        }, {
            capabilities: {
                tools: {},
            },
        });
        this.baseUrl = config.apiBaseUrl;
        this.authManager = new AuthManager();
        this.setupToolHandlers();
    }
    setupToolHandlers() {
        this.server.setRequestHandler(ListToolsRequestSchema, async () => {
            return {
                tools: [
                    {
                        name: "manage_task",
                        description: `Comprehensive task management tool that handles create, update, and read operations.
            
            Use this for common workflows like:
            - Creating new tasks with details
            - Updating task status or details
            - Getting task information
            
            Operation types:
            - 'create': Create new task (title required)
            - 'update': Update existing task (task_id required)
            - 'get': Get task details (task_id required)
            - 'list': List tasks (optional: status filter)`,
                        inputSchema: {
                            type: "object",
                            properties: {
                                operation: {
                                    type: "string",
                                    enum: ["create", "update", "get", "list"],
                                    description: "The operation to perform",
                                },
                                task_id: {
                                    type: "string",
                                    description: "Task ID (required for update/get operations)",
                                },
                                title: {
                                    type: "string",
                                    description: "Task title (required for create operation)",
                                },
                                description: {
                                    type: "string",
                                    description: "Task description (optional)",
                                },
                                status: {
                                    type: "string",
                                    enum: ["todo", "in_progress", "done"],
                                    description: "Task status",
                                },
                                priority: {
                                    type: "string",
                                    enum: ["low", "medium", "high"],
                                    description: "Task priority",
                                },
                            },
                            required: ["operation"],
                        },
                    },
                    {
                        name: "get_team_overview",
                        description: `Get comprehensive team information including members, projects, and recent activity.
            
            This tool bundles multiple read-only operations:
            - Team member list with roles
            - Active projects summary
            - Recent team activity
            - Team performance metrics
            
            Perfect for questions like "What's my team working on?" or "Who's available for new tasks?"`,
                        inputSchema: {
                            type: "object",
                            properties: {
                                team_id: {
                                    type: "string",
                                    description: "Team identifier (optional, defaults to user's primary team)",
                                },
                                include_metrics: {
                                    type: "boolean",
                                    description: "Include performance metrics (default: true)",
                                },
                            },
                        },
                    },
                    {
                        name: "get_weather",
                        description: "Get current weather for a location by city name or coordinates.",
                        inputSchema: {
                            type: "object",
                            properties: {
                                city: { type: "string", description: "City name (e.g., 'London')" },
                                lat: { type: "number", description: "Latitude (optional)" },
                                lon: { type: "number", description: "Longitude (optional)" },
                            },
                            anyOf: [
                                { required: ["city"] },
                                { required: ["lat", "lon"] }
                            ]
                        }
                    }
                ],
            };
        });
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;
            try {
                switch (name) {
                    case "manage_task":
                        return await this.handleTaskManagement(args);
                    case "get_team_overview":
                        return await this.handleTeamOverview(args);
                    case "get_weather":
                        return await this.handleWeather(args);
                    default:
                        throw new Error(`Unknown tool: ${name}`);
                }
            }
            catch (error) {
                const errorMessage = error instanceof Error ? error.message : String(error);
                return {
                    content: [
                        {
                            type: "text",
                            text: `❌ Error: ${errorMessage}`,
                        },
                    ],
                };
            }
        });
    }
    async handleTaskManagement(args) {
        const { operation } = args;
        try {
            const headers = {
                Authorization: `Bearer ${await this.authManager.getToken()}`,
                "Content-Type": "application/json",
            };
            switch (operation) {
                case "create": {
                    if (!args.title) {
                        throw new Error("title is required for create operations");
                    }
                    const payload = {
                        title: args.title,
                        description: args.description || "",
                        status: args.status || "todo",
                        priority: args.priority || "medium",
                    };
                    const response = await axios.post(`${this.baseUrl}/tasks`, payload, { headers });
                    const task = response.data;
                    return {
                        content: [
                            {
                                type: "text",
                                text: `✅ Task created successfully!\n\n**Task ID**: ${task.id}\n**Title**: ${task.title}\n**Status**: ${task.status}\n**Priority**: ${task.priority}`,
                            },
                        ],
                    };
                }
                case "update": {
                    if (!args.task_id) {
                        throw new Error("task_id is required for update operations");
                    }
                    const payload = {};
                    if (args.title)
                        payload.title = args.title;
                    if (args.description)
                        payload.description = args.description;
                    if (args.status)
                        payload.status = args.status;
                    if (args.priority)
                        payload.priority = args.priority;
                    const response = await axios.patch(`${this.baseUrl}/tasks/${args.task_id}`, payload, { headers });
                    const task = response.data;
                    return {
                        content: [
                            {
                                type: "text",
                                text: `✅ Task updated successfully!\n\n**Task ID**: ${task.id}\n**Title**: ${task.title}\n**Status**: ${task.status}\n**Priority**: ${task.priority}`,
                            },
                        ],
                    };
                }
                case "get": {
                    if (!args.task_id) {
                        throw new Error("task_id is required for get operations");
                    }
                    const response = await axios.get(`${this.baseUrl}/tasks/${args.task_id}`, { headers });
                    const task = response.data;
                    return {
                        content: [
                            {
                                type: "text",
                                text: `**Task Details**\n\n**ID**: ${task.id}\n**Title**: ${task.title}\n**Description**: ${task.description || "No description"}\n**Status**: ${task.status}\n**Priority**: ${task.priority}\n**Created**: ${task.created_at || "Unknown"}`,
                            },
                        ],
                    };
                }
                case "list": {
                    const params = {};
                    if (args.status)
                        params.status = args.status;
                    const response = await axios.get(`${this.baseUrl}/tasks`, { headers, params });
                    const tasks = response.data;
                    if (!tasks || tasks.length === 0) {
                        return {
                            content: [
                                {
                                    type: "text",
                                    text: "No tasks found.",
                                },
                            ],
                        };
                    }
                    let taskList = "**Task List**\n\n";
                    tasks.slice(0, 10).forEach((task) => {
                        taskList += `• **${task.title}** (ID: ${task.id}) - ${task.status} - ${task.priority} priority\n`;
                    });
                    if (tasks.length > 10) {
                        taskList += `\n*Showing first 10 of ${tasks.length} tasks*`;
                    }
                    return {
                        content: [
                            {
                                type: "text",
                                text: taskList,
                            },
                        ],
                    };
                }
                default:
                    throw new Error(`Unknown operation: ${operation}`);
            }
        }
        catch (error) {
            if (axios.isAxiosError(error)) {
                const axiosError = error;
                let errorMessage = `❌ API Error: ${axiosError.response?.status}`;
                if (axiosError.response?.data) {
                    errorMessage += ` - ${typeof axiosError.response.data === 'object' ? JSON.stringify(axiosError.response.data) : axiosError.response.data}`;
                }
                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
            throw error; // Re-throw if not an AxiosError, to be caught by the outer handler
        }
    }
    async handleTeamOverview(args) {
        try {
            const headers = {
                Authorization: `Bearer ${await this.authManager.getToken()}`,
                "Content-Type": "application/json",
            };
            const teamId = args.team_id || "default";
            const includeMetrics = args.include_metrics !== false; // Defaults to true if undefined
            // Parallel API calls for efficiency
            const [teamResponse, membersResponse, projectsResponse] = await Promise.all([
                axios.get(`${this.baseUrl}/teams/${teamId}`, { headers }),
                axios.get(`${this.baseUrl}/teams/${teamId}/members`, { headers }),
                axios.get(`${this.baseUrl}/teams/${teamId}/projects`, { headers }),
            ]);
            const team = teamResponse.data;
            const members = membersResponse.data;
            const projects = projectsResponse.data;
            let overview = `# Team Overview: ${team.name}\n\n`;
            // Team members
            overview += "## Team Members\n";
            members.forEach((member) => {
                const status = member.available ? "🟢" : "🔴";
                overview += `• ${status} **${member.name}** - ${member.role}\n`;
            });
            // Active projects
            overview += "\n## Active Projects\n";
            const activeProjects = projects.filter((p) => p.status === "active");
            if (activeProjects.length > 0) {
                activeProjects.forEach((project) => {
                    overview += `• **${project.name}** - ${project.progress || "N/A"}% complete\n`;
                });
            }
            else {
                overview += "No active projects\n";
            }
            // Metrics if requested
            if (includeMetrics) {
                try {
                    const metricsResponse = await axios.get(`${this.baseUrl}/teams/${teamId}/metrics`, { headers });
                    const metrics = metricsResponse.data;
                    overview += "\n## Team Metrics\n";
                    overview += `• Tasks completed this week: ${metrics.tasks_completed || "N/A"}\n`;
                    overview += `• Average completion time: ${metrics.avg_completion_time || "N/A"}\n`;
                    overview += `• Team velocity: ${metrics.velocity || "N/A"}\n`;
                }
                catch (error) {
                    // Metrics endpoint might not be available or might error, log and continue
                    console.warn("Could not fetch team metrics:", error);
                    overview += "\n## Team Metrics\n_Metrics data unavailable._\n";
                }
            }
            overview += `\n*Retrieved at: ${new Date().toISOString().slice(0, 19).replace('T', ' ')} UTC*`;
            return {
                content: [
                    {
                        type: "text",
                        text: overview,
                    },
                ],
            };
        }
        catch (error) {
            if (axios.isAxiosError(error)) {
                const axiosError = error;
                let errorMessage = `❌ API Error: ${axiosError.response?.status}`;
                if (axiosError.response?.data) {
                    errorMessage += ` - ${typeof axiosError.response.data === 'object' ? JSON.stringify(axiosError.response.data) : axiosError.response.data}`;
                }
                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
            throw error; // Re-throw if not an AxiosError
        }
    }
    async handleWeather(args) {
        const { city, lat, lon } = args;
        if (!config.weatherApiKey) {
            throw new Error("Weather API key is not configured.");
        }
        let url = `${config.weatherApiBaseUrl}/weather?appid=${config.weatherApiKey}&units=metric`; // Added units=metric for Celsius
        if (city) {
            url += `&q=${encodeURIComponent(city)}`;
        }
        else if (lat !== undefined && lon !== undefined) {
            url += `&lat=${lat}&lon=${lon}`;
        }
        else {
            // This case should ideally be prevented by the inputSchema's anyOf
            throw new Error("Either city or latitude and longitude must be provided for weather lookup.");
        }
        try {
            const response = await axios.get(url);
            const weatherData = response.data;
            // Construct a more readable weather summary
            const locationName = weatherData.name || (city || `${lat},${lon}`);
            const description = weatherData.weather && weatherData.weather[0] ? weatherData.weather[0].description : "N/A";
            const temperature = weatherData.main ? `${weatherData.main.temp}°C` : "N/A";
            const feelsLike = weatherData.main ? `${weatherData.main.feels_like}°C` : "N/A";
            const humidity = weatherData.main ? `${weatherData.main.humidity}%` : "N/A";
            const windSpeed = weatherData.wind ? `${weatherData.wind.speed} m/s` : "N/A";
            const weatherText = `🌦️ **Weather for ${locationName}**
      - **Condition**: ${description}
      - **Temperature**: ${temperature} (Feels like: ${feelsLike})
      - **Humidity**: ${humidity}
      - **Wind**: ${windSpeed}
      
      *Raw Data:*
      \`\`\`json
      ${JSON.stringify(weatherData, null, 2)}
      \`\`\``;
            // Using markdown for better readability of raw data.
            return {
                content: [
                    { type: "text", text: weatherText }
                ]
            };
        }
        catch (error) {
            if (axios.isAxiosError(error)) {
                const axiosError = error;
                let errorMessage = `❌ Weather API Error: ${axiosError.response?.status}`;
                if (axiosError.response?.data) {
                    // OpenWeatherMap often returns JSON error messages
                    const errorData = axiosError.response.data;
                    errorMessage += ` - ${errorData.message || (typeof axiosError.response.data === 'object' ? JSON.stringify(axiosError.response.data) : axiosError.response.data)}`;
                }
                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
            // For non-Axios errors, or if we want the main handler to catch it
            throw error;
        }
    }
    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error(`Basic API Wrapper MCP Server (${config.serverName} v${config.serverVersion}) running on stdio`);
    }
}
const server = new BasicAPIWrapperMCP();
server.run().catch(console.error);
//# sourceMappingURL=server.js.map