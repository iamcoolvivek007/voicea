#!/bin/bash

set -e

echo "🧹 Cleaning up any existing containers..."
docker-compose -f docker-compose.dev.yml down -v --remove-orphans

echo "📦 Building and starting all services..."
docker-compose -f docker-compose.dev.yml up --build

# The script will stay running with the compose output
# To stop, press Ctrl+C