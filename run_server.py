"""
Rehan Computers - Full-Stack E-Commerce & ERP Server Runner
Shop #96, 1st Floor, Trust Plaza, Sargodha, Punjab, Pakistan
Phone / WhatsApp: 0300-9607829
"""

import sys
import os
import uvicorn

# Ensure the root directory is on the python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database import init_db
from backend.seed_data import seed_database

def main():
    print("=" * 70)
    print("  REHAN LAPTOP & COMPUTER - E-COMMERCE & FULL ERP SYSTEM")
    print("  Shop #96, 1st Floor, Trust Plaza, Sargodha, Pakistan")
    print("  Contact & WhatsApp: 0300-9607829")
    print("=" * 70)
    
    print("\n[*] Initializing SQLite Database & Seeding Hardware Catalog...")
    init_db()
    seed_database()

    port = 8000
    host = "127.0.0.1"

    print("\n[+] Server is starting up successfully!")
    print(f"  --> Customer E-Commerce Store: http://{host}:{port}/")
    print(f"  --> Business ERP & POS Portal:  http://{host}:{port}/admin")
    print(f"  --> Interactive Swagger API:    http://{host}:{port}/docs")
    print("\n[*] Default ERP Credentials:")
    print("    Admin / Owner:      admin   / admin123")
    print("    POS Cashier:        cashier / cashier123")
    print("    Repair Technician:  tech    / tech123")
    print("=" * 70)
    print("\nPress Ctrl+C to terminate the server.\n")

    uvicorn.run("backend.main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()
