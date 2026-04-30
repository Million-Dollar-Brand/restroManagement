#!/usr/bin/env python3
"""
Create admin user script
Usage: python create_admin.py [email] [username] [password]
Defaults: admin@example.com, admin, AdminPass123!
"""

import sys
import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash
from app.config import settings

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def create_admin(
    email: str = "admin@example.com",
    username: str = "admin",
    password: str = "AdminPass123!",
    full_name: str = "Administrator"
):
    """Create an admin user"""
    db: Session = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing:
            print(f"User already exists: {existing.username} ({existing.email})")
            if input("Update this user to admin? (y/N): ").lower() == 'y':
                existing.is_admin = True
                db.commit()
                print(f"User {existing.username} is now an admin")
            return

        # Create admin user
        admin = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_admin=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("=" * 50)
        print("Admin user created successfully!")
        print("=" * 50)
        print(f"ID:        {admin.id}")
        print(f"Username:  {admin.username}")
        print(f"Email:     {admin.email}")
        print(f"Full Name: {admin.full_name}")
        print(f"Admin:     {admin.is_admin}")
        print("=" * 50)
        print("\nLogin credentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print("\n⚠️  Change the password after first login!")

    finally:
        db.close()


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) >= 3:
        email, username, password = args[0], args[1], args[2]
        full_name = args[3] if len(args) > 3 else "Administrator"
    else:
        print("Creating default admin user (admin@example.com / admin)")
        print("Usage: python create_admin.py [email] [username] [password] [full_name]")
        print()
        email = "admin@example.com"
        username = "admin"
        password = "AdminPass123!"
        full_name = "Administrator"

    create_admin(email, username, password, full_name)
