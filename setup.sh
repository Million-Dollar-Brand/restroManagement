#!/bin/bash

# TableManager Backend Setup Script

echo "Setting up TableManager Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env with your database credentials and secret key."
fi

# Create uploads directories
echo "Creating upload directories..."
mkdir -p uploads/profiles uploads/products uploads/temp

# Check if PostgreSQL is running
if ! pg_isready -q 2>/dev/null; then
    echo "Warning: PostgreSQL is not running. Please start PostgreSQL."
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database credentials"
echo "2. Ensure PostgreSQL is running"
echo "3. Run: alembic upgrade head"
echo "4. Start server: uvicorn app.main:app --reload"
echo ""
echo "API docs: http://localhost:8000/docs"
