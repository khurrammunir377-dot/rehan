import random
import time
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from backend.database import get_db, dict_from_row
from backend.auth import get_current_user
from backend.models import POSSaleCreate

router = APIRouter(prefix="/api/erp/pos", tags=["ERP Point of Sale"])

@router.get("/search")
def pos_search_products(
    q: str = "",
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    q_clean = q.strip()
    cat_clean = (category or "").strip().lower()

    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT p.id, p.title, p.sku, p.selling_price, p.discount_price, p.stock_quantity,
                   p.condition, p.image_url, b.name as brand_name, c.slug as category_slug, c.name as category_name
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1 AND p.stock_quantity > 0
        """
        params = []

        if q_clean:
            query += " AND (p.title LIKE ? OR p.sku LIKE ? OR b.name LIKE ? OR p.id = ?)"
            term = f"%{q_clean}%"
            params.extend([term, term, term, int(q_clean) if q_clean.isdigit() else -1])

        if cat_clean:
            if cat_clean in ("laptops", "laptop"):
                query += " AND (c.slug IN ('laptops', 'gaming-laptops') OR ((p.title LIKE '%laptop%' OR p.title LIKE '%notebook%' OR p.title LIKE '%elitebook%' OR p.title LIKE '%thinkpad%' OR p.title LIKE '%macbook%' OR p.title LIKE '%latitude%' OR p.title LIKE '%precision%') AND c.slug NOT IN ('accessories', 'parts-upgrades')))"
            elif cat_clean in ("cpu", "desktop", "cpu-desktops", "desktop-computers"):
                query += " AND (c.slug IN ('desktop-computers', 'cpu-desktops') OR p.title LIKE '%desktop%' OR p.title LIKE '%cpu%' OR p.title LIKE '%tower%' OR p.title LIKE '%gaming pc%' OR p.title LIKE '%prodesk%' OR p.title LIKE '%optiplex%' OR p.title LIKE '%thinkcentre%')"
            elif cat_clean in ("led", "monitor", "monitors", "led-monitors"):
                query += " AND (c.slug = 'led-monitors' OR ((p.title LIKE '%monitor%' OR p.title LIKE '%curved%' OR p.title LIKE '%led%') AND c.slug NOT IN ('accessories', 'parts-upgrades')))"
            elif cat_clean in ("accessories", "accessory"):
                query += " AND (c.slug = 'accessories' OR p.title LIKE '%mouse%' OR p.title LIKE '%keyboard%' OR p.title LIKE '%headset%' OR p.title LIKE '%webcam%' OR p.title LIKE '%dock%' OR p.title LIKE '%backpack%' OR p.title LIKE '%pad%' OR p.title LIKE '%clean%')"
            elif cat_clean in ("parts-upgrades", "storage-ram", "storage", "ram"):
                query += " AND (c.slug = 'parts-upgrades' OR p.title LIKE '%ssd%' OR p.title LIKE '%ram%' OR p.title LIKE '%nvme%' OR p.title LIKE '%charger%' OR p.title LIKE '%memory%')"
            else:
                query += " AND c.slug = ?"
                params.append(cat_clean)

        query += " ORDER BY p.id DESC LIMIT 100"
        cursor.execute(query, params)
        return [dict_from_row(r) for r in cursor.fetchall()]

@router.post("/checkout")
def pos_checkout(sale_in: POSSaleCreate, current_user: dict = Depends(get_current_user)):
    if not sale_in.items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty")

    with get_db() as conn:
        cursor = conn.cursor()

        # Calculate totals & check stock
        subtotal = 0.0
        validated_items = []
        for item in sale_in.items:
            cursor.execute("SELECT id, title, sku, stock_quantity FROM products WHERE id = ?", (item.product_id,))
            p = cursor.fetchone()
            if not p:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            if p["stock_quantity"] < item.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {p['title']}")
            
            line_total = item.unit_price * item.quantity
            subtotal += line_total
            validated_items.append({
                "product_id": p["id"],
                "product_title": p["title"],
                "unit_price": item.unit_price,
                "quantity": item.quantity,
                "total_price": line_total,
                "serial_number": item.serial_number
            })

            # Decrement inventory
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?", (item.quantity, item.product_id))

            # If serial number was provided, mark as sold
            if item.serial_number:
                cursor.execute("""
                    UPDATE product_serials SET status = 'sold'
                    WHERE serial_number = ? AND product_id = ?
                """, (item.serial_number, item.product_id))

        total_amount = max(0.0, subtotal - sale_in.discount + sale_in.tax)
        change_returned = max(0.0, sale_in.amount_paid - total_amount)

        # Generate Invoice Number RC-POS-XXXX
        invoice_number = f"RC-POS-{int(time.time()) % 100000}{random.randint(10, 99)}"

        cursor.execute("""
            INSERT INTO pos_sales (
                invoice_number, cashier_id, cashier_name, customer_name, customer_phone,
                payment_method, subtotal, discount, tax, total_amount,
                amount_paid, change_returned, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_number, current_user["id"], current_user["full_name"],
            sale_in.customer_name or "Walk-in Customer", sale_in.customer_phone,
            sale_in.payment_method, subtotal, sale_in.discount, sale_in.tax,
            total_amount, sale_in.amount_paid, change_returned, sale_in.notes
        ))
        sale_id = cursor.lastrowid

        # Insert items
        for vi in validated_items:
            cursor.execute("""
                INSERT INTO pos_sale_items (sale_id, product_id, product_title, unit_price, quantity, total_price, serial_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sale_id, vi["product_id"], vi["product_title"], vi["unit_price"], vi["quantity"], vi["total_price"], vi["serial_number"]))

        # Update customer if phone provided
        if sale_in.customer_phone:
            cursor.execute("SELECT id FROM customers WHERE phone = ?", (sale_in.customer_phone,))
            c_row = cursor.fetchone()
            if c_row:
                cursor.execute("UPDATE customers SET total_spent = total_spent + ?, orders_count = orders_count + 1 WHERE id = ?", (total_amount, c_row["id"]))
            else:
                cursor.execute("""
                    INSERT INTO customers (name, phone, city, address, total_spent, orders_count)
                    VALUES (?, ?, 'Sargodha', 'Walk-in Shop #96', ?, 1)
                """, (sale_in.customer_name or "Walk-in Customer", sale_in.customer_phone, total_amount))

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'POS Sale Completed', ?)
        """, (current_user["id"], current_user["username"], f"Invoice {invoice_number} generated for {total_amount:,.0f} PKR ({sale_in.payment_method})"))

        return {
            "success": True,
            "sale_id": sale_id,
            "invoice_number": invoice_number,
            "subtotal": subtotal,
            "discount": sale_in.discount,
            "tax": sale_in.tax,
            "total_amount": total_amount,
            "amount_paid": sale_in.amount_paid,
            "change_returned": change_returned,
            "cashier_name": current_user["full_name"],
            "items": validated_items,
            "customer_name": sale_in.customer_name,
            "customer_phone": sale_in.customer_phone,
            "payment_method": sale_in.payment_method
        }

@router.get("/sales")
def get_pos_sales(limit: int = 50, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pos_sales ORDER BY id DESC LIMIT ?", (limit,))
        sales = [dict_from_row(r) for r in cursor.fetchall()]
        for s in sales:
            cursor.execute("SELECT product_title, unit_price, quantity, total_price, serial_number FROM pos_sale_items WHERE sale_id = ?", (s["id"],))
            s["items"] = [dict(it) for it in cursor.fetchall()]
        return sales

@router.get("/sales/{sale_id_or_inv}")
def get_single_pos_sale(sale_id_or_inv: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        if sale_id_or_inv.isdigit():
            cursor.execute("SELECT * FROM pos_sales WHERE id = ?", (int(sale_id_or_inv),))
        else:
            cursor.execute("SELECT * FROM pos_sales WHERE invoice_number = ?", (sale_id_or_inv,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Sale invoice not found")
        sale = dict_from_row(row)
        cursor.execute("SELECT product_title, unit_price, quantity, total_price, serial_number FROM pos_sale_items WHERE sale_id = ?", (sale["id"],))
        sale["items"] = [dict(it) for it in cursor.fetchall()]
        return sale
