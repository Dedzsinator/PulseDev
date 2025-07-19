#!/bin/bash

# PulseDev+ Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="pulsedev-ccm"
CLUSTER_NAME="pulsedev-cluster"
REGION="us-west-2"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed"
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_warn "helm is not installed, using kubectl manifests"
        USE_HELM=false
    else
        USE_HELM=true
    fi
    
    log_info "Prerequisites check completed"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build API image
    docker build -t pulsedev-ccm-api:latest ./apps/ccm-api/
    
    # Build frontend image
    docker build -f Dockerfile.frontend -t pulsedev-frontend:latest .
    
    log_info "Docker images built successfully"
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    if [ "$USE_HELM" = true ]; then
        log_info "Using Helm for deployment"
        helm upgrade --install pulsedev ./helm/pulsedev \
            --namespace $NAMESPACE \
            --create-namespace \
            --wait \
            --timeout 10m
    else
        log_info "Using kubectl manifests for deployment"
        kubectl apply -f k8s/namespace.yaml
        kubectl apply -f k8s/secrets.yaml
        kubectl apply -f k8s/postgres.yaml
        kubectl apply -f k8s/redis.yaml
        kubectl apply -f k8s/ccm-api.yaml
        kubectl apply -f k8s/frontend.yaml
        kubectl apply -f k8s/monitoring.yaml
        
        # Wait for deployments
        kubectl rollout status deployment/postgres -n $NAMESPACE --timeout=300s
        kubectl rollout status deployment/redis -n $NAMESPACE --timeout=300s
        kubectl rollout status deployment/ccm-api -n $NAMESPACE --timeout=300s
        kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=300s
    fi
    
    log_info "Kubernetes deployment completed"
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Port forward for local access
    kubectl port-forward service/grafana-service 3001:3000 -n $NAMESPACE &
    kubectl port-forward service/prometheus-service 9090:9090 -n $NAMESPACE &
    
    log_info "Monitoring setup completed"
    log_info "Access Grafana at: http://localhost:3001 (admin/admin)"
    log_info "Access Prometheus at: http://localhost:9090"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pod status
    kubectl get pods -n $NAMESPACE
    
    # Check service status
    kubectl get services -n $NAMESPACE
    
    # Check if API is responding
    API_POD=$(kubectl get pods -n $NAMESPACE -l app=ccm-api -o jsonpath='{.items[0].metadata.name}')
    if kubectl exec -n $NAMESPACE $API_POD -- curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_info "API health check passed"
    else
        log_error "API health check failed"
        exit 1
    fi
    
    log_info "Deployment verification completed"
}

cleanup() {
    log_info "Cleaning up..."
    pkill -f "kubectl port-forward" || true
}

main() {
    log_info "Starting PulseDev+ deployment..."
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    check_prerequisites
    build_images
    deploy_kubernetes
    setup_monitoring
    verify_deployment
    
    log_info "Deployment completed successfully!"
    log_info "Frontend: kubectl port-forward service/frontend-service 3000:80 -n $NAMESPACE"
    log_info "API: kubectl port-forward service/ccm-api-service 8000:8000 -n $NAMESPACE"
}

# Parse command line arguments
case "${1:-}" in
    "build")
        build_images
        ;;
    "deploy")
        deploy_kubernetes
        ;;
    "monitor")
        setup_monitoring
        ;;
    "verify")
        verify_deployment
        ;;
    "clean")
        log_info "Cleaning up deployment..."
        kubectl delete namespace $NAMESPACE --ignore-not-found=true
        log_info "Cleanup completed"
        ;;
    *)
        main
        ;;
esac