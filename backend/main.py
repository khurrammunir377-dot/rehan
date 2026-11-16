import os
from fastapi import FastAPI
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
init_db()
seed_database()

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
    # Mount css, js, public
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
    app.mount("/public", StaticFiles(directory=os.path.join(FRONTEND_DIR, "public")), name="public")

# Serve pages
@app.get("/", response_class=FileResponse)
def serve_storefront():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/admin", response_class=FileResponse)
def serve_erp():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    return FileResponse(admin_path)

@app.get("/admin.html", response_class=FileResponse)
def serve_erp_alias():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    return FileResponse(admin_path)

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
