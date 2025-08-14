#!/bin/bash

# PulseDev+ Kubernetes Deployment Script
# This script deploys the complete PulseDev CCM system to Kubernetes

set -e

echo "🚀 PulseDev+ Kubernetes Deployment"
echo "=================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed. Please install kubectl first.${NC}"
    exit 1
fi

# Check if docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Building Docker Image${NC}"
echo "=============================="

cd apps/ccm-api

# Build the Docker image
echo "Building CCM API Docker image..."
docker build -t pulsedev-ccm-api:latest .

cd ../../

echo -e "${GREEN}✅ Docker image built successfully${NC}"

echo -e "${BLUE}Step 2: Deploying to Kubernetes${NC}"
echo "==============================="

# Apply Kubernetes manifests in order
echo "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "Creating secrets..."
kubectl apply -f k8s/secrets.yaml

echo "Deploying PostgreSQL database..."
kubectl apply -f k8s/postgres.yaml

echo "Deploying Redis cache..."
kubectl apply -f k8s/redis.yaml

echo "Deploying CCM API..."
kubectl apply -f k8s/ccm-api.yaml

echo -e "${GREEN}✅ All services deployed to Kubernetes${NC}"

echo -e "${BLUE}Step 3: Waiting for services to start${NC}"
echo "====================================="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n pulsedev-ccm --timeout=300s

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n pulsedev-ccm --timeout=300s

# Wait for CCM API to be ready
echo "Waiting for CCM API to be ready..."
kubectl wait --for=condition=ready pod -l app=ccm-api -n pulsedev-ccm --timeout=300s

echo -e "${GREEN}✅ All services are ready${NC}"

echo -e "${BLUE}Step 4: Service Information${NC}"
echo "=========================="

# Get service information
kubectl get services -n pulsedev-ccm

echo ""
echo -e "${BLUE}Step 5: Testing API Health${NC}"
echo "========================="

# Get the LoadBalancer IP or NodePort
CCM_SERVICE=$(kubectl get svc ccm-api-service -n pulsedev-ccm -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -z "$CCM_SERVICE" ]; then
    # If LoadBalancer IP is not available, try to get NodePort
    NODE_PORT=$(kubectl get svc ccm-api-service -n pulsedev-ccm -o jsonpath='{.spec.ports[0].nodePort}')
    if [ ! -z "$NODE_PORT" ]; then
        CCM_SERVICE="localhost:$NODE_PORT"
    else
        echo -e "${YELLOW}⚠️  LoadBalancer IP not available. Using port-forward for testing...${NC}"
        kubectl port-forward svc/ccm-api-service 8000:8000 -n pulsedev-ccm &
        PORT_FORWARD_PID=$!
        sleep 5
        CCM_SERVICE="localhost:8000"
    fi
fi

if [ ! -z "$CCM_SERVICE" ]; then
    echo "Testing API health at http://$CCM_SERVICE/health..."
    if curl -f http://$CCM_SERVICE/health &> /dev/null; then
        echo -e "${GREEN}✅ API health check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  API not ready yet, may take a few more minutes${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "======================="
echo "Services deployed:"
echo "  • PostgreSQL Database (with TimescaleDB)"
echo "  • Redis Cache"
echo "  • CCM API Backend (with NVIDIA NIM AI)"
echo ""
echo "Useful commands:"
echo "  • Check status: kubectl get all -n pulsedev-ccm"
echo "  • View logs: kubectl logs -l app=ccm-api -n pulsedev-ccm"
echo "  • Port forward: kubectl port-forward svc/ccm-api-service 8000:8000 -n pulsedev-ccm"
echo "  • Delete deployment: kubectl delete namespace pulsedev-ccm"
echo ""

if [ ! -z "$PORT_FORWARD_PID" ]; then
    echo -e "${YELLOW}Port-forward is running in background (PID: $PORT_FORWARD_PID)${NC}"
    echo "Kill it with: kill $PORT_FORWARD_PID"
fi

echo -e "${BLUE}API Configuration:${NC}"
echo "- Provider: NVIDIA NIM"
echo "- Model: nvidia/llama-3.1-nemotron-70b-instruct"
echo "- Health endpoint: http://$CCM_SERVICE/health"
echo "- API docs: http://$CCM_SERVICE/docs"
