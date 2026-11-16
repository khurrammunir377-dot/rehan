from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from backend.database import get_db, dict_from_row
from backend.auth import get_current_user

router = APIRouter(prefix="/api/erp/orders", tags=["ERP Orders Management"])

@router.get("")
def list_orders(
    status: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM orders WHERE 1=1"
        params = []
        if status:
            query += " AND order_status = ?"
            params.append(status)
        if source:
            query += " AND source = ?"
            params.append(source)
        if search:
            query += " AND (order_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s])

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        orders = [dict_from_row(r) for r in cursor.fetchall()]

        for o in orders:
            cursor.execute("SELECT product_title, sku, unit_price, quantity, total_price, serial_number FROM order_items WHERE order_id = ?", (o["id"],))
            o["items"] = [dict(it) for it in cursor.fetchall()]

        return orders

@router.get("/{order_id}")
def get_order_detail(order_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        order = dict_from_row(row)
        cursor.execute("SELECT product_title, sku, unit_price, quantity, total_price, serial_number FROM order_items WHERE order_id = ?", (order["id"],))
        order["items"] = [dict(it) for it in cursor.fetchall()]
        return order

@router.put("/{order_id}/status")
def update_order_status(order_id: int, status_update: dict, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, order_number, order_status FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        fields = []
        values = []

        if "order_status" in status_update:
            fields.append("order_status = ?")
            values.append(status_update["order_status"])
        if "payment_status" in status_update:
            fields.append("payment_status = ?")
            values.append(status_update["payment_status"])
        if "courier_name" in status_update:
            fields.append("courier_name = ?")
            values.append(status_update["courier_name"])
        if "courier_tracking_no" in status_update:
            fields.append("courier_tracking_no = ?")
            values.append(status_update["courier_tracking_no"])
        if "notes" in status_update:
            fields.append("notes = ?")
            values.append(status_update["notes"])

        if not fields:
            return {"message": "No changes supplied"}

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(order_id)

        sql = f"UPDATE orders SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, values)

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'Order Updated', ?)
        """, (current_user["id"], current_user["username"], f"Order {order['order_number']} status changed to {status_update.get('order_status', 'updated')}"))

        return {"message": "Order status updated successfully"}
