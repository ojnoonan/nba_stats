const { spawn } = require('child_process');
const path = require('path');
const https = require('https');
const fs = require('fs');

const AMP_BASE_PATH = '/AMP/node-server/app';

// Check Python version and installation
async function checkPython() {
    return new Promise((resolve, reject) => {
        const python = spawn('python3', ['--version']);
        
        python.stdout.on('data', (data) => {
            console.log(`Python version: ${data.toString().trim()}`);
            resolve();
        });

        python.stderr.on('data', (data) => {
            console.error(`Python check error: ${data.toString().trim()}`);
        });

        python.on('error', (error) => {
            if (error.code === 'ENOENT') {
                console.log('Python3 not found, attempting to install using yum...');
                const installPython = spawn('yum', ['install', '-y', 'python3'], {
                    shell: true
                });

                installPython.stdout.on('data', (data) => {
                    console.log(`Python install: ${data.toString().trim()}`);
                });

                installPython.stderr.on('data', (data) => {
                    console.error(`Python install error: ${data.toString().trim()}`);
                });

                installPython.on('close', (code) => {
                    if (code === 0) {
                        resolve();
                    } else {
                        reject(new Error('Failed to install Python'));
                    }
                });
            } else {
                reject(error);
            }
        });

        python.on('close', (code) => {
            if (code === 0) {
                resolve();
            }
        });
    });
}

// Install pip if not present
async function ensurePip() {
    return new Promise((resolve, reject) => {
        console.log('Downloading get-pip.py...');
        const file = fs.createWriteStream('get-pip.py');
        https.get('https://bootstrap.pypa.io/get-pip.py', (response) => {
            response.pipe(file);
            file.on('finish', () => {
                file.close();
                console.log('Installing pip...');
                const installPip = spawn('python3', ['get-pip.py', '--user'], {
                    shell: true
                });

                installPip.stdout.on('data', (data) => {
                    console.log(`Pip setup: ${data.toString().trim()}`);
                });

                installPip.stderr.on('data', (data) => {
                    console.error(`Pip setup error: ${data.toString().trim()}`);
                });

                installPip.on('close', (code) => {
                    fs.unlink('get-pip.py', () => {}); // Clean up
                    if (code === 0) {
                        resolve();
                    } else {
                        reject(new Error(`Failed to install pip, exit code: ${code}`));
                    }
                });
            });
        }).on('error', (err) => {
            fs.unlink('get-pip.py', () => {});
            reject(err);
        });
    });
}

// Start the Python backend
async function startBackend() {
    try {
        await ensurePip();
        
        return new Promise((resolve, reject) => {
            console.log('Installing Python dependencies...');
            const pip = spawn('python3', ['-m', 'pip', 'install', '--user', '-r', 'requirements.txt'], {
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
                    console.log('Starting backend server...');
                    const server = spawn('python3', ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'], {
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
                } else {
                    reject(new Error(`pip install failed with code ${code}`));
                }
            });
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
        await checkPython();
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