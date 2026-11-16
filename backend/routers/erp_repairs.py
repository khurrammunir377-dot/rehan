import time
import random
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from backend.database import get_db, dict_from_row
from backend.auth import get_current_user
from backend.models import RepairTicketCreate, RepairTicketUpdate

router = APIRouter(prefix="/api/erp/repairs", tags=["ERP Workshop & Repairs"])

@router.get("")
def list_repairs(
    status: Optional[str] = None,
    technician_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM repair_tickets WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if technician_id:
            query += " AND assigned_technician_id = ?"
            params.append(technician_id)
        if search:
            query += " AND (ticket_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ? OR device_model LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s, s])

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        return [dict_from_row(r) for r in cursor.fetchall()]

@router.post("")
def create_repair_ticket(ticket_in: RepairTicketCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        t_num = f"RC-REP-{int(time.time()) % 100000}{random.randint(10, 99)}"

        cursor.execute("""
            INSERT INTO repair_tickets (
                ticket_number, customer_name, customer_phone, customer_email,
                device_brand, device_model, serial_or_password, problem_description,
                accessories_received, estimated_cost, advance_paid, status,
                assigned_technician_id, technician_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'received', ?, ?)
        """, (
            t_num, ticket_in.customer_name, ticket_in.customer_phone, ticket_in.customer_email,
            ticket_in.device_brand, ticket_in.device_model, ticket_in.serial_or_password,
            ticket_in.problem_description, ticket_in.accessories_received or "None",
            ticket_in.estimated_cost, ticket_in.advance_paid,
            current_user["id"], current_user["full_name"]
        ))
        new_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'Repair Ticket Created', ?)
        """, (current_user["id"], current_user["username"], f"Ticket {t_num} created for {ticket_in.device_brand} {ticket_in.device_model}"))

        return {"message": "Repair ticket created successfully", "ticket_number": t_num, "id": new_id}

@router.get("/{ticket_id}")
def get_repair_detail(ticket_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repair_tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Repair ticket not found")
        return dict_from_row(row)

@router.put("/{ticket_id}")
def update_repair_ticket(ticket_id: int, update_data: RepairTicketUpdate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, ticket_number FROM repair_tickets WHERE id = ?", (ticket_id,))
        ticket = cursor.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Repair ticket not found")

        fields = []
        values = []

        if update_data.status is not None:
            fields.append("status = ?")
            values.append(update_data.status)
            if update_data.status == "delivered":
                fields.append("completed_at = CURRENT_TIMESTAMP")
        if update_data.assigned_technician_id is not None:
            fields.append("assigned_technician_id = ?")
            values.append(update_data.assigned_technician_id)
            cursor.execute("SELECT full_name FROM users WHERE id = ?", (update_data.assigned_technician_id,))
            tech = cursor.fetchone()
            if tech:
                fields.append("technician_name = ?")
                values.append(tech["full_name"])
        if update_data.final_cost is not None:
            fields.append("final_cost = ?")
            values.append(update_data.final_cost)
        if update_data.advance_paid is not None:
            fields.append("advance_paid = ?")
            values.append(update_data.advance_paid)
        if update_data.parts_cost is not None:
            fields.append("parts_cost = ?")
            values.append(update_data.parts_cost)
        if update_data.parts_used is not None:
            fields.append("parts_used = ?")
            values.append(update_data.parts_used)
        if update_data.technician_notes is not None:
            fields.append("technician_notes = ?")
            values.append(update_data.technician_notes)
        if update_data.customer_notified is not None:
            fields.append("customer_notified = ?")
            values.append(update_data.customer_notified)

        if not fields:
            return {"message": "No changes supplied"}

        values.append(ticket_id)
        sql = f"UPDATE repair_tickets SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, values)

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'Repair Ticket Updated', ?)
        """, (current_user["id"], current_user["username"], f"Ticket {ticket['ticket_number']} updated to {update_data.status or 'updated'}"))

        return {"message": "Repair ticket updated successfully"}
