import io
import csv
import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, Response
from backend.database import get_db, DB_PATH
from backend.auth import get_current_user, require_role

router = APIRouter(prefix="/api/erp/settings", tags=["ERP Store Settings & Backup"])

@router.get("")
def get_all_settings(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM store_settings")
        return {row[0]: row[1] for row in cursor.fetchall()}

@router.put("", dependencies=[Depends(require_role(["admin"]))])
def update_settings(settings_dict: dict, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        for k, v in settings_dict.items():
            cursor.execute("INSERT OR REPLACE INTO store_settings (key, value) VALUES (?, ?)", (k, str(v)))

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'Settings Updated', 'Updated store business configurations')
        """, (current_user["id"], current_user["username"]))

        return {"message": "Store settings updated successfully"}

@router.get("/backup-database", dependencies=[Depends(require_role(["admin"]))])
def backup_database(current_user: dict = Depends(get_current_user)):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database file not found")
    return FileResponse(
        path=DB_PATH,
        filename="rehan_computers_backup.db",
        media_type="application/octet-stream"
    )

@router.get("/export/products-csv", dependencies=[Depends(require_role(["admin", "manager"]))])
def export_products_csv(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.sku, p.title, b.name as brand, c.name as category,
                   p.condition, p.cost_price, p.selling_price, p.stock_quantity, p.warranty_period
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.id ASC
        """)
        rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "SKU", "Title", "Brand", "Category", "Condition", "Cost (PKR)", "Price (PKR)", "Stock", "Warranty"])
        for r in rows:
            writer.writerow(list(r))

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=rehan_computers_inventory.csv"}
        )

@router.get("/export/sales-csv", dependencies=[Depends(require_role(["admin", "manager"]))])
def export_sales_csv(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 'POS' as type, invoice_number as code, customer_name, customer_phone,
                   payment_method, total_amount, created_at
            FROM pos_sales
            UNION ALL
            SELECT 'Online' as type, order_number as code, customer_name, customer_phone,
                   payment_method, total_amount, created_at
            FROM orders
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Sale Type", "Invoice/Order #", "Customer Name", "Phone", "Payment Method", "Total (PKR)", "Date/Time"])
        for r in rows:
            writer.writerow(list(r))

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=rehan_computers_sales_report.csv"}
        )

@router.get("/activity-logs", dependencies=[Depends(require_role(["admin"]))])
def list_activity_logs(limit: int = 100, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
