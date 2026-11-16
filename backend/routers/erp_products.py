import json
import re
import os
import base64
import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from backend.database import get_db, dict_from_row
from backend.auth import get_current_user, require_role
from backend.models import ProductCreate, ProductUpdate, StockAdjustIn, ProductPricePicsUpdate

router = APIRouter(prefix="/api/erp/products", tags=["ERP Products & Inventory"])

if os.environ.get("VERCEL"):
    UPLOAD_DIR = "/tmp/uploads"
else:
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "public", "uploads")

try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception:
    pass

@router.post("/upload-image", dependencies=[Depends(require_role(["admin", "manager"]))])
def upload_image(payload: dict, current_user: dict = Depends(get_current_user)):
    """Uploads a base64 encoded image to frontend/public/uploads and returns the static URL."""
    data_base64 = payload.get("data_base64", "")
    filename = payload.get("filename", "upload.jpg")
    
    if not data_base64:
        raise HTTPException(status_code=400, detail="No image data provided")

    # If it contains header data:image/png;base64,...
    if "," in data_base64:
        header, base64_str = data_base64.split(",", 1)
    else:
        base64_str = data_base64

    try:
        image_bytes = base64.b64decode(base64_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {str(e)}")

    # Extract extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        ext = ".jpg"

    safe_name = f"rehan_{uuid.uuid4().hex[:10]}{ext}"
    target_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(target_path, "wb") as f:
        f.write(image_bytes)

    public_url = f"/public/uploads/{safe_name}"

    return {
        "success": True,
        "filename": safe_name,
        "url": public_url,
        "message": "Image uploaded successfully!"
    }

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text)

@router.get("")
def list_inventory_products(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    brand_id: Optional[int] = None,
    low_stock: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT p.*, b.name as brand_name, c.name as category_name,
                   (SELECT COUNT(*) FROM product_serials WHERE product_id = p.id AND status = 'available') as available_serials_count
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (p.title LIKE ? OR p.sku LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s])
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        if brand_id:
            query += " AND p.brand_id = ?"
            params.append(brand_id)
        if low_stock:
            query += " AND p.stock_quantity <= p.min_stock_alert"

        query += " ORDER BY p.id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict_from_row(r) for r in rows]

@router.post("", dependencies=[Depends(require_role(["admin", "manager"]))])
def create_product(prod: ProductCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        slug = slugify(prod.title)
        
        # Ensure unique slug
        cursor.execute("SELECT id FROM products WHERE slug = ?", (slug,))
        if cursor.fetchone():
            slug = f"{slug}-{int(hash(prod.title)) % 10000}"

        sku = prod.sku or f"RC-{slug[:6].upper()}-{int(hash(prod.title)) % 1000}"
        specs_json = json.dumps(prod.specs or {})
        gallery_json = json.dumps(prod.gallery or [])

        cursor.execute("""
            INSERT INTO products (
                title, slug, sku, brand_id, category_id, condition, specs,
                cost_price, selling_price, discount_price, stock_quantity, min_stock_alert,
                warranty_period, image_url, gallery, is_featured, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prod.title, slug, sku, prod.brand_id, prod.category_id, prod.condition, specs_json,
            prod.cost_price, prod.selling_price, prod.discount_price, prod.stock_quantity,
            prod.min_stock_alert, prod.warranty_period, prod.image_url, gallery_json,
            1 if prod.is_featured else 0, 1 if prod.is_active else 0
        ))
        product_id = cursor.lastrowid

        # Insert serials if provided
        if prod.serial_numbers:
            for s in prod.serial_numbers:
                s_clean = s.strip()
                if s_clean:
                    cursor.execute("""
                        INSERT OR IGNORE INTO product_serials (product_id, serial_number, status)
                        VALUES (?, ?, 'available')
                    """, (product_id, s_clean))

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'Product Added', ?)
        """, (current_user["id"], current_user["username"], f"Added product: {prod.title} (SKU: {sku})"))

        return {"message": "Product created successfully", "product_id": product_id}

@router.put("/{product_id}", dependencies=[Depends(require_role(["admin", "manager"]))])
def update_product(product_id: int, prod: ProductUpdate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM products WHERE id = ?", (product_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")

        fields = []
        values = []

        if prod.title is not None:
            fields.append("title = ?")
            values.append(prod.title)
        if prod.brand_id is not None:
            fields.append("brand_id = ?")
            values.append(prod.brand_id)
        if prod.category_id is not None:
            fields.append("category_id = ?")
            values.append(prod.category_id)
        if prod.condition is not None:
            fields.append("condition = ?")
            values.append(prod.condition)
        if prod.specs is not None:
            fields.append("specs = ?")
            values.append(json.dumps(prod.specs))
        if prod.cost_price is not None:
            fields.append("cost_price = ?")
            values.append(prod.cost_price)
        if prod.selling_price is not None:
            fields.append("selling_price = ?")
            values.append(prod.selling_price)
        if prod.discount_price is not None:
            fields.append("discount_price = ?")
            values.append(prod.discount_price)
        if prod.stock_quantity is not None:
            fields.append("stock_quantity = ?")
            values.append(prod.stock_quantity)
        if prod.min_stock_alert is not None:
            fields.append("min_stock_alert = ?")
            values.append(prod.min_stock_alert)
        if prod.warranty_period is not None:
            fields.append("warranty_period = ?")
            values.append(prod.warranty_period)
        if prod.image_url is not None:
            fields.append("image_url = ?")
            values.append(prod.image_url)
        if prod.gallery is not None:
            fields.append("gallery = ?")
            values.append(json.dumps(prod.gallery))
        if prod.is_featured is not None:
            fields.append("is_featured = ?")
            values.append(1 if prod.is_featured else 0)
        if prod.is_active is not None:
            fields.append("is_active = ?")
            values.append(1 if prod.is_active else 0)

        if not fields:
            return {"message": "No changes supplied"}

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(product_id)

        sql = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, values)

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'Product Updated', ?)
        """, (current_user["id"], current_user["username"], f"Updated product ID: {product_id}"))

        return {"message": "Product updated successfully"}

@router.put("/{product_id}/price-pics", dependencies=[Depends(require_role(["admin", "manager"]))])
def update_product_price_and_pics(product_id: int, payload: ProductPricePicsUpdate, current_user: dict = Depends(get_current_user)):
    """Fast dedicated endpoint for updating selling price, cost price, discount, primary photo & gallery."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, selling_price FROM products WHERE id = ?", (product_id,))
        p = cursor.fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Product not found")

        fields = ["selling_price = ?"]
        values = [payload.selling_price]

        if payload.cost_price is not None:
            fields.append("cost_price = ?")
            values.append(payload.cost_price)

        if payload.discount_price is not None:
            fields.append("discount_price = ?")
            values.append(payload.discount_price)

        if payload.image_url is not None:
            fields.append("image_url = ?")
            values.append(payload.image_url)

        if payload.gallery is not None:
            fields.append("gallery = ?")
            values.append(json.dumps(payload.gallery))

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(product_id)

        sql = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, values)

        log_msg = f"{p['title']}: Price set to PKR {payload.selling_price:,.0f}"
        if payload.image_url:
            log_msg += " (Updated photo)"

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'Price & Picture Updated', ?)
        """, (current_user["id"], current_user["username"], log_msg))

        return {
            "success": True,
            "message": f"Updated price & photos for {p['title']} successfully!",
            "selling_price": payload.selling_price,
            "image_url": payload.image_url
        }

@router.post("/{product_id}/adjust-stock")
def adjust_stock(product_id: int, adj: StockAdjustIn, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, stock_quantity FROM products WHERE id = ?", (product_id,))
        p = cursor.fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Product not found")

        new_qty = max(0, p["stock_quantity"] + adj.quantity_change)
        cursor.execute("UPDATE products SET stock_quantity = ? WHERE id = ?", (new_qty, product_id))

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'Stock Adjusted', ?)
        """, (current_user["id"], current_user["username"], f"{p['title']}: {adj.quantity_change:+d} units (Reason: {adj.reason}) -> New Qty: {new_qty}"))

        return {"message": "Stock adjusted successfully", "new_quantity": new_qty}

@router.get("/{product_id}/serials")
def get_product_serials(product_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_serials WHERE product_id = ? ORDER BY id DESC", (product_id,))
        return [dict(r) for r in cursor.fetchall()]

@router.post("/{product_id}/serials")
def add_product_serial(product_id: int, serial_data: dict, current_user: dict = Depends(get_current_user)):
    serial_no = serial_data.get("serial_number", "").strip()
    if not serial_no:
        raise HTTPException(status_code=400, detail="Serial number is required")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO product_serials (product_id, serial_number, status) VALUES (?, ?, 'available')", (product_id, serial_no))
        return {"message": "Serial number registered"}
