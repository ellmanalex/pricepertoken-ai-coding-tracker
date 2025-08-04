#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Get the directory where this package is installed
const packageDir = path.dirname(__dirname);
const pythonScript = path.join(packageDir, 'cli_tool', 'cli.py');

// Check if Python script exists
if (!fs.existsSync(pythonScript)) {
    console.error('❌ Python CLI script not found. Please reinstall the package.');
    process.exit(1);
}

// Function to find Python executable
function findPython() {
    const pythonCommands = ['python3', 'python'];
    
    for (const cmd of pythonCommands) {
        try {
            const result = require('child_process').execSync(`${cmd} --version`, { 
                stdio: 'pipe',
                encoding: 'utf8'
            });
            
            if (result.includes('Python 3.')) {
                return cmd;
            }
        } catch (e) {
            // Command not found, try next
            continue;
        }
    }
    
    console.error('❌ Python 3 not found. Please install Python 3.8 or higher.');
    console.error('💡 Download from: https://www.python.org/downloads/');
    process.exit(1);
}

// Check Python dependencies
function checkDependencies() {
    const python = findPython();
    const requirementsFile = path.join(packageDir, 'requirements.txt');
    
    if (fs.existsSync(requirementsFile)) {
        try {
            // Try to import required modules
            const checkScript = `
import sys
try:
    import httpx
    import jwt
    import pydantic
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("💡 Run: pip install -r ${requirementsFile}")
    sys.exit(1)
`;
            
            require('child_process').execSync(`${python} -c "${checkScript}"`, {
                stdio: 'pipe'
            });
        } catch (e) {
            console.error('❌ Python dependencies not installed.');
            console.error(`💡 Run: pip install -r ${requirementsFile}`);
            process.exit(1);
        }
    }
}

// Main execution
function main() {
    // Check dependencies on first run
    checkDependencies();
    
    const python = findPython();
    
    // Pass all arguments to the Python script
    const args = process.argv.slice(2);
    
    // Spawn Python process
    const pythonProcess = spawn(python, [pythonScript, ...args], {
        stdio: 'inherit',
        cwd: process.cwd()
    });
    
    // Handle process exit
    pythonProcess.on('close', (code) => {
        process.exit(code);
    });
    
    // Handle errors
    pythonProcess.on('error', (err) => {
        console.error('❌ Failed to start Python process:', err.message);
        process.exit(1);
    });
    
    // Handle signals
    process.on('SIGINT', () => {
        pythonProcess.kill('SIGINT');
    });
    
    process.on('SIGTERM', () => {
        pythonProcess.kill('SIGTERM');
    });
}

main(); 