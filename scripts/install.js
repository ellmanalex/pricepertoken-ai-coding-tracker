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
            // Try pip first, then pip3
            const pipCommands = [`${pythonCmd} -m pip`, 'pip3', 'pip'];
            
            for (const pipCmd of pipCommands) {
                try {
                    execSync(`${pipCmd} install -r "${requirementsFile}"`, {
                        stdio: 'inherit'
                    });
                    console.log('✅ Python dependencies installed successfully');
                    return true;
                } catch (e) {
                    continue;
                }
            }
            
            throw new Error('No pip command worked');
            
        } catch (error) {
            console.warn('⚠️  Failed to install Python dependencies automatically.');
            console.warn(`💡 Please run manually: ${pythonCmd} -m pip install -r "${requirementsFile}"`);
            console.warn('   Or install individually:');
            console.warn('   pip install httpx==0.25.2 PyJWT==2.8.0');
            return false;
        }
    }
    
    return true;
}

// Verify dependencies are installed
function verifyDependencies(pythonCmd) {
    console.log('🔍 Verifying dependencies...');
    
    const checkScript = `
import sys
try:
    import httpx
    import jwt
    print("✅ All dependencies found")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("💡 Run: pip install httpx==0.25.2 PyJWT==2.8.0")
    sys.exit(1)
`;
    
    try {
        execSync(`${pythonCmd} -c "${checkScript}"`, {
            stdio: 'pipe'
        });
        return true;
    } catch (e) {
        console.error('❌ Dependencies verification failed.');
        console.error('💡 Please install the required Python packages:');
        console.error('   pip install httpx==0.25.2 PyJWT==2.8.0');
        return false;
    }
}

// Main install process
function main() {
    const pythonCmd = checkPython();
    
    if (pythonCmd) {
        const depsInstalled = installDependencies(pythonCmd);
        
        if (depsInstalled) {
            const depsVerified = verifyDependencies(pythonCmd);
            
            if (depsVerified) {
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
                console.log('⚠️  Installation incomplete due to missing dependencies.');
                process.exit(1);
            }
        } else {
            console.log('');
            console.log('⚠️  Installation incomplete due to dependency installation failure.');
            process.exit(1);
        }
    } else {
        console.log('');
        console.log('⚠️  Installation incomplete. Please install Python 3 and run:');
        console.log('  npm install -g pricepertoken-ai-coding-tracker');
        process.exit(1);
    }
}

main(); 