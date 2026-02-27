#!/usr/bin/env python
"""
Start Script for TaskManager Application
This script automates the startup process
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    banner = """
    ╔═══════════════════════════════════════════╗
    ║      TASKMANAGER - Startup Script        ║
    ║   Professional Task Management System    ║
    ╚═══════════════════════════════════════════╝
    """
    print(banner)

def check_venv():
    """Check if virtual environment exists"""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found!")
        print("📌 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created!")
    return True

def activate_venv():
    """Activate virtual environment"""
    if sys.platform == "win32":
        venv_activate = Path("venv/Scripts/python.exe")
    else:
        venv_activate = Path("venv/bin/python")
    
    if venv_activate.exists():
        print(f"✅ Virtual environment found at: {venv_activate}")
        return str(venv_activate)
    else:
        print("❌ Failed to find Python executable in venv")
        sys.exit(1)

def check_database():
    """Check if database exists"""
    db_path = Path("db.sqlite3")
    if db_path.exists():
        print("✅ Database exists!")
        return True
    else:
        print("⚠️  Database not found, running migrations...")
        return False

def run_migrations(python_exe):
    """Run Django migrations"""
    print("🔄 Running database migrations...")
    subprocess.run([python_exe, "manage.py", "migrate"], check=True)
    print("✅ Migrations completed!")

def create_superuser_check(python_exe):
    """Check and create superuser if needed"""
    print("🔑 Checking for superuser...")
    try:
        subprocess.run(
            [python_exe, "manage.py", "shell", "-c", 
             "from django.contrib.auth.models import User; User.objects.get(username='admin')"],
            check=True,
            capture_output=True
        )
        print("✅ Admin user already exists!")
    except:
        print("📌 Creating admin user...")
        subprocess.run([python_exe, "create_superuser.py"], check=True)
        print("✅ Admin user created!")

def start_server(python_exe):
    """Start Django development server"""
    print("\n" + "="*50)
    print("🚀 Starting Django Development Server...")
    print("="*50)
    print("\n✅ Server is running on: http://localhost:8000")
    print("\n📝 Login Credentials:")
    print("   Username: admin")
    print("   Password: admin@123")
    print("\n💡 Press Ctrl+C to stop the server\n")
    print("="*50 + "\n")
    
    try:
        subprocess.run([python_exe, "manage.py", "runserver"], check=False)
    except KeyboardInterrupt:
        print("\n\n❌ Server stopped by user")
        sys.exit(0)

def main():
    print_banner()
    
    # Check virtual environment
    print("🔍 Checking virtual environment...")
    check_venv()
    
    # Get python executable
    python_exe = activate_venv()
    
    # Check database
    print("\n🔍 Checking database...")
    db_exists = check_database()
    if not db_exists:
        run_migrations(python_exe)
    
    # Check superuser
    print("\n🔍 Checking for admin user...")
    create_superuser_check(python_exe)
    
    # Start server
    print("\n" + "="*50)
    start_server(python_exe)

if __name__ == "__main__":
    main()
