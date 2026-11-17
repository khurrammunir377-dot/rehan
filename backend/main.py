import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db
from backend.seed_data import seed_database
from backend.routers import (
    auth_router,
    public_router,
    erp_dashboard,
    erp_products,
    erp_pos,
    erp_orders,
    erp_repairs,
    erp_finance,
    erp_crm,
    erp_settings,
    erp_visitors
)

# Initialize and seed database if necessary
try:
    init_db()
    seed_database()
except Exception as e:
    print(f"Warning: database initialization notice: {e}")

app = FastAPI(
    title="Rehan Computers E-Commerce & ERP System",
    description="Full-featured E-Commerce Website & Enterprise Resource Planning (ERP) Platform for Rehan Laptop & Computer, Shop #96, 1st Floor, Trust Plaza, Sargodha.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel URL rewrite middleware (restores original client route from query param / headers)
@app.middleware("http")
async def vercel_url_rewrite_middleware(request: Request, call_next):
    orig_path = (
        request.query_params.get("__orig_path")
        or request.headers.get("x-forwarded-uri")
        or request.headers.get("x-matched-path")
        or request.headers.get("x-invoke-path")
    )
    if orig_path:
        clean_path = orig_path.split("?")[0]
        request.scope["path"] = clean_path
    return await call_next(request)

# Include API Routers
app.include_router(auth_router.router)
app.include_router(public_router.router)
app.include_router(erp_dashboard.router)
app.include_router(erp_products.router)
app.include_router(erp_pos.router)
app.include_router(erp_orders.router)
app.include_router(erp_repairs.router)
app.include_router(erp_finance.router)
app.include_router(erp_crm.router)
app.include_router(erp_settings.router)
app.include_router(erp_visitors.router)

# Mount frontend static directories
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

if os.path.exists(FRONTEND_DIR):
    try:
        if os.path.exists(os.path.join(FRONTEND_DIR, "css")):
            app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
        if os.path.exists(os.path.join(FRONTEND_DIR, "js")):
            app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
        if os.path.exists(os.path.join(FRONTEND_DIR, "public")):
            app.mount("/public", StaticFiles(directory=os.path.join(FRONTEND_DIR, "public")), name="public")
    except Exception as e:
        print("Static mount note:", e)

# Serve pages
@app.get("/", response_class=FileResponse)
@app.get("/frontend/index.html", response_class=FileResponse)
def serve_storefront():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/admin", response_class=FileResponse)
@app.get("/admin.html", response_class=FileResponse)
@app.get("/frontend/admin.html", response_class=FileResponse)
def serve_erp():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    return FileResponse(admin_path)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.get("/frontend/css/{file_path:path}")
def serve_frontend_css(file_path: str):
    p = os.path.join(FRONTEND_DIR, "css", file_path)
    if os.path.isfile(p):
        return FileResponse(p)
    return Response(status_code=404, content=b"CSS not found")

@app.get("/frontend/js/{file_path:path}")
def serve_frontend_js(file_path: str):
    p = os.path.join(FRONTEND_DIR, "js", file_path)
    if os.path.isfile(p):
        return FileResponse(p)
    return Response(status_code=404, content=b"JS not found")

@app.get("/frontend/public/{file_path:path}")
@app.get("/public/{file_path:path}")
@app.get("/posters/{file_path:path}")
def serve_frontend_public(file_path: str):
    # Strip any leading slashes or prefixes
    clean = file_path.lstrip("/").replace("public/", "").replace("posters/", "")
    filename = os.path.basename(file_path)
    
    candidates = [
        os.path.join(ROOT_DIR, "public", file_path),
        os.path.join(ROOT_DIR, "public", "posters", filename),
        os.path.join(ROOT_DIR, "public", "uploads", filename),
        os.path.join(ROOT_DIR, "posters", filename),
        os.path.join(FRONTEND_DIR, "public", file_path),
        os.path.join(FRONTEND_DIR, "public", "posters", filename),
        os.path.join(FRONTEND_DIR, "public", "uploads", filename),
        os.path.join(ROOT_DIR, "public", clean),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return FileResponse(c)
    return Response(status_code=404, content=b"Image not found")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "store": "Rehan Laptop & Computer",
        "location": "Shop #96, 1st Floor, Trust Plaza, Sargodha",
        "phone": "0300-9607829",
        "system": "Active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
