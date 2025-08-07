#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Setting up AI Usage Tracker...');

// Check if Python 3 is available
function checkPython() {
    const pythonCommands = ['python3', 'python'];
    
    for (const cmd of pythonCommands) {
        try {
            const result = execSync(`${cmd} --version`, { 
                stdio: 'pipe',
                encoding: 'utf8'
            });
            
            if (result.includes('Python 3.')) {
                console.log(`✅ Found ${result.trim()}`);
                return cmd;
            }
        } catch (e) {
            continue;
        }
    }
    
    console.error('❌ Python 3 not found.');
    console.error('💡 Please install Python 3.8 or higher from: https://www.python.org/downloads/');
    return null;
}

// Install Python dependencies
function installDependencies(pythonCmd) {
    const requirementsFile = path.join(__dirname, '..', 'requirements.txt');
    
    if (fs.existsSync(requirementsFile)) {
        console.log('📦 Installing Python dependencies...');
        
        try {
            execSync(`${pythonCmd} -m pip install -r "${requirementsFile}"`, {
                stdio: 'inherit'
            });
            console.log('✅ Python dependencies installed successfully');
        } catch (error) {
            console.warn('⚠️  Failed to install Python dependencies automatically.');
            console.warn(`💡 Please run manually: ${pythonCmd} -m pip install -r "${requirementsFile}"`);
        }
    }
}

// Main install process
function main() {
    const pythonCmd = checkPython();
    
    if (pythonCmd) {
        installDependencies(pythonCmd);
        
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
    } else {
        console.log('');
        console.log('⚠️  Installation incomplete. Please install Python 3 and run:');
        console.log('  npm install -g pricepertoken-ai-coding-tracker');
        process.exit(1);
    }
}

main(); 