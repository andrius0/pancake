#!/bin/bash
set -e

# Build Order Service
echo "****************************************************"
echo "Building order_service..."
echo "****************************************************"
docker build -t pancake-order-service:latest ./order_service

echo "****************************************************"
echo "Building status_service..."
echo "****************************************************"
docker build -t pancake-status-service:latest ./status_service

echo "****************************************************"
echo "Building workflow_worker..."
echo "****************************************************"
docker build -t pancake-workflow-worker:latest ./workflow_worker

echo "****************************************************"
echo "Building activity_workers/analyze_order..."
echo "****************************************************"
docker build -t pancake-analyze-order-worker:latest ./activity_workers/analyze_order

echo "****************************************************"
echo "Building activity_workers/inventory..."
echo "****************************************************"
docker build -t pancake-inventory-worker:latest ./activity_workers/inventory

echo "****************************************************"
echo "Building activity_workers/kitchen..."
echo "****************************************************"
docker build -t pancake-kitchen-worker:latest ./activity_workers/kitchen

echo "****************************************************"
echo "Building activity_workers/notify..."
echo "****************************************************"
docker build -t pancake-notify-worker:latest ./activity_workers/notify

echo "****************************************************"
echo "Building frontend..."
echo "****************************************************"
docker build -t pancake-frontend:latest ./front_end


echo "All images built successfully!" 