#!/bin/bash
set -e

# Date Prefix File Renamer - Container Entrypoint Script

echo "Date Prefix File Renamer - Docker Container"
echo "==========================================="

# Function to check if X11 is available
check_x11() {
    if [ -n "$DISPLAY" ] && command -v xdpyinfo >/dev/null 2>&1; then
        if xdpyinfo >/dev/null 2>&1; then
            echo "✓ X11 display available: $DISPLAY"
            return 0
        else
            echo "✗ X11 display not accessible: $DISPLAY"
            return 1
        fi
    else
        echo "✗ X11 not configured or xdpyinfo not available"
        return 1
    fi
}

# Function to validate data directory
validate_data_directory() {
    if [ ! -d "/data" ]; then
        echo "✗ Error: /data directory not found"
        echo "Please mount a directory to /data using: -v /host/path:/data"
        exit 1
    fi
    
    if [ ! -r "/data" ] || [ ! -w "/data" ]; then
        echo "✗ Error: /data directory not readable/writable"
        echo "Check permissions on the mounted directory"
        exit 1
    fi
    
    echo "✓ Data directory accessible: /data"
}

# Function to show usage
show_usage() {
    echo "Usage:"
    echo "  Web mode:  docker run -v /host/path:/data -p 8080:8080 date-prefix-renamer"
    echo "  GUI mode:  docker run -v /host/path:/data -e DISPLAY=\$DISPLAY date-prefix-renamer gui"
    echo "  CLI mode:  docker run -v /host/path:/data date-prefix-renamer cli [directory]"
    echo "  Help:      docker run date-prefix-renamer help"
    echo ""
    echo "Examples:"
    echo "  # Web interface (Recommended)"
    echo "  docker run -v ~/Documents:/data -p 8080:8080 date-prefix-renamer"
    echo "  Then open: http://localhost:8080"
    echo ""
    echo "  # GUI with X11 forwarding (Linux/macOS)"
    echo "  docker run -v ~/Documents:/data -e DISPLAY=\$DISPLAY date-prefix-renamer gui"
    echo ""
    echo "  # CLI mode for headless environments"
    echo "  docker run -v ~/Documents:/data date-prefix-renamer cli /data/my-folder"
    echo ""
    echo "Environment Variables:"
    echo "  DISPLAY     - X11 display for GUI mode (e.g., :0, localhost:10.0)"
    echo "  LOG_LEVEL   - Logging level (DEBUG, INFO, WARNING, ERROR)"
}

# Parse command line arguments
MODE="${1:-web}"
TARGET_DIR="${2:-}"

case "$MODE" in
    "web")
        echo "Starting in WEB mode..."
        validate_data_directory
        
        echo "Launching web interface on http://0.0.0.0:8080"
        echo "Access from your browser: http://localhost:8080"
        cd /app
        exec python web_app.py
        ;;
        
    "gui")
        echo "Starting in GUI mode..."
        validate_data_directory
        
        echo "Launching GUI application..."
        echo "Note: GUI requires X11 forwarding to be configured on your host"
        cd /app
        exec python modern_gui.py
        ;;
        
    "cli")
        echo "Starting in CLI mode..."
        validate_data_directory
        
        if [ -z "$TARGET_DIR" ]; then
            echo "CLI mode usage: docker run -v /host/path:/data date-prefix-renamer cli /data/target-folder"
            echo "Available directories in /data:"
            ls -la /data/ 2>/dev/null || echo "  (empty or not accessible)"
            exit 1
        fi
        
        if [ ! -d "$TARGET_DIR" ]; then
            echo "✗ Error: Target directory '$TARGET_DIR' does not exist"
            echo "Available directories in /data:"
            ls -la /data/ 2>/dev/null || echo "  (empty or not accessible)"
            exit 1
        fi
        
        echo "Processing directory: $TARGET_DIR"
        cd /app
        shift 2  # Remove 'cli' and directory from arguments
        exec python -m src.main "$TARGET_DIR" "$@"
        ;;
        
    "help"|"--help"|"-h")
        show_usage
        exit 0
        ;;
        
    "version"|"--version"|"-v")
        cd /app
        python -c "import src; print(f'Date Prefix File Renamer v{src.__version__}')"
        exit 0
        ;;
        
    *)
        echo "✗ Error: Unknown mode '$MODE'"
        echo ""
        show_usage
        exit 1
        ;;
esac