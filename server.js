const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const AMP_BASE_PATH = '/AMP/node-server/app';
const VENV_PATH = path.join(AMP_BASE_PATH, 'venv');
const PYTHON_PATH = path.join(VENV_PATH, 'bin', 'python');
const PIP_PATH = path.join(VENV_PATH, 'bin', 'pip');

// Create and setup virtual environment
async function setupVirtualEnv() {
    return new Promise((resolve, reject) => {
        console.log('Setting up Python virtual environment...');
        
        // Create venv directory if it doesn't exist
        if (!fs.existsSync(VENV_PATH)) {
            console.log('Creating new virtual environment...');
            const createVenv = spawn('python3', ['-m', 'venv', '--without-pip', VENV_PATH], {
                shell: true
            });

            createVenv.stdout.on('data', (data) => {
                console.log(`Venv setup: ${data.toString().trim()}`);
            });

            createVenv.stderr.on('data', (data) => {
                console.error(`Venv setup error: ${data.toString().trim()}`);
            });

            createVenv.on('close', async (code) => {
                if (code === 0) {
                    try {
                        // Install pip in the virtual environment
                        console.log('Installing pip in virtual environment...');
                        await new Promise((resolve, reject) => {
                            const getPip = spawn(PYTHON_PATH, ['-m', 'ensurepip', '--default-pip'], {
                                shell: true
                            });

                            getPip.stdout.on('data', (data) => {
                                console.log(`Pip setup: ${data.toString().trim()}`);
                            });

                            getPip.stderr.on('data', (data) => {
                                console.error(`Pip setup error: ${data.toString().trim()}`);
                            });

                            getPip.on('close', (code) => {
                                if (code === 0) {
                                    resolve();
                                } else {
                                    reject(new Error(`pip installation failed with code ${code}`));
                                }
                            });
                        });

                        // Upgrade pip
                        await new Promise((resolve, reject) => {
                            const upgradePip = spawn(PIP_PATH, ['install', '--upgrade', 'pip'], {
                                shell: true
                            });

                            upgradePip.on('close', (code) => {
                                if (code === 0) {
                                    resolve();
                                } else {
                                    reject(new Error(`pip upgrade failed with code ${code}`));
                                }
                            });
                        });

                        // Install requirements
                        console.log('Installing Python dependencies...');
                        const pip = spawn(PIP_PATH, ['install', '-r', 'requirements.txt'], {
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
                                reject(new Error(`pip install requirements failed with code ${code}`));
                            }
                        });
                    } catch (error) {
                        reject(error);
                    }
                } else {
                    reject(new Error(`venv creation failed with code ${code}`));
                }
            });
        } else {
            // Virtual environment exists, just install requirements
            console.log('Installing Python dependencies in existing virtual environment...');
            const pip = spawn(PIP_PATH, ['install', '-r', 'requirements.txt'], {
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
                    reject(new Error(`pip install requirements failed with code ${code}`));
                }
            });
        }
    });
}

// Start the Python backend
async function startBackend() {
    try {
        await setupVirtualEnv();
        
        return new Promise((resolve, reject) => {
            console.log('Starting backend server...');
            const server = spawn(PYTHON_PATH, ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'], {
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