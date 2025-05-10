const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const AMP_BASE_PATH = '/AMP/node-server/app';
const VENV_PATH = path.join(AMP_BASE_PATH, 'venv');

// Create and setup virtual environment
async function setupVirtualEnv() {
    return new Promise((resolve, reject) => {
        console.log('Setting up Python virtual environment...');
        
        // Create venv directory if it doesn't exist
        if (!fs.existsSync(VENV_PATH)) {
            const createVenv = spawn('python3', ['-m', 'venv', VENV_PATH], {
                shell: true
            });

            createVenv.stdout.on('data', (data) => {
                console.log(`Venv setup: ${data.toString().trim()}`);
            });

            createVenv.stderr.on('data', (data) => {
                console.error(`Venv setup error: ${data.toString().trim()}`);
            });

            createVenv.on('close', (code) => {
                if (code === 0) {
                    // Install requirements using venv pip
                    console.log('Installing Python dependencies in virtual environment...');
                    const pip = spawn(path.join(VENV_PATH, 'bin', 'pip'), ['install', '-r', 'requirements.txt'], {
                        cwd: path.join(AMP_BASE_PATH, 'Application/backend')
                    });

                    pip.stdout.on('data', (data) => {
                        console.log(`Pip install: ${data.toString().trim()}`);
                    });

                    pip.stderr.on('data', (data) => {
                        console.error(`Pip error: ${data.toString().trim()}`);
                    });

                    pip.on('close', (code) => {
                        if (code === 0) {
                            resolve();
                        } else {
                            reject(new Error(`pip install failed with code ${code}`));
                        }
                    });
                } else {
                    reject(new Error(`venv creation failed with code ${code}`));
                }
            });
        } else {
            resolve();
        }
    });
}

// Start the Python backend
async function startBackend() {
    try {
        await setupVirtualEnv();
        
        return new Promise((resolve, reject) => {
            console.log('Starting backend server...');
            const server = spawn(path.join(VENV_PATH, 'bin', 'python'), ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'], {
                cwd: path.join(AMP_BASE_PATH, 'Application/backend'),
                stdio: ['pipe', 'pipe', 'pipe']
            });

            server.stdout.on('data', (data) => {
                console.log(`Backend: ${data.toString().trim()}`);
            });

            server.stderr.on('data', (data) => {
                console.error(`Backend error: ${data.toString().trim()}`);
            });

            server.on('error', (error) => {
                console.error('Backend server error:', error);
                reject(error);
            });

            resolve(server);
        });
    } catch (error) {
        console.error('Error setting up Python environment:', error);
        throw error;
    }
}

// Start the frontend
async function startFrontend() {
    return new Promise((resolve, reject) => {
        console.log('Starting frontend server...');
        const frontend = spawn('npm', ['run', 'preview', '--', '--port', '7779', '--host'], {
            cwd: path.join(AMP_BASE_PATH, 'Application/frontend'),
            shell: true,
            env: { ...process.env, NODE_ENV: 'production' }
        });

        frontend.stdout.on('data', (data) => {
            console.log(`Frontend: ${data.toString().trim()}`);
        });

        frontend.stderr.on('data', (data) => {
            console.error(`Frontend error: ${data.toString().trim()}`);
        });

        frontend.on('error', (error) => {
            console.error('Frontend server error:', error);
            reject(error);
        });

        resolve(frontend);
    });
}

// Handle graceful shutdown
let backend;
let frontend;

function shutdown() {
    console.log('Shutting down services...');
    if (backend) backend.kill();
    if (frontend) frontend.kill();
    process.exit(0);
}

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

// Start services
console.log('Starting NBA Stats services...');
async function start() {
    try {
        backend = await startBackend();
        console.log('Backend started successfully');
        frontend = await startFrontend();
        console.log('Frontend started successfully');

        // Monitor processes for unexpected exits
        backend.on('close', (code) => {
            console.log(`Backend process exited with code ${code}`);
            if (code !== 0) {
                shutdown();
            }
        });

        frontend.on('close', (code) => {
            console.log(`Frontend process exited with code ${code}`);
            if (code !== 0) {
                shutdown();
            }
        });
    } catch (error) {
        console.error('Error starting services:', error);
        shutdown();
    }
}

start();