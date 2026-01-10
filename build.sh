#!/bin/bash
# Build script for Railway deployment

echo "🔧 Starting build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Compile translations
echo "🌐 Compiling translations..."
python manage.py compilemessages --ignore=venv --ignore=env

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

echo "✅ Build completed successfully!"
