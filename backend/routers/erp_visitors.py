import io
import csv
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
from backend.database import get_db, dict_from_row
from backend.auth import get_current_user, require_role
from backend.models import VisitorLogCreate, BlockIPRequest, TrafficControlUpdate

router = APIRouter(tags=["Visitor Analytics & Traffic Control"])

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

# ==================== PUBLIC ENDPOINTS ====================

@router.post("/api/public/visitor/ping")
def log_visitor_ping(req_data: VisitorLogCreate, request: Request):
    """Public beacon called on page visits to register session, track visitor count, and enforce IP access control."""
    ip = get_client_ip(request)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Check if IP is blocked
        cursor.execute("SELECT id, reason FROM blocked_ips WHERE ip_address = ? AND is_blocked = 1", (ip,))
        blocked_row = cursor.fetchone()
        if blocked_row:
            return {
                "blocked": True,
                "reason": blocked_row["reason"] or "Access restricted by administrator."
            }

        # 2. Check maintenance mode & global announcement banner
        cursor.execute("SELECT key, value FROM traffic_controls")
        controls = {r[0]: r[1] for r in cursor.fetchall()}
        maintenance = controls.get("maintenance_mode", "0") == "1"
        announcement = controls.get("announcement_banner", "")

        # 3. Insert visitor log
        # Simple user-agent parser
        ua_str = request.headers.get("user-agent", "")
        browser = req_data.browser or "Browser"
        os_name = req_data.os or "OS"

        if not req_data.browser:
            if "Chrome" in ua_str and "Edg" not in ua_str: browser = "Chrome"
            elif "Edg" in ua_str: browser = "Edge"
            elif "Firefox" in ua_str: browser = "Firefox"
            elif "Safari" in ua_str and "Chrome" not in ua_str: browser = "Safari"

        if not req_data.os:
            if "Windows" in ua_str: os_name = "Windows"
            elif "Android" in ua_str: os_name = "Android"
            elif "iPhone" in ua_str or "iPad" in ua_str: os_name = "iOS"
            elif "Mac" in ua_str: os_name = "macOS"
            elif "Linux" in ua_str: os_name = "Linux"

        cursor.execute("""
            INSERT INTO visitor_logs (
                ip_address, session_id, page_url, page_title, referrer,
                user_agent, device_type, browser, os, city, country
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Sargodha', 'Pakistan')
        """, (
            ip, req_data.session_id, req_data.page_url or "/", req_data.page_title,
            req_data.referrer, ua_str[:250], req_data.device_type or "Desktop",
            browser, os_name
        ))

        return {
            "blocked": False,
            "maintenance": maintenance,
            "announcement": announcement,
            "session_id": req_data.session_id
        }

# ==================== ERP PROTECTED ENDPOINTS ====================

@router.get("/api/erp/visitors/stats")
def get_visitor_stats(current_user: dict = Depends(get_current_user)):
    """Summary traffic stats, device breakdowns, and live active visitors."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Total Pageviews
        cursor.execute("SELECT COUNT(*) FROM visitor_logs")
        total_pageviews = cursor.fetchone()[0]

        # Total Unique Visitors (unique IPs)
        cursor.execute("SELECT COUNT(DISTINCT ip_address) FROM visitor_logs")
        total_unique_visitors = cursor.fetchone()[0]

        # Today's Pageviews
        cursor.execute("SELECT COUNT(*) FROM visitor_logs WHERE DATE(created_at) = DATE('now')")
        today_pageviews = cursor.fetchone()[0]

        # Today's Unique Visitors
        cursor.execute("SELECT COUNT(DISTINCT ip_address) FROM visitor_logs WHERE DATE(created_at) = DATE('now')")
        today_unique_visitors = cursor.fetchone()[0]

        # Active online in the last 15 minutes
        cursor.execute("""
            SELECT COUNT(DISTINCT ip_address) FROM visitor_logs 
            WHERE created_at >= DATETIME('now', '-15 minutes')
        """)
        active_online_visitors = cursor.fetchone()[0]

        # Device Breakdown
        cursor.execute("""
            SELECT device_type, COUNT(*) as count 
            FROM visitor_logs 
            GROUP BY device_type
        """)
        device_breakdown = [dict(r) for r in cursor.fetchall()]

        # Top Visited Pages
        cursor.execute("""
            SELECT page_url, COUNT(*) as hits 
            FROM visitor_logs 
            GROUP BY page_url 
            ORDER BY hits DESC LIMIT 6
        """)
        top_pages = [dict(r) for r in cursor.fetchall()]

        # Browser breakdown
        cursor.execute("""
            SELECT browser, COUNT(*) as count 
            FROM visitor_logs 
            WHERE browser IS NOT NULL 
            GROUP BY browser 
            ORDER BY count DESC LIMIT 5
        """)
        top_browsers = [dict(r) for r in cursor.fetchall()]

        # OS breakdown
        cursor.execute("""
            SELECT os, COUNT(*) as count 
            FROM visitor_logs 
            WHERE os IS NOT NULL 
            GROUP BY os 
            ORDER BY count DESC LIMIT 5
        """)
        top_os = [dict(r) for r in cursor.fetchall()]

        # Traffic Controls Status
        cursor.execute("SELECT key, value FROM traffic_controls")
        controls = {r[0]: r[1] for r in cursor.fetchall()}

        return {
            "total_pageviews": total_pageviews,
            "total_unique_visitors": total_unique_visitors,
            "today_pageviews": today_pageviews,
            "today_unique_visitors": today_unique_visitors,
            "active_online_visitors": max(1, active_online_visitors), # At least 1 (the current user)
            "device_breakdown": device_breakdown,
            "top_pages": top_pages,
            "top_browsers": top_browsers,
            "top_os": top_os,
            "maintenance_mode": controls.get("maintenance_mode", "0") == "1",
            "announcement_banner": controls.get("announcement_banner", "")
        }

@router.get("/api/erp/visitors/logs")
def get_visitor_logs(limit: int = 100, current_user: dict = Depends(get_current_user)):
    """Returns detailed individual visitor visit logs with IP block status."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.*, (SELECT COUNT(*) FROM blocked_ips WHERE ip_address = v.ip_address AND is_blocked = 1) as is_blocked
            FROM visitor_logs v
            ORDER BY v.id DESC LIMIT ?
        """, (limit,))
        return [dict_from_row(r) for r in cursor.fetchall()]

@router.get("/api/erp/visitors/blocked-ips", dependencies=[Depends(require_role(["admin"]))])
def get_blocked_ips(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blocked_ips ORDER BY id DESC")
        return [dict_from_row(r) for r in cursor.fetchall()]

@router.post("/api/erp/visitors/block-ip", dependencies=[Depends(require_role(["admin"]))])
def block_ip(block_in: BlockIPRequest, current_user: dict = Depends(get_current_user)):
    ip = block_in.ip_address.strip()
    if not ip:
        raise HTTPException(status_code=400, detail="Invalid IP address")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO blocked_ips (ip_address, reason, is_blocked, blocked_by)
            VALUES (?, ?, 1, ?)
        """, (ip, block_in.reason, current_user["username"]))

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'IP Blocked', ?)
        """, (current_user["id"], current_user["username"], f"Blocked IP address: {ip} (Reason: {block_in.reason})"))

        return {"success": True, "message": f"IP address {ip} has been blocked successfully."}

@router.post("/api/erp/visitors/unblock-ip", dependencies=[Depends(require_role(["admin"]))])
def unblock_ip(payload: dict, current_user: dict = Depends(get_current_user)):
    ip = payload.get("ip_address", "").strip()
    if not ip:
        raise HTTPException(status_code=400, detail="IP address required")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM blocked_ips WHERE ip_address = ?", (ip,))

        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'IP Unblocked', ?)
        """, (current_user["id"], current_user["username"], f"Unblocked IP address: {ip}"))

        return {"success": True, "message": f"IP address {ip} unblocked."}

@router.put("/api/erp/visitors/controls", dependencies=[Depends(require_role(["admin"]))])
def update_traffic_controls(ctrl: TrafficControlUpdate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        if ctrl.maintenance_mode is not None:
            val = "1" if ctrl.maintenance_mode else "0"
            cursor.execute("INSERT OR REPLACE INTO traffic_controls (key, value) VALUES ('maintenance_mode', ?)", (val,))
            cursor.execute("""
                INSERT INTO activity_logs (user_id, username, action, details)
                VALUES (?, ?, 'Store Control', ?)
            """, (current_user["id"], current_user["username"], f"Maintenance mode set to {val}"))

        if ctrl.announcement_banner is not None:
            cursor.execute("INSERT OR REPLACE INTO traffic_controls (key, value) VALUES ('announcement_banner', ?)", (ctrl.announcement_banner,))

        return {"success": True, "message": "Traffic and store controls updated."}

@router.get("/api/erp/visitors/export-csv", dependencies=[Depends(require_role(["admin"]))])
def export_visitors_csv(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, ip_address, page_url, device_type, browser, os, city, created_at
            FROM visitor_logs
            ORDER BY id DESC LIMIT 500
        """)
        rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Log ID", "IP Address", "Page Visited", "Device", "Browser", "Operating System", "Location", "Timestamp"])
        for r in rows:
            writer.writerow(list(r))

        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=rehan_computers_traffic_log.csv"}
        )
