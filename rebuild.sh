#!/bin/bash

echo "Stopping containers..."
docker compose down

echo "Building services..."
# Only use --no-cache if explicitly requested
if [ "$1" == "--no-cache" ]; then
    docker compose build --no-cache
else
    docker compose build
fi

echo "Starting services..."
docker compose up -d

echo "Waiting for services to be healthy..."
# Wait for backend health check to succeed
while ! docker compose ps backend | grep -q "healthy"; do
    echo "Waiting for backend to be ready..."
    sleep 2
done

echo "Services are ready! Container status:"
docker compose ps
