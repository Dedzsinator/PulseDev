#!/bin/bash

# Quick Kubernetes Test Script
# Tests if the PulseDev CCM system is running correctly in Kubernetes

echo "🧪 Testing PulseDev Kubernetes Deployment"
echo "========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Checking if namespace exists..."
if kubectl get namespace pulsedev-ccm &> /dev/null; then
    echo -e "${GREEN}✅ Namespace 'pulsedev-ccm' exists${NC}"
else
    echo -e "${RED}❌ Namespace 'pulsedev-ccm' not found${NC}"
    exit 1
fi

echo ""
echo "Checking pod status..."
kubectl get pods -n pulsedev-ccm

echo ""
echo "Checking service status..."
kubectl get services -n pulsedev-ccm

echo ""
echo "Testing database connectivity..."
DB_POD=$(kubectl get pods -n pulsedev-ccm -l app=postgres -o jsonpath='{.items[0].metadata.name}')
if [ ! -z "$DB_POD" ]; then
    echo "Database pod: $DB_POD"
    kubectl exec -n pulsedev-ccm $DB_POD -- pg_isready
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database is ready${NC}"
    else
        echo -e "${RED}❌ Database is not ready${NC}"
    fi
else
    echo -e "${RED}❌ No database pod found${NC}"
fi

echo ""
echo "Testing Redis connectivity..."
REDIS_POD=$(kubectl get pods -n pulsedev-ccm -l app=redis -o jsonpath='{.items[0].metadata.name}')
if [ ! -z "$REDIS_POD" ]; then
    echo "Redis pod: $REDIS_POD"
    kubectl exec -n pulsedev-ccm $REDIS_POD -- redis-cli ping
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Redis is ready${NC}"
    else
        echo -e "${RED}❌ Redis is not ready${NC}"
    fi
else
    echo -e "${RED}❌ No Redis pod found${NC}"
fi

echo ""
echo "Testing API health..."
API_POD=$(kubectl get pods -n pulsedev-ccm -l app=ccm-api -o jsonpath='{.items[0].metadata.name}')
if [ ! -z "$API_POD" ]; then
    echo "API pod: $API_POD"

    # Port forward to test the API
    kubectl port-forward -n pulsedev-ccm $API_POD 8080:8000 &
    PORT_FORWARD_PID=$!
    sleep 3

    if curl -f http://localhost:8080/health &> /dev/null; then
        echo -e "${GREEN}✅ API health check passed${NC}"
    else
        echo -e "${RED}❌ API health check failed${NC}"
    fi

    kill $PORT_FORWARD_PID &> /dev/null
else
    echo -e "${RED}❌ No API pod found${NC}"
fi

echo ""
echo "Checking resource usage..."
kubectl top pods -n pulsedev-ccm 2>/dev/null || echo "Metrics server not available"

echo ""
echo "Recent events:"
kubectl get events -n pulsedev-ccm --sort-by='.lastTimestamp' | tail -10

echo ""
echo -e "${GREEN}Test complete!${NC}"
