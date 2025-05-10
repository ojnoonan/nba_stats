const { spawn } = require('child_process');
const path = require('path');

// Function to run docker-compose command
function runDockerCompose(args) {
    return new Promise((resolve, reject) => {
        const dockerCompose = spawn('docker-compose', args, {
            stdio: 'inherit',
            shell: true
        });

        dockerCompose.on('error', (err) => {
            console.error('Failed to start docker-compose:', err);
            reject(err);
        });

        dockerCompose.on('close', (code) => {
            if (code !== 0) {
                console.error(`docker-compose exited with code ${code}`);
                reject(new Error(`docker-compose exited with code ${code}`));
            } else {
                resolve();
            }
        });
    });
}

// Main startup function
async function start() {
    try {
        // Ensure we're down first
        await runDockerCompose(['down']);
        
        // Build and start services
        console.log('Building and starting services...');
        await runDockerCompose(['up', '--build', '-d']);
        
        // Keep the Node.js process running
        console.log('Services started successfully');
        process.on('SIGTERM', async () => {
            console.log('Shutting down services...');
            await runDockerCompose(['down']);
            process.exit(0);
        });
    } catch (error) {
        console.error('Error starting services:', error);
        process.exit(1);
    }
}

start();