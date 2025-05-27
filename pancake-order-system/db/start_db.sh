#!/bin/bash

# Stop and remove existing container if it exists
docker stop restaurant-db 2>/dev/null
docker rm restaurant-db 2>/dev/null

# Start PostgreSQL container
docker run --name restaurant-db \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=restaurant \
    -p 5432:5432 \
    -d postgres:latest

# Wait for PostgreSQL to start
echo "Waiting for PostgreSQL to start..."
sleep 5

# Copy and execute the initialization script
docker cp db_init.sql restaurant-db:/db_init.sql
docker exec restaurant-db psql -U postgres -f /db_init.sql

echo "Database initialized successfully!"
echo "Connection details:"
echo "Host: localhost"
echo "Port: 5432"
echo "Database: restaurant"
echo "Username: postgres"
echo "Password: postgres" 