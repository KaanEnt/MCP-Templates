import keytar from "keytar";
import { config } from "./config.js";
export class AuthManager {
    async getToken() {
        const token = await keytar.getPassword(config.keychainService, config.keychainAccount);
        if (!token) {
            throw new Error("API token not found. Please run setup-auth first.");
        }
        return token;
    }
    async setToken(token) {
        await keytar.setPassword(config.keychainService, config.keychainAccount, token);
    }
    async removeToken() {
        await keytar.deletePassword(config.keychainService, config.keychainAccount);
    }
    async hasToken() {
        const token = await keytar.getPassword(config.keychainService, config.keychainAccount);
        return !!token;
    }
}
//# sourceMappingURL=auth.js.map