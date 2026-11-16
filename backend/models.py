from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Dict

# Auth
class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "cashier"
    phone: Optional[str] = None

# Product
class ProductCreate(BaseModel):
    title: str
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    condition: str = "Grade A+ Used"
    specs: Optional[Dict[str, Any]] = None
    cost_price: float = 0.0
    selling_price: float
    discount_price: Optional[float] = None
    stock_quantity: int = 1
    min_stock_alert: int = 2
    warranty_period: str = "1 Month Checking Warranty"
    image_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    is_featured: bool = False
    is_active: bool = True
    sku: Optional[str] = None
    serial_numbers: Optional[List[str]] = None

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    condition: Optional[str] = None
    specs: Optional[Dict[str, Any]] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    discount_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    min_stock_alert: Optional[int] = None
    warranty_period: Optional[str] = None
    image_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None

class ProductPricePicsUpdate(BaseModel):
    selling_price: float
    cost_price: Optional[float] = None
    discount_price: Optional[float] = None
    image_url: Optional[str] = None
    gallery: Optional[List[str]] = None

# Visitor Analytics & Traffic Control Models
class VisitorLogCreate(BaseModel):
    page_url: str = "/"
    page_title: Optional[str] = None
    referrer: Optional[str] = None
    session_id: Optional[str] = None
    device_type: Optional[str] = "Desktop"
    browser: Optional[str] = None
    os: Optional[str] = None

class BlockIPRequest(BaseModel):
    ip_address: str
    reason: Optional[str] = "Spam / Suspicious traffic"

class TrafficControlUpdate(BaseModel):
    maintenance_mode: Optional[bool] = None
    announcement_banner: Optional[str] = None

# Cart / Public Order
class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = 1

class PublicOrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    shipping_address: str
    city: str = "Sargodha"
    payment_method: str = "cash_on_delivery" # cash_on_delivery, bank_transfer, easypaisa_jazzcash
    notes: Optional[str] = None
    items: List[OrderItemIn]

# POS Sale
class POSItemIn(BaseModel):
    product_id: int
    quantity: int = 1
    unit_price: float
    serial_number: Optional[str] = None

class POSSaleCreate(BaseModel):
    customer_name: Optional[str] = "Walk-in Customer"
    customer_phone: Optional[str] = None
    payment_method: str = "cash" # cash, jazzcash_easypaisa, bank_transfer, split
    items: List[POSItemIn]
    discount: float = 0.0
    tax: float = 0.0
    amount_paid: float
    notes: Optional[str] = None

# Repair Ticket
class RepairTicketCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    device_brand: str
    device_model: str
    serial_or_password: Optional[str] = None
    problem_description: str
    accessories_received: Optional[str] = "None"
    estimated_cost: float = 0.0
    advance_paid: float = 0.0

class RepairTicketUpdate(BaseModel):
    status: Optional[str] = None
    assigned_technician_id: Optional[int] = None
    final_cost: Optional[float] = None
    advance_paid: Optional[float] = None
    parts_cost: Optional[float] = None
    parts_used: Optional[str] = None
    technician_notes: Optional[str] = None
    customer_notified: Optional[int] = None

# Trade-In Request
class TradeInCreate(BaseModel):
    customer_name: str
    customer_phone: str
    device_brand: str
    device_model: str
    specs_details: str
    condition_grade: str
    customer_expected_price: Optional[float] = None

# Expense
class ExpenseCreate(BaseModel):
    category: str
    amount: float
    description: str
    payment_method: str = "cash"
    expense_date: Optional[str] = None

# Supplier & Purchase
class SupplierCreate(BaseModel):
    company_name: str
    contact_person: Optional[str] = None
    phone: str
    city: Optional[str] = None
    address: Optional[str] = None

class PurchaseItemIn(BaseModel):
    product_id: int
    unit_cost: float
    quantity: int

class PurchaseCreate(BaseModel):
    supplier_id: int
    supplier_invoice_no: Optional[str] = None
    items: List[PurchaseItemIn]
    paid_amount: float
    notes: Optional[str] = None

# Stock adjustment
class StockAdjustIn(BaseModel):
    quantity_change: int # positive or negative
    reason: str
