import keytar from "keytar";
import { config } from "./config.js";

export class AuthManager {
  async getToken(): Promise<string> {
    const token = await keytar.getPassword(config.keychainService, config.keychainAccount);
    if (!token) {
      throw new Error("API token not found. Please run setup-auth first.");
    }
    return token;
  }

  async setToken(token: string): Promise<void> {
    await keytar.setPassword(config.keychainService, config.keychainAccount, token);
  }

  async removeToken(): Promise<void> {
    await keytar.deletePassword(config.keychainService, config.keychainAccount);
  }

  async hasToken(): Promise<boolean> {
    const token = await keytar.getPassword(config.keychainService, config.keychainAccount);
    return !!token;
  }
} 