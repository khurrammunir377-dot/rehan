import sqlite3
import os
import json
from contextlib import contextmanager

DB_DIR = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("VERCEL"):
    import shutil
    TEMP_DB = "/tmp/rehan_computers.db"
    ORIGINAL_DB = os.path.join(DB_DIR, "rehan_computers.db")
    if not os.path.exists(TEMP_DB) and os.path.exists(ORIGINAL_DB):
        shutil.copyfile(ORIGINAL_DB, TEMP_DB)
    DB_PATH = TEMP_DB
else:
    DB_PATH = os.path.join(DB_DIR, "rehan_computers.db")

@contextmanager
def get_db():
    if os.environ.get("VERCEL"):
        TEMP_DB = "/tmp/rehan_computers.db"
        ORIGINAL_DB = os.path.join(DB_DIR, "rehan_computers.db")
        if not os.path.exists(TEMP_DB) and os.path.exists(ORIGINAL_DB):
            import shutil
            shutil.copyfile(ORIGINAL_DB, TEMP_DB)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'cashier', -- admin, manager, cashier, technician
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Store settings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS store_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        # 3. Categories
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT,
            display_order INTEGER DEFAULT 0
        );
        """)

        # 4. Brands
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            logo_url TEXT,
            is_featured INTEGER DEFAULT 1
        );
        """)

        # 5. Products
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            condition TEXT NOT NULL DEFAULT 'Grade A+ Used', -- Brand New, Grade A+ Used, Refurbished
            specs TEXT, -- JSON string with cpu, ram, storage, gpu, screen, etc.
            cost_price REAL NOT NULL DEFAULT 0,
            selling_price REAL NOT NULL,
            discount_price REAL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            min_stock_alert INTEGER NOT NULL DEFAULT 2,
            warranty_period TEXT DEFAULT '1 Month Checking Warranty',
            image_url TEXT,
            gallery TEXT, -- JSON array of URLs
            is_featured INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 6. Serial Numbers (individual hardware identification)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_serials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            serial_number TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'available', -- available, sold, in_repair, defective
            sold_invoice_or_order TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 7. Orders (Online & In-store)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL DEFAULT 'online', -- online, pos, phone_whatsapp
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT,
            shipping_address TEXT NOT NULL,
            city TEXT NOT NULL DEFAULT 'Sargodha',
            payment_method TEXT NOT NULL DEFAULT 'cash_on_delivery', -- cash_on_delivery, bank_transfer, easypaisa_jazzcash, pos_cash, pos_card
            payment_status TEXT NOT NULL DEFAULT 'pending', -- pending, paid, refunded
            order_status TEXT NOT NULL DEFAULT 'new', -- new, confirmed, processing, shipped, delivered, cancelled
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0,
            shipping_fee REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            courier_name TEXT,
            courier_tracking_no TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 8. Order items
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
            product_title TEXT NOT NULL,
            sku TEXT,
            unit_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            serial_number TEXT
        );
        """)

        # 9. POS Sales (In-Store Counter Checkout)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            cashier_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            cashier_name TEXT,
            customer_name TEXT DEFAULT 'Walk-in Customer',
            customer_phone TEXT,
            payment_method TEXT NOT NULL DEFAULT 'cash', -- cash, jazzcash_easypaisa, bank_transfer, split
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            amount_paid REAL NOT NULL,
            change_returned REAL DEFAULT 0,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 10. POS Sale items
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL REFERENCES pos_sales(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
            product_title TEXT NOT NULL,
            unit_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            serial_number TEXT
        );
        """)

        # 11. Repair Tickets (RMA / Workshop Center)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS repair_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT,
            device_brand TEXT NOT NULL,
            device_model TEXT NOT NULL,
            serial_or_password TEXT,
            problem_description TEXT NOT NULL,
            accessories_received TEXT, -- Charger, Bag, None, etc.
            assigned_technician_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            technician_name TEXT,
            estimated_cost REAL DEFAULT 0,
            final_cost REAL DEFAULT 0,
            advance_paid REAL DEFAULT 0,
            parts_cost REAL DEFAULT 0,
            parts_used TEXT,
            status TEXT NOT NULL DEFAULT 'received', -- received, diagnosing, awaiting_parts, repairing, ready_for_pickup, delivered, cancelled
            technician_notes TEXT,
            customer_notified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        );
        """)

        # 12. Trade-in / Sell Used Laptop Requests
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_in_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_code TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            device_brand TEXT NOT NULL,
            device_model TEXT NOT NULL,
            specs_details TEXT NOT NULL,
            condition_grade TEXT NOT NULL,
            customer_expected_price REAL,
            estimated_offer_price REAL,
            status TEXT NOT NULL DEFAULT 'pending', -- pending, under_review, accepted, rejected, completed
            admin_notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 13. Suppliers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT NOT NULL,
            city TEXT,
            address TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 14. Purchases (Restocking / Stock In)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_code TEXT UNIQUE NOT NULL,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
            supplier_name TEXT,
            supplier_invoice_no TEXT,
            total_amount REAL NOT NULL,
            paid_amount REAL NOT NULL DEFAULT 0,
            payment_status TEXT DEFAULT 'paid', -- paid, partial, unpaid
            purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        );
        """)

        # 15. Purchase items
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
            product_title TEXT NOT NULL,
            unit_cost REAL NOT NULL,
            quantity INTEGER NOT NULL,
            total_cost REAL NOT NULL
        );
        """)

        # 16. Expenses
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL, -- Shop Rent, Electricity Bill, Staff Salaries, Courier Charges, Refreshments, Maintenance, Miscellaneous
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            payment_method TEXT DEFAULT 'cash',
            expense_date DATE DEFAULT (DATE('now')),
            recorded_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            recorded_by_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 17. Customers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT,
            city TEXT DEFAULT 'Sargodha',
            address TEXT,
            total_spent REAL DEFAULT 0,
            orders_count INTEGER DEFAULT 0,
            repairs_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 18. Activity Logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 19. Visitor Logs (Detailed traffic analytics)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            session_id TEXT,
            page_url TEXT NOT NULL DEFAULT '/',
            page_title TEXT,
            referrer TEXT,
            user_agent TEXT,
            device_type TEXT DEFAULT 'Desktop', -- Desktop, Mobile, Tablet
            browser TEXT,
            os TEXT,
            city TEXT DEFAULT 'Sargodha',
            country TEXT DEFAULT 'Pakistan',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 20. Blocked IPs & Security Rules (Traffic Control)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocked_ips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE NOT NULL,
            reason TEXT,
            is_blocked INTEGER DEFAULT 1,
            blocked_by TEXT DEFAULT 'Admin',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 21. Traffic & Storefront Controls
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_controls (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

def dict_from_row(row):
    if row is None:
        return None
    d = dict(row)
    if 'specs' in d and isinstance(d['specs'], str):
        try:
            d['specs'] = json.loads(d['specs'])
        except Exception:
            pass
    if 'gallery' in d and isinstance(d['gallery'], str):
        try:
            d['gallery'] = json.loads(d['gallery'])
        except Exception:
            pass
    return d
