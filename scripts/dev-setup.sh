#!/bin/bash

# PulseDev+ Development Setup Script
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

setup_environment() {
    log_info "Setting up development environment..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_warn "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Start services
    log_info "Starting PostgreSQL and Redis..."
    docker-compose up -d postgres redis
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are healthy
    if docker-compose ps | grep -q "healthy"; then
        log_info "Services are healthy"
    else
        log_warn "Some services may not be ready yet"
    fi
}

install_dependencies() {
    log_info "Installing dependencies..."
    
    # Install root dependencies
    npm install
    
    # Install API dependencies
    log_info "Installing API dependencies..."
    cd apps/ccm-api
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ../..
    
    # Install VSCode plugin dependencies
    log_info "Installing VSCode plugin dependencies..."
    cd apps/vscode-plugin
    npm install
    cd ../..
    
    # Install browser extension dependencies
    log_info "Installing browser extension dependencies..."
    cd apps/browser-extension
    npm install
    cd ../..
    
    log_info "Dependencies installed successfully"
}

setup_database() {
    log_info "Setting up database..."
    
    # Wait for PostgreSQL to be ready
    while ! docker-compose exec postgres pg_isready -U postgres > /dev/null 2>&1; do
        log_info "Waiting for PostgreSQL..."
        sleep 2
    done
    
    # Run database migrations
    log_info "Running database migrations..."
    docker-compose exec postgres psql -U postgres -d pulsedev_ccm -f /docker-entrypoint-initdb.d/01-schema.sql
    
    log_info "Database setup completed"
}

build_plugins() {
    log_info "Building plugins..."
    
    # Build VSCode plugin
    cd apps/vscode-plugin
    npm run compile
    cd ../..
    
    # Build browser extension
    cd apps/browser-extension
    npm run build
    cd ../..
    
    log_info "Plugins built successfully"
}

start_development() {
    log_info "Starting development servers..."
    
    # Start API in development mode
    docker-compose up -d ccm-api
    
    # Start frontend in development mode
    npm run dev &
    
    log_info "Development environment is ready!"
    log_info "Frontend: http://localhost:3000"
    log_info "API: http://localhost:8000"
    log_info "API Docs: http://localhost:8000/docs"
    log_info "Grafana: http://localhost:3001 (admin/admin)"
    log_info "n8n: http://localhost:5678 (admin/password)"
}

show_plugin_instructions() {
    log_info "Plugin Installation Instructions:"
    echo
    echo "VSCode Plugin:"
    echo "1. Open VSCode"
    echo "2. Go to Extensions (Ctrl+Shift+X)"
    echo "3. Click 'Install from VSIX'"
    echo "4. Select apps/vscode-plugin/pulsedev-*.vsix"
    echo
    echo "Browser Extension:"
    echo "1. Open Chrome/Firefox"
    echo "2. Go to Extensions page"
    echo "3. Enable Developer mode"
    echo "4. Click 'Load unpacked'"
    echo "5. Select apps/browser-extension/dist folder"
    echo
    echo "Neovim Plugin:"
    echo "1. Copy apps/nvim-plugin/lua/pulsedev to your Neovim config"
    echo "2. Add require('pulsedev').setup() to your init.lua"
}

main() {
    log_info "Starting PulseDev+ development setup..."
    
    setup_environment
    install_dependencies
    setup_database
    build_plugins
    start_development
    show_plugin_instructions
    
    log_info "Development setup completed successfully!"
    log_info "Run 'make logs' to view application logs"
    log_info "Run 'make clean' to stop and clean up"
}

case "${1:-}" in
    "env")
        setup_environment
        ;;
    "deps")
        install_dependencies
        ;;
    "db")
        setup_database
        ;;
    "plugins")
        build_plugins
        ;;
    "start")
        start_development
        ;;
    *)
        main
        ;;
esac