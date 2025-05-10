#!/bin/bash
set -e

# Pull the latest changes
git pull origin master

# Copy files to AMP instance directory
sudo cp -r . /home/amp/instances/nba_stats/

# Set correct permissions
sudo chown -R amp:amp /home/amp/instances/nba_stats/

# Use AMP's management interface to restart the instance
curl -X POST "http://localhost:8080/API/Core/Start" \
  -H "Authorization: Basic ${AMP_API_KEY}" \
  -H "Content-Type: application/json" \
  --data '{"InstanceID": "Instance1"}'