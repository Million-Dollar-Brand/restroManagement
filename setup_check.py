#!/usr/bin/env python3
"""
Quick setup and validation script for TableManager Backend
Run: python setup_check.py
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("ERROR: Python 3.9+ required")
        return False
    print(f" Python version OK: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    required = ["fastapi", "uvicorn", "sqlalchemy", "alembic", "psycopg2", "jose", "passlib"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print(f" {pkg} - installed")
        except ImportError:
            missing.append(pkg)
            print(f" {pkg} - MISSING")

    if missing:
        print(f"\nPlease install: pip install {' '.join(missing)}")
        return False
    return True


def check_env_file():
    """Check if .env exists and has required variables"""
    env_path = Path(".env")
    if not env_path.exists():
        print(" WARNING: .env file not found")
        print("   Copy .env.example to .env and configure it")
        return False

    with open(env_path) as f:
        content = f.read()

    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    missing = []

    for var in required_vars:
        if var not in content or content.find(var) == content.find("=", content.find(var)) + 1:
            # Check if value is not just the placeholder
            line_start = content.find(var + "=")
            if line_start != -1:
                line_end = content.find("\n", line_start)
                line = content[line_start:line_end]
                if "your-" in line or "change-" in line or "example" in line.lower():
                    missing.append(var)

    if missing:
        print(f" WARNING: Update these in .env: {', '.join(missing)}")
        return False

    print(" .env file configured")
    return True


def check_uploads_dir():
    """Check if uploads directory is writable"""
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        uploads_dir.mkdir(parents=True)
        print(" Created uploads directory")
    else:
        print(" Uploads directory exists")

    # Check write permission
    test_file = uploads_dir / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
        print(" Uploads directory is writable")
        return True
    except Exception as e:
        print(f" ERROR: Uploads directory not writable: {e}")
        return False


def check_database_connection():
    """Check database connection"""
    try:
        from app.config import settings
        from sqlalchemy import create_engine
        from sqlalchemy.exc import OperationalError

        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print(" Database connection OK")
        return True
    except Exception as e:
        print(f" Database connection FAILED: {e}")
        print("  - Check DATABASE_URL in .env")
        print("  - Ensure PostgreSQL is running")
        return False


def run_alembic_check():
    """Check if migrations can be run"""
    try:
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(" Alembic configured")
            print(f"  Current revision: {result.stdout.strip()}")
            return True
        else:
            print(" Alembic check failed")
            print(f"  {result.stderr}")
            return False
    except FileNotFoundError:
        print(" ERROR: Alembic not installed")
        return False


def main():
    print("=" * 60)
    print("TableManager Backend - Setup Validation")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment Config", check_env_file),
        ("Uploads Directory", check_uploads_dir),
        ("Database Connection", check_database_connection),
        ("Alembic Setup", run_alembic_check),
    ]

    print("\nRunning checks...\n")
    results = {}

    for name, check_func in checks:
        print(f"[{name}]")
        results[name] = check_func()
        print()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = " PASS" if result else " FAIL"
        print(f"{status} - {name}")

    print()
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print(" All checks passed! You can start the server:")
        print("  uvicorn app.main:app --reload")
        return 0
    else:
        print(" Some checks failed. Please fix them before starting.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
