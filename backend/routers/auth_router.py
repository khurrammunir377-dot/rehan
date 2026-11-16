from fastapi import APIRouter, HTTPException, Depends, status
from backend.database import get_db, dict_from_row
from backend.auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from backend.models import LoginRequest, UserCreate

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login")
def login(req: LoginRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, password_hash, full_name, role, phone, is_active
            FROM users
            WHERE username = ? OR email = ?
        """, (req.username_or_email, req.username_or_email))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=400, detail="Invalid username/email or password")
        
        user = dict(row)
        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="Account is deactivated. Contact administrator.")
        
        if not verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Invalid username/email or password")
        
        # Log activity
        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'User Login', 'Logged in to Rehan Computers ERP')
        """, (user["id"], user["username"]))

        token = create_access_token(data={"sub": str(user["id"]), "role": user["role"], "username": user["username"]})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "phone": user["phone"]
            }
        }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}

@router.get("/users", dependencies=[Depends(require_role(["admin"]))])
def list_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, full_name, role, phone, is_active, created_at FROM users ORDER BY id ASC")
        return [dict_from_row(r) for r in cursor.fetchall()]

@router.post("/users", dependencies=[Depends(require_role(["admin"]))])
def create_user(req: UserCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        # Check duplicate
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (req.username, req.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        pw_hash = hash_password(req.password)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (req.username, req.email, pw_hash, req.full_name, req.role, req.phone))
        
        new_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, action, details)
            VALUES (?, ?, 'User Created', ?)
        """, (current_user["id"], current_user["username"], f"Created user {req.username} ({req.role})"))

        return {"message": "User created successfully", "user_id": new_id}

@router.put("/users/{user_id}/status", dependencies=[Depends(require_role(["admin"]))])
def toggle_user_status(user_id: int, current_user: dict = Depends(get_current_user)):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own administrator account")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_active, username FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        new_status = 0 if row["is_active"] == 1 else 1
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        return {"message": f"User status updated to {'Active' if new_status else 'Inactive'}"}
