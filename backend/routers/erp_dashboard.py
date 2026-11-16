from fastapi import APIRouter, Depends
from backend.database import get_db, dict_from_row
from backend.auth import get_current_user

router = APIRouter(prefix="/api/erp/dashboard", tags=["ERP Dashboard"])

@router.get("/stats")
def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Total Sales & Revenue (Orders + POS)
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE payment_status = 'paid'")
        paid_orders_revenue = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM pos_sales")
        pos_revenue = cursor.fetchone()[0]

        total_gross_revenue = paid_orders_revenue + pos_revenue

        # 2. Today's Sales
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM pos_sales 
            WHERE DATE(created_at) = DATE('now')
        """)
        today_pos = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM orders 
            WHERE DATE(created_at) = DATE('now')
        """)
        today_orders = cursor.fetchone()[0]
        today_sales = today_pos + today_orders

        # 3. Monthly Sales
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM pos_sales 
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        """)
        monthly_pos = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM orders 
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        """)
        monthly_orders = cursor.fetchone()[0]
        monthly_sales = monthly_pos + monthly_orders

        # 4. Total Orders & Status counts
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'new'")
        new_orders_count = cursor.fetchone()[0]

        # 5. Inventory & Low Stock Alerts
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        total_products_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1 AND stock_quantity <= min_stock_alert")
        low_stock_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT id, title, sku, stock_quantity, min_stock_alert, selling_price
            FROM products
            WHERE is_active = 1 AND stock_quantity <= min_stock_alert
            ORDER BY stock_quantity ASC LIMIT 5
        """)
        low_stock_items = [dict(r) for r in cursor.fetchall()]

        # 6. Active Repair Tickets
        cursor.execute("SELECT COUNT(*) FROM repair_tickets WHERE status NOT IN ('delivered', 'cancelled')")
        active_repairs_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM repair_tickets WHERE status = 'ready_for_pickup'")
        ready_repairs_count = cursor.fetchone()[0]

        # 7. Total Expenses & Net Profit this month
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses 
            WHERE strftime('%Y-%m', expense_date) = strftime('%Y-%m', 'now')
        """)
        monthly_expenses = cursor.fetchone()[0]

        # Estimated Gross Margin ~ 15-20% of sales
        estimated_gross_profit = monthly_sales * 0.16
        estimated_net_profit = estimated_gross_profit - monthly_expenses

        # 8. Recent 7-days sales trend (for chart)
        cursor.execute("""
            SELECT DATE(created_at) as sale_date, SUM(total_amount) as daily_total
            FROM (
                SELECT created_at, total_amount FROM pos_sales
                UNION ALL
                SELECT created_at, total_amount FROM orders
            )
            WHERE created_at >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY sale_date ASC
        """)
        sales_trend = [dict(r) for r in cursor.fetchall()]

        # 9. Recent Orders
        cursor.execute("""
            SELECT id, order_number, customer_name, customer_phone, total_amount, payment_status, order_status, created_at
            FROM orders
            ORDER BY id DESC LIMIT 5
        """)
        recent_orders = [dict_from_row(r) for r in cursor.fetchall()]

        # 10. Recent Repair Jobs
        cursor.execute("""
            SELECT id, ticket_number, customer_name, device_brand, device_model, status, estimated_cost, final_cost, created_at
            FROM repair_tickets
            ORDER BY id DESC LIMIT 5
        """)
        recent_repairs = [dict_from_row(r) for r in cursor.fetchall()]

        # 11. Recent Activity Logs
        cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 6")
        recent_logs = [dict(r) for r in cursor.fetchall()]

        return {
            "total_gross_revenue": total_gross_revenue,
            "today_sales": today_sales,
            "monthly_sales": monthly_sales,
            "total_orders_count": total_orders_count,
            "new_orders_count": new_orders_count,
            "total_products_count": total_products_count,
            "low_stock_count": low_stock_count,
            "low_stock_items": low_stock_items,
            "active_repairs_count": active_repairs_count,
            "ready_repairs_count": ready_repairs_count,
            "monthly_expenses": monthly_expenses,
            "estimated_net_profit": estimated_net_profit,
            "sales_trend": sales_trend,
            "recent_orders": recent_orders,
            "recent_repairs": recent_repairs,
            "recent_logs": recent_logs
        }
