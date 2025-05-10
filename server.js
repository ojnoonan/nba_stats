const { spawn } = require('child_process');
const path = require('path');

const AMP_BASE_PATH = '/AMP/node-server/app';

// Start the Python backend
function startBackend() {
    const backend = spawn('python3', ['-m', 'pip', 'install', '-r', 'requirements.txt'], {
        cwd: path.join(AMP_BASE_PATH, 'Application/backend')
    }).on('close', (code) => {
        if (code === 0) {
            const server = spawn('python3', ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'], {
                cwd: path.join(AMP_BASE_PATH, 'Application/backend')
            });

            server.stdout.on('data', (data) => {
                console.log(`Backend: ${data}`);
            });

            server.stderr.on('data', (data) => {
                console.error(`Backend error: ${data}`);
            });
        }
    });

    return backend;
}

// Start the frontend
function startFrontend() {
    const frontend = spawn('npm', ['run', 'preview', '--', '--port', '7779', '--host'], {
        cwd: path.join(AMP_BASE_PATH, 'Application/frontend'),
        shell: true,
        env: { ...process.env, NODE_ENV: 'production' }
    });

    frontend.stdout.on('data', (data) => {
        console.log(`Frontend: ${data}`);
    });

    frontend.stderr.on('data', (data) => {
        console.error(`Frontend error: ${data}`);
    });

    return frontend;
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
backend = startBackend();
frontend = startFrontend();