#!/bin/bash

# Development startup script for PaperPacer
# This script starts the application using Flask's development server
# Usage: Run from the project root directory: ./scripts/start_development.sh

echo "🔧 Starting PaperPacer in development mode..."

# Change to project root directory
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Set development environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Create instance directory if it doesn't exist
mkdir -p instance

# Initialize database if needed
echo "🗄️  Initializing database..."
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database ready!')"

# Start Flask development server
echo "🌟 Starting Flask development server..."
echo "📍 Server will be available at: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo "🔄 Auto-reload enabled for development"
echo ""

python app.py