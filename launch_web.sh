#!/bin/bash
# Launch web interface locally (without Docker)

echo "📦 Date Prefix Renamer - Web Interface"
echo "======================================="
echo ""

# Check if Flask is installed
if ! python3.11 -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip3.11 install Flask Werkzeug
fi

# Change to project directory
cd "/Users/Mohammad/Documents/app development folder/RE-N"

echo "🚀 Starting web server on http://localhost:8080"
echo "Press Ctrl+C to stop"
echo ""

# Run the web app
python3.11 web_app.py
