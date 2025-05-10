const { spawn } = require('child_process');
const path = require('path');

const FRONTEND_PORT = 7779;
const BACKEND_PORT = 7778;

// Start the Python backend
async function startBackend() {
    return new Promise((resolve, reject) => {
        console.log('Starting backend server...');
        const server = spawn('python3', ['-m', 'uvicorn', 'app.main:app', '--host', 'localhost', '--port', BACKEND_PORT.toString()], {
            cwd: path.join(__dirname, 'Application/backend'),
            stdio: 'inherit',
            env: {
                ...process.env,
                PYTHONPATH: path.join(__dirname, 'Application/backend'),
            }
        });

        server.on('error', (error) => {
            console.error('Backend server error:', error);
            reject(error);
        });

        resolve(server);
    });
}

// Start the frontend
async function startFrontend() {
    return new Promise((resolve, reject) => {
        console.log('Starting frontend server...');
        const frontend = spawn('npm', ['run', 'preview', '--', '--port', FRONTEND_PORT.toString()], {
            cwd: path.join(__dirname, 'Application/frontend'),
            stdio: 'inherit',
            env: { 
                ...process.env, 
                NODE_ENV: 'production'
            }
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