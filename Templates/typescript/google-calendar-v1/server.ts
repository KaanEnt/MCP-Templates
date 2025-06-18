#!/usr/bin/env node

/**
 * Google Calendar MCP v1 - Thin API Wrapper (TypeScript)
 * This represents the initial version mentioned in Block's playbook that served 
 * as a thin wrapper around the external API before the v2 analytics improvements.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios, { AxiosError } from "axios";
import { AuthManager } from "./auth.js";

interface CalendarListArgs {
  // No arguments needed
}

interface EventsListArgs {
  calendar_id?: string;
  time_max?: string;
  time_min?: string;
  verbose?: boolean;
}

interface TimezoneArgs {
  calendar_id?: string;
}

interface FreeBusyArgs {
  time_min: string;
  time_max: string;
  timezone?: string;
  calendar_ids?: string[];
}

class GoogleCalendarV1MCP {
  private server: Server;
  private baseUrl: string;
  private authManager: AuthManager;

  constructor() {
    this.server = new Server(
      {
        name: "google-calendar-v1-ts",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.baseUrl = "https://www.googleapis.com/calendar/v3";
    this.authManager = new AuthManager();
    this.setupToolHandlers();
  }

  private setupToolHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "list_calendars",
            description: "Lists all user calendars.",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
          {
            name: "list_calendar_events",
            description: "Get all events for a specified time period for a given calendar.",
            inputSchema: {
              type: "object",
              properties: {
                calendar_id: {
                  type: "string",
                  description: "Calendar ID (default: primary)",
                  default: "primary",
                },
                time_max: {
                  type: "string",
                  description: "Upper bound (exclusive) for an event's start time (RFC3339 timestamp)",
                },
                time_min: {
                  type: "string",
                  description: "Lower bound (exclusive) for an event's end time (RFC3339 timestamp)",
                },
                verbose: {
                  type: "boolean",
                  description: "Include detailed event information",
                  default: false,
                },
              },
            },
          },
          {
            name: "retrieve_timezone",
            description: "Retrieves timezone for a given calendar.",
            inputSchema: {
              type: "object",
              properties: {
                calendar_id: {
                  type: "string",
                  description: "Calendar ID (default: primary)",
                  default: "primary",
                },
              },
            },
          },
          {
            name: "retrieve_calendar_free_busy_slots",
            description: "Retrieves free and busy slots from the calendars of the calendar_ids list.",
            inputSchema: {
              type: "object",
              properties: {
                time_min: {
                  type: "string",
                  description: "Lower bound for the query (RFC3339 timestamp)",
                },
                time_max: {
                  type: "string",
                  description: "Upper bound for the query (RFC3339 timestamp)",
                },
                timezone: {
                  type: "string",
                  description: "Timezone to use for the query",
                  default: "UTC",
                },
                calendar_ids: {
                  type: "array",
                  items: { type: "string" },
                  description: "List of calendar IDs to query",
                  default: ["primary"],
                },
              },
              required: ["time_min", "time_max"],
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "list_calendars":
            return await this.listCalendars(args as CalendarListArgs);
          case "list_calendar_events":
            return await this.listCalendarEvents(args as EventsListArgs);
          case "retrieve_timezone":
            return await this.retrieveTimezone(args as TimezoneArgs);
          case "retrieve_calendar_free_busy_slots":
            return await this.retrieveFreeBusySlots(args as FreeBusyArgs);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
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

  private async listCalendars(args: CalendarListArgs) {
    try {
      const headers = {
        Authorization: `Bearer ${await this.authManager.getToken()}`,
      };

      const response = await axios.get(`${this.baseUrl}/users/me/calendarList`, { headers });
      const data = response.data;

      // Return raw API response as text
      let calendarsText = "**Calendars List**\n\n";
      const calendars = data.items || [];
      
      calendars.forEach((calendar: any) => {
        calendarsText += `• **${calendar.summary || "Unknown"}** (ID: ${calendar.id || "Unknown"})\n`;
        calendarsText += `  - Primary: ${calendar.primary || false}\n`;
        calendarsText += `  - Access Role: ${calendar.accessRole || "Unknown"}\n\n`;
      });

      return {
        content: [
          {
            type: "text",
            text: calendarsText,
          },
        ],
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError;
        return {
          content: [
            {
              type: "text",
              text: `❌ API Error: ${axiosError.response?.status} - ${axiosError.response?.data}`,
            },
          ],
        };
      }
      throw error;
    }
  }

  private async listCalendarEvents(args: EventsListArgs) {
    try {
      const calendarId = args.calendar_id || "primary";
      const timeMax = args.time_max;
      const timeMin = args.time_min;
      const verbose = args.verbose || false;

      const headers = {
        Authorization: `Bearer ${await this.authManager.getToken()}`,
      };

      const params: Record<string, string> = {};
      if (timeMax) params.timeMax = timeMax;
      if (timeMin) params.timeMin = timeMin;

      const response = await axios.get(`${this.baseUrl}/calendars/${calendarId}/events`, {
        headers,
        params,
      });
      const data = response.data;

      // Return verbose API response - this gets unwieldy quickly
      const events = data.items || [];
      if (events.length === 0) {
        return {
          content: [
            {
              type: "text",
              text: "No events found for the specified time period.",
            },
          ],
        };
      }

      let eventsText = `**Calendar Events** (${events.length} found)\n\n`;

      events.forEach((event: any) => {
        eventsText += `### ${event.summary || "No title"}\n`;

        // Start time
        const start = event.start || {};
        const startTime = start.dateTime || start.date || "Unknown";
        eventsText += `**Start**: ${startTime}\n`;

        // End time
        const end = event.end || {};
        const endTime = end.dateTime || end.date || "Unknown";
        eventsText += `**End**: ${endTime}\n`;

        if (verbose) {
          // Include all the verbose details that make this painful to use
          eventsText += `**ID**: ${event.id || "Unknown"}\n`;
          eventsText += `**Status**: ${event.status || "Unknown"}\n`;
          eventsText += `**Creator**: ${event.creator?.email || "Unknown"}\n`;
          eventsText += `**Organizer**: ${event.organizer?.email || "Unknown"}\n`;

          const attendees = event.attendees || [];
          if (attendees.length > 0) {
            eventsText += `**Attendees** (${attendees.length}):\n`;
            attendees.forEach((attendee: any) => {
              eventsText += `  - ${attendee.email || "Unknown"} (${attendee.responseStatus || "Unknown"})\n`;
            });
          }

          if (event.description) {
            eventsText += `**Description**: ${event.description}\n`;
          }

          if (event.location) {
            eventsText += `**Location**: ${event.location}\n`;
          }
        }

        eventsText += "\n---\n\n";
      });

      // This response can become extremely long and unwieldy
      if (eventsText.length > 8000) {
        eventsText = eventsText.substring(0, 8000) + "\n\n*[Response truncated - too much data]*";
      }

      return {
        content: [
          {
            type: "text",
            text: eventsText,
          },
        ],
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError;
        return {
          content: [
            {
              type: "text",
              text: `❌ API Error: ${axiosError.response?.status} - ${axiosError.response?.data}`,
            },
          ],
        };
      }
      throw error;
    }
  }

  private async retrieveTimezone(args: TimezoneArgs) {
    try {
      const calendarId = args.calendar_id || "primary";
      const headers = {
        Authorization: `Bearer ${await this.authManager.getToken()}`,
      };

      const response = await axios.get(`${this.baseUrl}/calendars/${calendarId}`, { headers });
      const data = response.data;

      let timezoneText = "**Calendar Timezone Information**\n\n";
      timezoneText += `**Calendar**: ${data.summary || "Unknown"}\n`;
      timezoneText += `**Timezone**: ${data.timeZone || "Unknown"}\n`;
      timezoneText += `**Location**: ${data.location || "Not specified"}\n`;

      return {
        content: [
          {
            type: "text",
            text: timezoneText,
          },
        ],
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError;
        return {
          content: [
            {
              type: "text",
              text: `❌ API Error: ${axiosError.response?.status} - ${axiosError.response?.data}`,
            },
          ],
        };
      }
      throw error;
    }
  }

  private async retrieveFreeBusySlots(args: FreeBusyArgs) {
    try {
      const { time_min, time_max } = args;
      const timezone = args.timezone || "UTC";
      const calendarIds = args.calendar_ids || ["primary"];

      const headers = {
        Authorization: `Bearer ${await this.authManager.getToken()}`,
        "Content-Type": "application/json",
      };

      const payload = {
        timeMin: time_min,
        timeMax: time_max,
        timeZone: timezone,
        items: calendarIds.map((id) => ({ id })),
      };

      const response = await axios.post(`${this.baseUrl}/freeBusy`, payload, { headers });
      const data = response.data;

      // Return raw API response - hard to interpret without additional processing
      let freebusyText = "**Free/Busy Information**\n\n";
      freebusyText += `**Time Range**: ${time_min} to ${time_max}\n`;
      freebusyText += `**Timezone**: ${timezone}\n\n`;

      const calendars = data.calendars || {};
      Object.entries(calendars).forEach(([calendarId, calendarData]: [string, any]) => {
        freebusyText += `### Calendar: ${calendarId}\n`;

        const busyTimes = calendarData.busy || [];
        if (busyTimes.length > 0) {
          freebusyText += "**Busy periods**:\n";
          busyTimes.forEach((busy: any) => {
            freebusyText += `  - ${busy.start} to ${busy.end}\n`;
          });
        } else {
          freebusyText += "**No busy periods found**\n";
        }

        const errors = calendarData.errors || [];
        if (errors.length > 0) {
          freebusyText += "**Errors**:\n";
          errors.forEach((error: any) => {
            freebusyText += `  - ${error.reason || "Unknown error"}\n`;
          });
        }

        freebusyText += "\n";
      });

      return {
        content: [
          {
            type: "text",
            text: freebusyText,
          },
        ],
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError;
        return {
          content: [
            {
              type: "text",
              text: `❌ API Error: ${axiosError.response?.status} - ${axiosError.response?.data}`,
            },
          ],
        };
      }
      throw error;
    }
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Google Calendar v1 MCP Server (TypeScript) running on stdio");
  }
}

const server = new GoogleCalendarV1MCP();
server.run().catch(console.error); 