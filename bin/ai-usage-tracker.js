#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Get the directory where this package is installed
const packageDir = path.dirname(__dirname);

// Determine the correct binary path based on platform
function getBinaryPath() {
    const platform = os.platform();
    const arch = os.arch();
    
    // PyInstaller creates different binary names
    let binaryName = 'cli';
    if (platform === 'win32') {
        binaryName += '.exe';
    }
    
    // Look for the binary in the dist directory (PyInstaller output)
    const binaryPath = path.join(packageDir, 'dist', binaryName);
    
    return binaryPath;
}

// Check if binary exists
function checkBinary() {
    const binaryPath = getBinaryPath();
    
    if (!fs.existsSync(binaryPath)) {
        console.error('❌ Binary not found. Please build the package first.');
        console.error(`💡 Expected binary at: ${binaryPath}`);
        console.error('💡 Run: npm run build');
        process.exit(1);
    }
    
    return binaryPath;
}

// Main execution
function main() {
    const binaryPath = checkBinary();
    
    // Pass all arguments to the binary
    const args = process.argv.slice(2);
    
    // Spawn binary process
    const binaryProcess = spawn(binaryPath, args, {
        stdio: 'inherit',
        cwd: process.cwd()
    });
    
    // Handle process exit
    binaryProcess.on('close', (code) => {
        process.exit(code);
    });
    
    // Handle errors
    binaryProcess.on('error', (err) => {
        console.error('❌ Failed to start binary:', err.message);
        process.exit(1);
    });
    
    // Handle signals
    process.on('SIGINT', () => {
        binaryProcess.kill('SIGINT');
    });
    
    process.on('SIGTERM', () => {
        binaryProcess.kill('SIGTERM');
    });
}

main(); 