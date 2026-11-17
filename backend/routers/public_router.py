import random
import time
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.database import get_db, dict_from_row
from backend.models import PublicOrderCreate, RepairTicketCreate, TradeInCreate

router = APIRouter(prefix="/api/public", tags=["Public E-Commerce"])

@router.get("/store-info")
def get_store_info():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM store_settings")
        settings = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Add quick stats
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        settings["total_products_count"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM brands")
        settings["brands_count"] = cursor.fetchone()[0]
        
        return settings

@router.get("/categories")
def get_categories():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, slug, description, icon FROM categories ORDER BY display_order ASC")
        return [dict(r) for r in cursor.fetchall()]

@router.get("/brands")
def get_brands():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, slug, logo_url FROM brands ORDER BY id ASC")
        return [dict(r) for r in cursor.fetchall()]

@router.get("/products")
def get_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    condition: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    sort: Optional[str] = "newest", # newest, price_low, price_high, title_asc
    limit: int = 50,
    offset: int = 0
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT p.*, b.name as brand_name, b.slug as brand_slug, c.name as category_name, c.slug as category_slug
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
        """
        params = []

        if category:
            query += " AND (c.slug = ? OR c.name = ?)"
            params.extend([category, category])
        if brand:
            query += " AND (b.slug = ? OR b.name = ?)"
            params.extend([brand, brand])
        if condition:
            query += " AND p.condition = ?"
            params.append(condition)
        if search:
            query += " AND (p.title LIKE ? OR p.sku LIKE ? OR p.specs LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])
        if min_price is not None:
            query += " AND (CASE WHEN p.discount_price IS NOT NULL AND p.discount_price > 0 THEN p.discount_price ELSE p.selling_price END) >= ?"
            params.append(min_price)
        if max_price is not None:
            query += " AND (CASE WHEN p.discount_price IS NOT NULL AND p.discount_price > 0 THEN p.discount_price ELSE p.selling_price END) <= ?"
            params.append(max_price)
        if featured is not None and featured:
            query += " AND p.is_featured = 1"

        if sort == "price_low":
            query += " ORDER BY (CASE WHEN p.discount_price IS NOT NULL AND p.discount_price > 0 THEN p.discount_price ELSE p.selling_price END) ASC"
        elif sort == "price_high":
            query += " ORDER BY (CASE WHEN p.discount_price IS NOT NULL AND p.discount_price > 0 THEN p.discount_price ELSE p.selling_price END) DESC"
        elif sort == "title_asc":
            query += " ORDER BY p.title ASC"
        else:
            query += " ORDER BY COALESCE(c.display_order, 99) ASC, p.is_featured DESC, p.id ASC"

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict_from_row(r) for r in rows]

@router.get("/products/{slug_or_id}")
def get_product_detail(slug_or_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        if slug_or_id.isdigit():
            cursor.execute("""
                SELECT p.*, b.name as brand_name, c.name as category_name
                FROM products p
                LEFT JOIN brands b ON p.brand_id = b.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = ? AND p.is_active = 1
            """, (int(slug_or_id),))
        else:
            cursor.execute("""
                SELECT p.*, b.name as brand_name, c.name as category_name
                FROM products p
                LEFT JOIN brands b ON p.brand_id = b.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.slug = ? AND p.is_active = 1
            """, (slug_or_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        
        prod = dict_from_row(row)

        # Also get related products from same category
        cursor.execute("""
            SELECT id, title, slug, selling_price, discount_price, condition, image_url
            FROM products
            WHERE category_id = ? AND id != ? AND is_active = 1
            LIMIT 4
        """, (prod["category_id"], prod["id"]))
        prod["related_products"] = [dict_from_row(r) for r in cursor.fetchall()]

        return prod

@router.post("/orders")
def place_order(order_in: PublicOrderCreate):
    if not order_in.items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Calculate subtotal and verify stock
        subtotal = 0.0
        validated_items = []
        for item in order_in.items:
            cursor.execute("SELECT id, title, sku, selling_price, discount_price, stock_quantity FROM products WHERE id = ?", (item.product_id,))
            p = cursor.fetchone()
            if not p:
                raise HTTPException(status_code=400, detail=f"Product ID {item.product_id} not found")
            if p["stock_quantity"] < item.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {p['title']} (Available: {p['stock_quantity']})")
            
            unit_price = p["discount_price"] if p["discount_price"] and p["discount_price"] > 0 else p["selling_price"]
            item_total = unit_price * item.quantity
            subtotal += item_total
            validated_items.append({
                "product_id": p["id"],
                "product_title": p["title"],
                "sku": p["sku"],
                "unit_price": unit_price,
                "quantity": item.quantity,
                "total_price": item_total
            })
            
            # Decrement stock
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?", (item.quantity, item.product_id))

        # Shipping logic (Free above 25,000 PKR or in Sargodha special)
        shipping_fee = 0.0 if subtotal >= 25000 or "sargodha" in order_in.city.lower() else 300.0
        total_amount = subtotal + shipping_fee

        # Order Number generator (RC-ORD-XXXX)
        timestamp_part = int(time.time()) % 100000
        rand_part = random.randint(10, 99)
        order_number = f"RC-ORD-{timestamp_part}{rand_part}"

        cursor.execute("""
            INSERT INTO orders (
                order_number, source, customer_name, customer_phone, customer_email,
                shipping_address, city, payment_method, payment_status, order_status,
                subtotal, discount, shipping_fee, total_amount, notes
            ) VALUES (?, 'online', ?, ?, ?, ?, ?, ?, 'pending', 'new', ?, 0, ?, ?, ?)
        """, (
            order_number, order_in.customer_name, order_in.customer_phone, order_in.customer_email,
            order_in.shipping_address, order_in.city, order_in.payment_method,
            subtotal, shipping_fee, total_amount, order_in.notes
        ))
        order_id = cursor.lastrowid

        # Insert items
        for vi in validated_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, product_title, sku, unit_price, quantity, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_id, vi["product_id"], vi["product_title"], vi["sku"], vi["unit_price"], vi["quantity"], vi["total_price"]))

        # Update or create customer
        cursor.execute("SELECT id, orders_count, total_spent FROM customers WHERE phone = ?", (order_in.customer_phone,))
        cust = cursor.fetchone()
        if cust:
            cursor.execute("""
                UPDATE customers
                SET orders_count = orders_count + 1, total_spent = total_spent + ?, city = ?, address = ?
                WHERE id = ?
            """, (total_amount, order_in.city, order_in.shipping_address, cust["id"]))
        else:
            cursor.execute("""
                INSERT INTO customers (name, phone, email, city, address, total_spent, orders_count, repairs_count)
                VALUES (?, ?, ?, ?, ?, ?, 1, 0)
            """, (order_in.customer_name, order_in.customer_phone, order_in.customer_email, order_in.city, order_in.shipping_address, total_amount))

        return {
            "success": True,
            "order_number": order_number,
            "total_amount": total_amount,
            "subtotal": subtotal,
            "shipping_fee": shipping_fee,
            "message": "Order placed successfully! We will contact you at your phone number for dispatch confirmation."
        }

@router.get("/orders/track/{tracking_key}")
def track_order(tracking_key: str):
    key = tracking_key.strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM orders
            WHERE order_number = ? OR customer_phone = ? OR courier_tracking_no = ?
            ORDER BY id DESC LIMIT 5
        """, (key, key, key))
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No orders found matching this order number or phone.")
        
        results = []
        for r in rows:
            order = dict_from_row(r)
            cursor.execute("SELECT product_title, sku, unit_price, quantity, total_price FROM order_items WHERE order_id = ?", (order["id"],))
            order["items"] = [dict(it) for it in cursor.fetchall()]
            results.append(order)

        return results

@router.post("/repairs")
def submit_repair_request(rep: RepairTicketCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Ticket number RC-REP-XXXX
        t_part = int(time.time()) % 100000
        r_part = random.randint(10, 99)
        ticket_number = f"RC-REP-{t_part}{r_part}"

        cursor.execute("""
            INSERT INTO repair_tickets (
                ticket_number, customer_name, customer_phone, customer_email,
                device_brand, device_model, serial_or_password, problem_description,
                accessories_received, estimated_cost, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'received')
        """, (
            ticket_number, rep.customer_name, rep.customer_phone, rep.customer_email,
            rep.device_brand, rep.device_model, rep.serial_or_password,
            rep.problem_description, rep.accessories_received or "None", rep.estimated_cost
        ))

        # Update customer table
        cursor.execute("SELECT id FROM customers WHERE phone = ?", (rep.customer_phone,))
        cust = cursor.fetchone()
        if cust:
            cursor.execute("UPDATE customers SET repairs_count = repairs_count + 1 WHERE id = ?", (cust["id"],))
        else:
            cursor.execute("""
                INSERT INTO customers (name, phone, email, city, address, total_spent, orders_count, repairs_count)
                VALUES (?, ?, ?, 'Sargodha', 'Shop #96 Walk-in / Online', 0, 0, 1)
            """, (rep.customer_name, rep.customer_phone, rep.customer_email))

        return {
            "success": True,
            "ticket_number": ticket_number,
            "message": f"Repair request registered! Your tracking ticket is {ticket_number}. Bring your machine to Shop #96, 1st Floor, Trust Plaza, Sargodha or contact 0300-9607829."
        }

@router.get("/repairs/track/{tracking_key}")
def track_repair(tracking_key: str):
    key = tracking_key.strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ticket_number, customer_name, device_brand, device_model,
                   problem_description, accessories_received, estimated_cost, final_cost,
                   advance_paid, status, technician_notes, created_at, completed_at
            FROM repair_tickets
            WHERE ticket_number = ? OR customer_phone = ?
            ORDER BY id DESC LIMIT 5
        """, (key, key))
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No repair tickets found matching this ticket number or phone.")
        return [dict_from_row(r) for r in rows]

@router.post("/trade-in")
def submit_trade_in(req: TradeInCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        t_part = int(time.time()) % 100000
        request_code = f"RC-TRD-{t_part}"
        
        cursor.execute("""
            INSERT INTO trade_in_requests (
                request_code, customer_name, customer_phone, device_brand,
                device_model, specs_details, condition_grade, customer_expected_price, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (
            request_code, req.customer_name, req.customer_phone, req.device_brand,
            req.device_model, req.specs_details, req.condition_grade, req.customer_expected_price
        ))

        return {
            "success": True,
            "request_code": request_code,
            "message": f"Your trade-in quote request has been registered with reference {request_code}! Our valuation team at Trust Plaza Sargodha will review and call you shortly."
        }
