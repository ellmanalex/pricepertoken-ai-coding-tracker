#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

console.log('🚀 Setting up AI Usage Tracker...');

// Check if binary exists
function checkBinary() {
    const packageDir = path.dirname(__dirname);
    const platform = os.platform();
    
    let binaryName = 'cli';
    if (platform === 'win32') {
        binaryName += '.exe';
    }
    
    const binaryPath = path.join(packageDir, 'dist', binaryName);
    
    if (fs.existsSync(binaryPath)) {
        console.log(`✅ Found binary: ${binaryName}`);
        return binaryPath;
    } else {
        console.error(`❌ Binary not found at: ${binaryPath}`);
        console.error('💡 This package should include a pre-built binary.');
        console.error('   Please reinstall or contact support.');
        return null;
    }
}

// Set executable permissions on Unix systems
function setExecutablePermissions(binaryPath) {
    if (os.platform() !== 'win32') {
        try {
            const { execSync } = require('child_process');
            execSync(`chmod +x "${binaryPath}"`, { stdio: 'pipe' });
            console.log('✅ Set executable permissions');
        } catch (e) {
            console.warn('⚠️  Could not set executable permissions (this is usually okay)');
        }
    }
}

// Test the binary
function testBinary(binaryPath) {
    console.log('🧪 Testing binary...');
    
    try {
        const { execSync } = require('child_process');
        execSync(`"${binaryPath}" --help`, { 
            stdio: 'pipe',
            timeout: 10000
        });
        console.log('✅ Binary test successful');
        return true;
    } catch (e) {
        console.error('❌ Binary test failed');
        console.error('💡 The binary may be corrupted or incompatible with your system.');
        return false;
    }
}

// Main install process
function main() {
    const binaryPath = checkBinary();
    
    if (binaryPath) {
        setExecutablePermissions(binaryPath);
        
        const binaryWorks = testBinary(binaryPath);
        
        if (binaryWorks) {
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
            console.log('⚠️  Installation incomplete due to binary test failure.');
            process.exit(1);
        }
    } else {
        console.log('');
        console.log('⚠️  Installation incomplete. Please reinstall:');
        console.log('  npm install -g pricepertoken-ai-coding-tracker');
        process.exit(1);
    }
}

main(); 