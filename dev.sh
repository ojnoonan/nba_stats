#!/bin/bash

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Using .venv virtual environment"
elif [ -d "Application/backend/venv" ]; then
    source Application/backend/venv/bin/activate
    echo "Using backend/venv virtual environment"
elif [ -d "Application/backend/env" ]; then
    source Application/backend/env/bin/activate
    echo "Using backend/env virtual environment"
else
    echo "Warning: No virtual environment found, using system Python"
fi

# Start the backend server
cd Application/backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 7778 &
BACKEND_PID=$!

# Start the frontend development server
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Function to handle script termination
cleanup() {
    echo "Shutting down servers..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Keep script running
wait