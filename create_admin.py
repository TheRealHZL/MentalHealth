#!/usr/bin/env python3
"""
Create Admin User Script
"""
import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from src.core.database import AsyncSessionLocal
from src.core.security import hash_password
from src.models import User
import uuid
from datetime import datetime


async def create_admin_user(email: str, password: str, first_name: str = "Admin", last_name: str = "User"):
    """Create an admin user"""
    
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"❌ User mit Email '{email}' existiert bereits!")
            print(f"   Rolle: {existing.role}")
            return False
        
        # Create admin user
        admin = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role="admin",
            is_active=True,
            is_verified=True,
            email_verified=True,
            registration_completed=True,
            created_at=datetime.utcnow(),
        )
        
        session.add(admin)
        await session.commit()
        
        print("✅ Admin-User erfolgreich erstellt!")
        print(f"\n📧 Email:    {email}")
        print(f"🔑 Passwort: {password}")
        print(f"👤 Name:     {first_name} {last_name}")
        print(f"\n🔐 Login-URL: http://localhost:8080/docs")
        print(f"🌐 Frontend:  http://localhost:3000/login")
        
        return True


async def list_admin_users():
    """List all admin users"""
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.role == "admin")
        )
        admins = result.scalars().all()
        
        if not admins:
            print("❌ Keine Admin-User gefunden!")
            return
        
        print(f"✅ {len(admins)} Admin-User gefunden:\n")
        for admin in admins:
            print(f"📧 {admin.email}")
            print(f"   Name: {admin.first_name} {admin.last_name}")
            print(f"   Aktiv: {'✓' if admin.is_active else '✗'}")
            print(f"   Verifiziert: {'✓' if admin.is_verified else '✗'}")
            print()


async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Admin User Management")
        print("\nVerwendung:")
        print("  python create_admin.py list")
        print("  python create_admin.py create <email> <password> [first_name] [last_name]")
        print("\nBeispiel:")
        print("  python create_admin.py create admin@example.com MySecurePass123 Admin User")
        print("  python create_admin.py list")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        await list_admin_users()
    
    elif command == "create":
        if len(sys.argv) < 4:
            print("❌ Fehler: Email und Passwort erforderlich!")
            print("Verwendung: python create_admin.py create <email> <password> [first_name] [last_name]")
            return
        
        email = sys.argv[2]
        password = sys.argv[3]
        first_name = sys.argv[4] if len(sys.argv) > 4 else "Admin"
        last_name = sys.argv[5] if len(sys.argv) > 5 else "User"
        
        await create_admin_user(email, password, first_name, last_name)
    
    else:
        print(f"❌ Unbekannter Befehl: {command}")
        print("Verfügbare Befehle: list, create")


if __name__ == "__main__":
    asyncio.run(main())
