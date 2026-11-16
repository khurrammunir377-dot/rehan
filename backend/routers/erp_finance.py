from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from backend.database import get_db, dict_from_row
from backend.auth import get_current_user, require_role
from backend.models import ExpenseCreate

router = APIRouter(prefix="/api/erp/finance", tags=["ERP Financial Management"])

@router.get("/expenses")
def list_expenses(
    category: Optional[str] = None,
    month: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if month:
            query += " AND strftime('%Y-%m', expense_date) = ?"
            params.append(month)

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        return [dict_from_row(r) for r in cursor.fetchall()]

@router.post("/expenses")
def record_expense(exp: ExpenseCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (category, amount, description, payment_method, expense_date, recorded_by_id, recorded_by_name)
            VALUES (?, ?, ?, ?, COALESCE(?, DATE('now')), ?, ?)
        """, (
            exp.category, exp.amount, exp.description, exp.payment_method,
            exp.expense_date, current_user["id"], current_user["full_name"]
        ))
        new_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'Expense Recorded', ?)
        """, (current_user["id"], current_user["username"], f"{exp.category}: {exp.amount:,.0f} PKR ({exp.description})"))

        return {"message": "Expense recorded successfully", "expense_id": new_id}

@router.delete("/expenses/{expense_id}", dependencies=[Depends(require_role(["admin"]))])
def delete_expense(expense_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return {"message": "Expense deleted"}

@router.get("/profit-loss")
def get_profit_and_loss(month: Optional[str] = None, current_user: dict = Depends(require_role(["admin", "manager"]))):
    with get_db() as conn:
        cursor = conn.cursor()
        month_filter = month or "strftime('%Y-%m', 'now')"

        # Sales Revenue (POS)
        cursor.execute(f"""
            SELECT COALESCE(SUM(total_amount), 0) FROM pos_sales 
            WHERE strftime('%Y-%m', created_at) = {month_filter}
        """)
        pos_total = cursor.fetchone()[0]

        # Sales Revenue (Orders)
        cursor.execute(f"""
            SELECT COALESCE(SUM(total_amount), 0) FROM orders 
            WHERE payment_status = 'paid' AND strftime('%Y-%m', created_at) = {month_filter}
        """)
        orders_total = cursor.fetchone()[0]

        # Repair Revenue
        cursor.execute(f"""
            SELECT COALESCE(SUM(final_cost), 0) FROM repair_tickets 
            WHERE status = 'delivered' AND strftime('%Y-%m', created_at) = {month_filter}
        """)
        repairs_total = cursor.fetchone()[0]

        gross_revenue = pos_total + orders_total + repairs_total

        # Cost of Goods Sold (estimated 82% of sales based on hardware margins)
        cogs = (pos_total + orders_total) * 0.84

        # Total Operating Expenses
        cursor.execute(f"""
            SELECT COALESCE(SUM(amount), 0) FROM expenses 
            WHERE strftime('%Y-%m', expense_date) = {month_filter}
        """)
        total_expenses = cursor.fetchone()[0]

        # Expenses by category
        cursor.execute(f"""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE strftime('%Y-%m', expense_date) = {month_filter}
            GROUP BY category
        """)
        expenses_by_category = [dict(r) for r in cursor.fetchall()]

        gross_profit = gross_revenue - cogs
        net_profit = gross_profit - total_expenses

        return {
            "month": month or "Current Month",
            "pos_revenue": pos_total,
            "orders_revenue": orders_total,
            "repairs_revenue": repairs_total,
            "gross_revenue": gross_revenue,
            "estimated_cogs": cogs,
            "gross_profit": gross_profit,
            "total_expenses": total_expenses,
            "expenses_by_category": expenses_by_category,
            "net_profit": net_profit
        }

@router.get("/daily-register")
def get_daily_register(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        # Today's Cash POS
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM pos_sales WHERE payment_method = 'cash' AND DATE(created_at) = DATE('now')")
        cash_sales = cursor.fetchone()[0]

        # Today's Digital/Bank POS
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM pos_sales WHERE payment_method != 'cash' AND DATE(created_at) = DATE('now')")
        digital_sales = cursor.fetchone()[0]

        # Today's Cash Expenses
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE payment_method = 'cash' AND DATE(expense_date) = DATE('now')")
        cash_expenses = cursor.fetchone()[0]

        # Expected cash in drawer
        opening_float = 15000.0 # Standard drawer float
        expected_cash = opening_float + cash_sales - cash_expenses

        return {
            "date": "Today",
            "opening_float": opening_float,
            "cash_sales": cash_sales,
            "digital_sales": digital_sales,
            "cash_expenses": cash_expenses,
            "expected_cash_in_drawer": expected_cash
        }
