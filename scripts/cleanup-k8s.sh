#!/bin/bash

# PulseDev+ Kubernetes Cleanup Script
# This script removes the complete PulseDev CCM system from Kubernetes

echo "🧹 PulseDev+ Kubernetes Cleanup"
echo "==============================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  This will delete the entire pulsedev-ccm namespace and all data!${NC}"
echo -e "${RED}This action cannot be undone!${NC}"
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 1
fi

echo ""
echo "Deleting PulseDev CCM deployment..."

# Delete the namespace (this will delete everything inside it)
kubectl delete namespace pulsedev-ccm

# Wait for the namespace to be fully deleted
echo "Waiting for namespace deletion to complete..."
kubectl wait --for=delete namespace/pulsedev-ccm --timeout=300s

echo ""
echo "Cleaning up Docker images (optional)..."
read -p "Do you want to delete the Docker image as well? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi pulsedev-ccm-api:latest 2>/dev/null || echo "Docker image not found or already deleted"
fi

echo ""
echo -e "${GREEN}🎉 Cleanup complete!${NC}"
echo "The PulseDev CCM system has been removed from your Kubernetes cluster."
