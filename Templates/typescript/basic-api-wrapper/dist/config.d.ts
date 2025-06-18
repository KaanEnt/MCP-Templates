export interface Config {
    apiBaseUrl: string;
    apiTimeout: number;
    serverName: string;
    serverVersion: string;
    keychainService: string;
    keychainAccount: string;
    maxRequestsPerMinute: number;
    weatherApiBaseUrl: string;
    weatherApiKey: string;
}
export declare const config: Config;
export declare function validateConfig(): void;
