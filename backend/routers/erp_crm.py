from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from backend.database import get_db, dict_from_row
from backend.auth import get_current_user

router = APIRouter(prefix="/api/erp/crm", tags=["ERP CRM & Customers"])

@router.get("/customers")
def list_customers(
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        if search:
            s = f"%{search}%"
            cursor.execute("""
                SELECT * FROM customers
                WHERE name LIKE ? OR phone LIKE ? OR city LIKE ?
                ORDER BY total_spent DESC
            """, (s, s, s))
        else:
            cursor.execute("SELECT * FROM customers ORDER BY total_spent DESC LIMIT 100")
        return [dict_from_row(r) for r in cursor.fetchall()]

@router.get("/customers/{customer_id}")
def get_customer_history(customer_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        cust = cursor.fetchone()
        if not cust:
            raise HTTPException(status_code=404, detail="Customer not found")
        data = dict_from_row(cust)

        # Get their orders
        cursor.execute("SELECT * FROM orders WHERE customer_phone = ? ORDER BY id DESC", (data["phone"],))
        data["orders"] = [dict_from_row(r) for r in cursor.fetchall()]

        # Get their POS sales
        cursor.execute("SELECT * FROM pos_sales WHERE customer_phone = ? ORDER BY id DESC", (data["phone"],))
        data["pos_sales"] = [dict_from_row(r) for r in cursor.fetchall()]

        # Get their repairs
        cursor.execute("SELECT * FROM repair_tickets WHERE customer_phone = ? ORDER BY id DESC", (data["phone"],))
        data["repairs"] = [dict_from_row(r) for r in cursor.fetchall()]

        return data

@router.get("/trade-ins")
def list_trade_ins(status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM trade_in_requests WHERE status = ? ORDER BY id DESC", (status,))
        else:
            cursor.execute("SELECT * FROM trade_in_requests ORDER BY id DESC")
        return [dict_from_row(r) for r in cursor.fetchall()]

@router.put("/trade-ins/{trade_id}")
def update_trade_in(trade_id: int, payload: dict, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, request_code FROM trade_in_requests WHERE id = ?", (trade_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trade-in request not found")

        fields = []
        values = []
        if "status" in payload:
            fields.append("status = ?")
            values.append(payload["status"])
        if "estimated_offer_price" in payload:
            fields.append("estimated_offer_price = ?")
            values.append(payload["estimated_offer_price"])
        if "admin_notes" in payload:
            fields.append("admin_notes = ?")
            values.append(payload["admin_notes"])

        if fields:
            values.append(trade_id)
            cursor.execute(f"UPDATE trade_in_requests SET {', '.join(fields)} WHERE id = ?", values)

        return {"message": "Trade-in updated successfully"}
