#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

console.log('🚀 Setting up AI Usage Tracker...');

// Check if binary exists and set permissions
function setupBinary() {
    const packageDir = path.dirname(__dirname);
    const platform = os.platform();
    
    let binaryName = 'cli';
    if (platform === 'win32') {
        binaryName += '.exe';
    }
    
    const binaryPath = path.join(packageDir, 'dist', binaryName);
    
    if (fs.existsSync(binaryPath)) {
        console.log(`✅ Found binary: ${binaryName}`);
        
        // Set executable permissions on Unix systems
        if (os.platform() !== 'win32') {
            try {
                const { execSync } = require('child_process');
                execSync(`chmod +x "${binaryPath}"`, { stdio: 'pipe' });
                console.log('✅ Set executable permissions');
            } catch (e) {
                console.log('⚠️  Could not set executable permissions (may still work)');
            }
        }
        
        return true;
    } else {
        console.error(`❌ Binary not found at: ${binaryPath}`);
        return false;
    }
}

// Main install process
function main() {
    const binaryFound = setupBinary();
    
    if (binaryFound) {
        console.log('');
        console.log('🎉 AI Usage Tracker installed successfully!');
        console.log('');
        console.log('📖 Getting Started:');
        console.log('  1. Try local mode first: pricepertoken-ai-coding-tracker --local');
        console.log('  2. Get your API token from: https://pricepertoken.com/coding-tracker/');
        console.log('  3. Configure token: pricepertoken-ai-coding-tracker --configure YOUR_TOKEN');
        console.log('  4. Send to dashboard: pricepertoken-ai-coding-tracker --live');
        console.log('');
        console.log('📚 More commands:');
        console.log('  pricepertoken-ai-coding-tracker --help     # Show all options');
        console.log('');
        console.log('💡 No Python required - everything is bundled in the binary!');
        console.log('');
    } else {
        console.log('');
        console.log('⚠️  Binary not found but installation completed.');
        console.log('💡 Please try reinstalling: npm install -g pricepertoken-ai-coding-tracker');
        console.log('');
    }
}

main(); 