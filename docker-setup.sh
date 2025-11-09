#!/bin/bash
# Quick setup script for Docker GUI on macOS

set -e

echo "======================================"
echo "Date Prefix Renamer - Docker GUI Setup"
echo "======================================"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored output
print_success() {
    echo "✅ $1"
}

print_warning() {
    echo "⚠️  $1"
}

print_error() {
    echo "❌ $1"
}

print_info() {
    echo "ℹ️  $1"
}

# Check for Homebrew
if ! command_exists brew; then
    print_error "Homebrew not found. Please install from https://brew.sh"
    exit 1
fi
print_success "Homebrew installed"

# Check for XQuartz
if [ -d "/Applications/Utilities/XQuartz.app" ]; then
    print_success "XQuartz installed"
else
    print_warning "XQuartz not found"
    echo "Installing XQuartz..."
    brew install --cask xquartz
    print_success "XQuartz installed"
    print_info "Please log out and log back in, then run this script again"
    exit 0
fi

# Check if XQuartz is running
if pgrep -x "X11" > /dev/null || pgrep -x "XQuartz" > /dev/null; then
    print_success "XQuartz is running"
else
    print_warning "XQuartz is not running"
    echo "Starting XQuartz..."
    open -a XQuartz
    sleep 3
    print_success "XQuartz started"
fi

# Configure xhost
echo ""
echo "Configuring X11 access control..."
xhost + 127.0.0.1 2>/dev/null || print_warning "xhost command not available yet"

# Check Docker
if ! command_exists docker; then
    print_error "Docker not found. Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi
print_success "Docker installed"

# Check if Docker is running
if docker info >/dev/null 2>&1; then
    print_success "Docker is running"
else
    print_error "Docker is not running. Please start Docker Desktop"
    exit 1
fi

# Build the Docker image
echo ""
echo "Building Docker image (this may take a few minutes)..."
docker-compose build

if [ $? -eq 0 ]; then
    print_success "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    print_info "If you see 'input/output error', try restarting Docker Desktop:"
    print_info "  1. Click Docker icon in menu bar"
    print_info "  2. Select 'Restart'"
    print_info "  3. Wait for Docker to fully restart"
    print_info "  4. Run this script again"
    exit 1
fi

# Final instructions
echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "To use the GUI:"
echo "  docker-compose up"
echo ""
echo "To use CLI mode:"
echo "  docker-compose --profile cli up date-prefix-renamer-cli"
echo ""
echo "IMPORTANT: XQuartz Settings"
echo "  1. Open XQuartz (Applications/Utilities/XQuartz)"
echo "  2. Go to Preferences → Security"
echo "  3. Enable 'Allow connections from network clients'"
echo "  4. Restart XQuartz"
echo ""
echo "For troubleshooting, see DOCKER_SETUP.md"
echo ""
