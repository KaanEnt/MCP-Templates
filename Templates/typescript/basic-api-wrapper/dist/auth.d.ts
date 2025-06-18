export declare class AuthManager {
    getToken(): Promise<string>;
    setToken(token: string): Promise<void>;
    removeToken(): Promise<void>;
    hasToken(): Promise<boolean>;
}
