import dotenv from "dotenv";
dotenv.config();
export const config = {
    apiBaseUrl: process.env.API_BASE_URL || "https://api.example.com",
    apiTimeout: parseInt(process.env.API_TIMEOUT || "30000"),
    serverName: "basic-api-wrapper-ts",
    serverVersion: "1.0.0",
    keychainService: "basic-api-wrapper-ts",
    keychainAccount: "api_token",
    maxRequestsPerMinute: parseInt(process.env.MAX_REQUESTS_PER_MINUTE || "60"),
    weatherApiBaseUrl: process.env.WEATHER_API_BASE_URL || "https://api.openweathermap.org/data/2.5", // Added
    weatherApiKey: process.env.WEATHER_API_KEY || "d1059b08794db7be77dd0b3aedb225af", // Added
};
export function validateConfig() {
    const requiredVars = ["apiBaseUrl"]; // weatherApiKey is not strictly required for the server to run, only for the weather tool
    const missing = requiredVars.filter(key => !config[key]);
    if (missing.length > 0) {
        throw new Error(`Missing required configuration: ${missing.join(", ")}`);
    }
    // Optional: Add a warning if weatherApiKey is missing, if desired for operational clarity
    if (!config.weatherApiKey) {
        console.warn("Warning: WEATHER_API_KEY is not set. The get_weather tool will not function.");
    }
}
//# sourceMappingURL=config.js.map