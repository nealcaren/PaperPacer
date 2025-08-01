#!/bin/bash

# Production startup script for PaperPacer
# This script starts the application using Gunicorn WSGI server

echo "🚀 Starting PaperPacer in production mode..."

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

# Set production environment variables
export FLASK_ENV=production
export FLASK_DEBUG=0

# Create instance directory if it doesn't exist
mkdir -p instance

# Initialize database if needed
echo "🗄️  Initializing database..."
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database ready!')"

# Start Gunicorn server
echo "🌟 Starting Gunicorn server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

gunicorn --config gunicorn.conf.py wsgi:app