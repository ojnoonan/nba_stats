const { spawn } = require('child_process');
const path = require('path');

const AMP_BASE_PATH = '/AMP/node-server/app';
const FRONTEND_PORT = 7779;
const BACKEND_PORT = 7778;

// Start the Python backend
async function startBackend() {
    return new Promise((resolve, reject) => {
        console.log('Starting backend server...');
        const server = spawn('python3', ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', BACKEND_PORT.toString()], {
            cwd: path.join(AMP_BASE_PATH, 'Application/backend'),
            stdio: ['pipe', 'pipe', 'pipe'],
            env: {
                ...process.env,
                PYTHONPATH: `${path.join(AMP_BASE_PATH, 'Application/backend')}:/usr/lib/python3/dist-packages:/usr/local/lib/python3.11/dist-packages:/usr/lib/python3.11/dist-packages`,
                PYTHONUSERBASE: '/usr/local',
                PATH: `/usr/local/bin:${process.env.PATH}`
            }
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
}

// Start the frontend
async function startFrontend() {
    return new Promise((resolve, reject) => {
        console.log('Starting frontend server...');
        const frontend = spawn('npm', ['run', 'preview', '--', '--port', FRONTEND_PORT.toString(), '--host'], {
            cwd: path.join(AMP_BASE_PATH, 'Application/frontend'),
            shell: true,
            env: { 
                ...process.env, 
                NODE_ENV: 'production',
                VITE_BACKEND_URL: `http://localhost:${BACKEND_PORT}`,
                VITE_USE_PROXY: 'true'
            }
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