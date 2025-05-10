const { spawn, spawnSync } = require('child_process');
const path = require('path');

const AMP_BASE_PATH = '/AMP/node-server/app';
const FRONTEND_PORT = 7779;
const BACKEND_PORT = 7778;

// Install required system packages
function installSystemPackages() {
    console.log('Installing Python packages...');
    const packages = [
        'python3-fastapi',
        'python3-sqlalchemy',
        'python3-pydantic',
        'python3-dotenv',
        'python3-pandas',
        'python3-aiohttp',
        'python3-pytest',
        'python3-httpx',
        'python3-uvicorn',
        'python3-apscheduler',
        'python3-pip',
        'python3-venv'
    ];

    try {
        // Update package list with sudo
        console.log('Updating package list...');
        const updateResult = spawnSync('sudo', ['apt-get', 'update'], { 
            stdio: 'inherit',
            shell: true
        });
        if (updateResult.error || updateResult.status !== 0) {
            console.error('Failed to update package list');
            // Try without sudo as fallback
            const nonSudoUpdateResult = spawnSync('apt-get', ['update'], { 
                stdio: 'inherit',
                shell: true
            });
            if (nonSudoUpdateResult.error || nonSudoUpdateResult.status !== 0) {
                console.error('Failed to update package list without sudo');
                return false;
            }
        }

        // Install system packages with sudo
        console.log('Installing system packages...');
        const installResult = spawnSync('sudo', ['apt-get', 'install', '-y', ...packages], { 
            stdio: 'inherit',
            shell: true
        });
        if (installResult.error || installResult.status !== 0) {
            console.error('Failed to install system packages with sudo');
            // Try without sudo as fallback
            const nonSudoInstallResult = spawnSync('apt-get', ['install', '-y', ...packages], { 
                stdio: 'inherit',
                shell: true
            });
            if (nonSudoInstallResult.error || nonSudoInstallResult.status !== 0) {
                console.error('Failed to install system packages without sudo');
                return false;
            }
        }

        // Create virtual environment
        const venvPath = path.join(AMP_BASE_PATH, 'venv');
        console.log('Creating virtual environment...');
        const venvResult = spawnSync('python3', ['-m', 'venv', venvPath], { 
            stdio: 'inherit',
            shell: true
        });
        if (venvResult.error || venvResult.status !== 0) {
            console.error('Failed to create virtual environment');
            return false;
        }

        // Install nba_api in the virtual environment
        console.log('Installing nba_api in virtual environment...');
        const pipResult = spawnSync(path.join(venvPath, 'bin', 'pip'), ['install', 'nba_api'], { 
            stdio: 'inherit',
            shell: true
        });
        if (pipResult.error || pipResult.status !== 0) {
            console.error('Failed to install nba_api');
            return false;
        }

        console.log('Successfully installed all required packages');
        return true;
    } catch (error) {
        console.error('Error installing packages:', error);
        return false;
    }
}

// Start the Python backend
async function startBackend() {
    return new Promise((resolve, reject) => {
        console.log('Starting backend server...');
        const venvPath = path.join(AMP_BASE_PATH, 'venv');
        const pythonPath = path.join(venvPath, 'bin', 'python3');
        
        const server = spawn(pythonPath, ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', BACKEND_PORT.toString()], {
            cwd: path.join(AMP_BASE_PATH, 'Application/backend'),
            stdio: ['pipe', 'pipe', 'pipe'],
            env: {
                ...process.env,
                PYTHONPATH: `${path.join(AMP_BASE_PATH, 'Application/backend')}:/usr/lib/python3/dist-packages:/usr/local/lib/python3.11/dist-packages:/usr/lib/python3.11/dist-packages`,
                PATH: `${path.join(venvPath, 'bin')}:${process.env.PATH}`,
                VIRTUAL_ENV: venvPath,
                HOST: '0.0.0.0'
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
        const frontend = spawn('npm', ['run', 'preview', '--', '--port', FRONTEND_PORT.toString(), '--host', '0.0.0.0'], {
            cwd: path.join(AMP_BASE_PATH, 'Application/frontend'),
            shell: true,
            env: { 
                ...process.env, 
                NODE_ENV: 'production',
                HOST: '0.0.0.0',
                PORT: FRONTEND_PORT.toString()
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
        // Install required packages first
        if (!installSystemPackages()) {
            throw new Error('Failed to install required packages');
        }

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