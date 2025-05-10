const { spawn } = require('child_process');
const path = require('path');

// Start the Python backend
function startBackend() {
    const backend = spawn('python3', ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'], {
        cwd: path.join(__dirname, 'Application/backend')
    });

    backend.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data}`);
    });

    backend.stderr.on('data', (data) => {
        console.error(`Backend stderr: ${data}`);
    });

    backend.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });

    return backend;
}

// Start the frontend
function startFrontend() {
    const frontend = spawn('npm', ['run', 'preview', '--', '--port', '7779', '--host'], {
        cwd: path.join(__dirname, 'Application/frontend'),
        shell: true
    });

    frontend.stdout.on('data', (data) => {
        console.log(`Frontend stdout: ${data}`);
    });

    frontend.stderr.on('data', (data) => {
        console.error(`Frontend stderr: ${data}`);
    });

    frontend.on('close', (code) => {
        console.log(`Frontend process exited with code ${code}`);
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