@echo off
REM TableManager Backend Setup Script for Windows

echo Setting up TableManager Backend...

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Create .env from example if not exists
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    echo Please edit .env with your database credentials and secret key.
)

REM Create uploads directories
echo Creating upload directories...
mkdir uploads\profiles 2>nul
mkdir uploads\products 2>nul
mkdir uploads\temp 2>nul

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your database credentials
echo 2. Ensure PostgreSQL is running
echo 3. Run: alembic upgrade head
echo 4. Start server: uvicorn app.main:app --reload
echo.
echo API docs: http://localhost:8000/docs
