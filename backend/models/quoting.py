from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid

class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED = "converted"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"

class PricingTier(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class QuoteLayout(str, Enum):
    MODERN = "modern"
    CLASSIC = "classic"
    MINIMAL = "minimal"
    PROFESSIONAL = "professional"

class ProductService(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    category: str = "General"
    unit_price: float
    pricing_tiers: Dict[str, float] = {}  # {"standard": 100, "premium": 80, "enterprise": 60}
    is_service: bool = False  # True for services, False for products
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class QuoteLineItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_service_id: str
    product_name: str
    description: Optional[str] = None
    quantity: float = 1.0
    unit_price: float
    discount_percentage: float = 0.0
    discount_amount: float = 0.0
    line_total: float = 0.0
    pricing_tier: PricingTier = PricingTier.STANDARD

class TaxSettings(BaseModel):
    tax_rate: float = 0.0  # Percentage
    tax_name: str = "Tax"
    tax_amount: float = 0.0
    is_inclusive: bool = False

class Quote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quote_number: str
    title: str
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_address: Optional[Dict[str, str]] = None
    
    # Quote Details
    line_items: List[QuoteLineItem] = []
    subtotal: float = 0.0
    total_discount: float = 0.0
    tax_settings: TaxSettings = TaxSettings()
    total_amount: float = 0.0
    
    # Status and Workflow
    status: QuoteStatus = QuoteStatus.DRAFT
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    
    # Dates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Customization
    layout: QuoteLayout = QuoteLayout.MODERN
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    
    # Tracking
    view_count: int = 0
    created_by: str
    last_modified_by: str
    
    # Advanced Features
    e_signature_required: bool = False
    e_signature_url: Optional[str] = None
    payment_link: Optional[str] = None
    conversion_probability: float = 0.0  # AI-calculated probability

class QuoteTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    layout: QuoteLayout
    industry: Optional[str] = None
    default_terms: Optional[str] = None
    default_notes: Optional[str] = None
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QuoteAnalytics(BaseModel):
    quote_id: str
    total_views: int = 0
    unique_views: int = 0
    time_to_first_view: Optional[int] = None  # Minutes
    time_to_decision: Optional[int] = None  # Minutes
    last_activity: Optional[datetime] = None
    conversion_events: List[Dict[str, Any]] = []

# Request Models for API
class ProductServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "General"
    unit_price: float
    pricing_tiers: Dict[str, float] = {}
    is_service: bool = False

class QuoteLineItemCreate(BaseModel):
    product_service_id: str
    quantity: float = 1.0
    discount_percentage: float = 0.0
    discount_amount: float = 0.0
    pricing_tier: PricingTier = PricingTier.STANDARD

class QuoteCreate(BaseModel):
    title: str
    lead_id: Optional[str] = None
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_address: Optional[Dict[str, str]] = None
    line_items: List[QuoteLineItemCreate] = []
    tax_settings: TaxSettings = TaxSettings()
    layout: QuoteLayout = QuoteLayout.MODERN
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    expires_in_days: int = 30
    e_signature_required: bool = False
    created_by: str

class QuoteUpdate(BaseModel):
    title: Optional[str] = None
    line_items: Optional[List[QuoteLineItemCreate]] = None
    tax_settings: Optional[TaxSettings] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    expires_in_days: Optional[int] = None
    e_signature_required: Optional[bool] = None

class ApprovalRequest(BaseModel):
    quote_id: str
    action: str  # "approve" or "reject"
    notes: Optional[str] = None
    approved_by: str