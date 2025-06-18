#!/usr/bin/env node

import * as readline from 'readline';
import { AuthManager } from './auth.js';
import { config } from './config.js';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(prompt: string): Promise<string> {
  return new Promise((resolve) => {
    rl.question(prompt, resolve);
  });
}

async function setupAuth(): Promise<void> {
  console.log('🔐 MCP Server Authentication Setup');
  console.log('=====================================\n');
  
  const authManager = new AuthManager();
  
  try {
    console.log('This will help you set up secure authentication for your MCP server.');
    console.log('Your API token will be stored securely in your system keychain.\n');
    
    // Get API token
    const apiToken = await question('Enter your API token: ');
    if (!apiToken.trim()) {
      console.error('❌ API token is required');
      process.exit(1);
    }
    
    // Store token
    await authManager.setToken(apiToken.trim());
    
    console.log('\n✅ Authentication setup complete!');
    console.log('Your API token has been stored securely.');
    console.log('\nNext steps:');
    console.log('1. npm run build');
    console.log('2. npm start');
    
  } catch (error) {
    console.error('❌ Setup failed:', error);
    process.exit(1);
  } finally {
    rl.close();
  }
}

// Test token if --test flag is passed
async function testToken(): Promise<void> {
  console.log('🧪 Testing stored token...\n');
  
  const authManager = new AuthManager();
  
  try {
    const hasToken = await authManager.hasToken();
    if (hasToken) {
      const token = await authManager.getToken();
      console.log('✅ Token found:');
      console.log(`   API Token: ${token.substring(0, 8)}...`);
      console.log(`   Base URL: ${config.apiBaseUrl}`);
    } else {
      throw new Error('No token found');
    }
  } catch (error) {
    console.error('❌ No token found. Run setup first:', error);
    process.exit(1);
  }
}

// Main execution
async function main(): Promise<void> {
  const args = process.argv.slice(2);
  
  if (args.includes('--test')) {
    await testToken();
  } else {
    await setupAuth();
  }
}

main().catch(console.error); 