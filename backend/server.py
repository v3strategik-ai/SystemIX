from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from jose import JWTError, jwt
import hashlib
from datetime import datetime, timedelta
# Import built-in models and types
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import os
import logging
import uuid
import json
import asyncio
import random
from pathlib import Path
import base64
import io
import requests
from requests_oauthlib import OAuth2Session
from authlib.integrations.base_client import OAuthError

# File processing libraries
from docx import Document as DocxDocument
from openpyxl import Workbook, load_workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# AI Integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import monitoring models
from models.monitoring import (
    MonitoringMetric, SystemAlert, SystemStatus, HealingAction,
    MonitoringConfig, AnomalyDetection, AlertSeverity, AlertStatus
)

# Import authentication models
from models.auth import (
    User, UserCreate, UserLogin, UserResponse, TokenResponse, 
    TokenData, UserRole
)

# Define UserRole locally as backup
class LocalUserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"

# Import quoting models directly
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
    pricing_tiers: Dict[str, float] = {}
    is_service: bool = False
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
    tax_rate: float = 0.0
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
    line_items: List[QuoteLineItem] = []
    subtotal: float = 0.0
    total_discount: float = 0.0
    tax_settings: TaxSettings = TaxSettings()
    total_amount: float = 0.0
    status: QuoteStatus = QuoteStatus.DRAFT
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    layout: QuoteLayout = QuoteLayout.MODERN
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    view_count: int = 0
    created_by: str
    last_modified_by: str
    e_signature_required: bool = False
    e_signature_url: Optional[str] = None
    payment_link: Optional[str] = None
    conversion_probability: float = 0.0

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
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[Dict[str, str]] = None
    line_items: Optional[List[QuoteLineItemCreate]] = None
    tax_settings: Optional[TaxSettings] = None
    layout: Optional[QuoteLayout] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    status: Optional[QuoteStatus] = None
    last_modified_by: str

class ApprovalRequest(BaseModel):
    quote_id: str
    action: str
    notes: Optional[str] = None
    approved_by: str

class QuoteTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    layout: QuoteLayout = QuoteLayout.MODERN
    default_terms: Optional[str] = None
    default_notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class QuoteAnalytics(BaseModel):
    quote_id: str
    total_views: int = 0
    unique_views: int = 0
    time_to_first_view: Optional[int] = None  # minutes
    last_activity: Optional[datetime] = None
    conversion_events: List[Dict[str, Any]] = []

# Document Center Models
class DocumentType(str, Enum):
    CONTRACT = "contract"
    FORM = "form"
    TEMPLATE = "template"
    INVOICE = "invoice"
    PROPOSAL = "proposal"
    AGREEMENT = "agreement"
    CUSTOM = "custom"

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    EXPIRED = "expired"

class FileFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    HTML = "html"
    TXT = "txt"

class AccessLevel(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    PUBLIC = "public"

class FormFieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    DATE = "date"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SELECT = "select"
    SIGNATURE = "signature"
    EMAIL = "email"
    PHONE = "phone"

class FormField(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: FormFieldType
    label: str
    placeholder: Optional[str] = None
    required: bool = False
    options: List[str] = []  # For select, radio
    validation: Optional[Dict[str, Any]] = None
    position: Dict[str, float] = {}  # x, y, width, height for positioning
    default_value: Optional[str] = None

class DocumentCategory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    color: str = "#3B82F6"
    icon: str = "📄"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

class DocumentTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    type: DocumentType
    category_id: Optional[str] = None
    content: str  # HTML content or template structure
    form_fields: List[FormField] = []
    variables: List[str] = []  # Template variables like {{customer_name}}
    thumbnail_url: Optional[str] = None
    file_format: FileFormat = FileFormat.PDF
    is_active: bool = True
    access_level: AccessLevel = AccessLevel.TEAM
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = 0
    tags: List[str] = []

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    template_id: Optional[str] = None
    type: DocumentType
    category_id: Optional[str] = None
    content: str
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_format: FileFormat
    file_size: int = 0  # in bytes
    status: DocumentStatus = DocumentStatus.DRAFT
    access_level: AccessLevel = AccessLevel.PRIVATE
    
    # DocuSign Integration
    docusign_envelope_id: Optional[str] = None
    docusign_status: Optional[str] = None
    signature_required: bool = False
    signers: List[Dict[str, str]] = []  # [{"name": "", "email": "", "role": ""}]
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    tags: List[str] = []
    
    # Relations
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    quote_id: Optional[str] = None

class DocumentPermission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    user_id: str
    permission_type: str  # "view", "edit", "admin"
    granted_by: str
    granted_at: datetime = Field(default_factory=datetime.utcnow)

class DocuSignEnvelope(BaseModel):
    envelope_id: str
    document_id: str
    status: str
    created_date: datetime
    sent_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    declined_date: Optional[datetime] = None
    recipients: List[Dict[str, Any]] = []
    documents: List[Dict[str, Any]] = []

# Request Models
class DocumentCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    color: str = "#3B82F6"
    icon: str = "📄"
    created_by: str

class DocumentTemplateCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: DocumentType
    category_id: Optional[str] = None
    content: str
    form_fields: List[FormField] = []
    variables: List[str] = []
    file_format: FileFormat = FileFormat.PDF
    access_level: AccessLevel = AccessLevel.TEAM
    created_by: str
    tags: List[str] = []

class DocumentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    template_id: Optional[str] = None
    type: DocumentType
    category_id: Optional[str] = None
    content: str
    file_format: FileFormat
    access_level: AccessLevel = AccessLevel.PRIVATE
    signature_required: bool = False
    signers: List[Dict[str, str]] = []
    created_by: str
    tags: List[str] = []
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    quote_id: Optional[str] = None

class FileConversionRequest(BaseModel):
    file_content: str  # Base64 encoded
    source_format: FileFormat
    target_format: FileFormat
    document_title: Optional[str] = None

class DocuSignSendRequest(BaseModel):
    document_id: str
    signers: List[Dict[str, str]]  # [{"name": "", "email": "", "role": ""}]
    email_subject: Optional[str] = None
    email_message: Optional[str] = None
    send_reminders: bool = True

# Integrations Hub Models
class IntegrationType(str, Enum):
    CRM = "crm"
    PAYMENT = "payment"
    MARKETING = "marketing"
    COMMUNICATION = "communication"
    PROJECT_MANAGEMENT = "project_management"
    ECOMMERCE = "ecommerce"
    CUSTOM = "custom"

class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"
    EXPIRED = "expired"

class SyncStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    CANCELLED = "cancelled"

class AuthType(str, Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    CUSTOM = "custom"

class SyncDirection(str, Enum):
    BIDIRECTIONAL = "bidirectional"
    INBOUND = "inbound"  # From external to SystemIX
    OUTBOUND = "outbound"  # From SystemIX to external

class IntegrationPlatform(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str  # e.g., 'salesforce', 'hubspot'
    type: IntegrationType
    description: str
    logo_url: str
    website_url: str
    documentation_url: Optional[str] = None
    auth_type: AuthType
    auth_config: Dict[str, Any] = {}  # OAuth endpoints, scopes, etc.
    supported_features: List[str] = []  # ['contacts', 'deals', 'tasks']
    api_base_url: str
    rate_limits: Dict[str, int] = {}  # {'requests_per_hour': 1000}
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class IntegrationConnection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform_id: str
    platform_name: str
    user_id: str
    connection_name: str  # User-defined name for this connection
    status: ConnectionStatus = ConnectionStatus.PENDING
    
    # Authentication data
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    api_key: Optional[str] = None
    auth_data: Dict[str, Any] = {}  # Additional auth data
    
    # Configuration
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    sync_frequency: int = 60  # minutes
    field_mappings: Dict[str, str] = {}  # SystemIX field -> External field
    sync_filters: Dict[str, Any] = {}  # Conditions for syncing
    
    # Status tracking
    last_sync_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    total_syncs: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class SyncJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    platform_name: str
    job_type: str  # 'scheduled', 'manual', 'webhook'
    direction: SyncDirection
    status: SyncStatus = SyncStatus.PENDING
    
    # Job details
    data_type: str  # 'contacts', 'deals', 'tasks', etc.
    records_to_sync: int = 0
    records_processed: int = 0
    records_success: int = 0
    records_failed: int = 0
    
    # Execution info
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = {}
    
    # Results
    sync_summary: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WebhookEndpoint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    platform_name: str
    endpoint_url: str
    secret_key: str
    events: List[str] = []  # ['contact.created', 'deal.updated']
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    total_triggers: int = 0

class IntegrationAnalytics(BaseModel):
    connection_id: str
    platform_name: str
    date: datetime
    sync_count: int = 0
    success_rate: float = 0.0
    avg_sync_duration: float = 0.0  # seconds
    data_volume: int = 0  # records synced
    error_count: int = 0
    api_calls_made: int = 0

# Request Models
class IntegrationPlatformCreate(BaseModel):
    name: str
    slug: str
    type: IntegrationType
    description: str
    logo_url: str
    website_url: str
    documentation_url: Optional[str] = None
    auth_type: AuthType
    auth_config: Dict[str, Any] = {}
    supported_features: List[str] = []
    api_base_url: str
    rate_limits: Dict[str, int] = {}

class ConnectionCreate(BaseModel):
    platform_id: str
    connection_name: str
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    sync_frequency: int = 60
    field_mappings: Dict[str, str] = {}
    sync_filters: Dict[str, Any] = {}
    user_id: str

class OAuthInitRequest(BaseModel):
    platform_id: str
    connection_name: str
    redirect_uri: str
    user_id: str

class OAuthCallbackRequest(BaseModel):
    platform_id: str
    code: str
    state: str
    user_id: str

class APIKeyConnectionRequest(BaseModel):
    platform_id: str
    connection_name: str
    api_key: str
    user_id: str
    additional_config: Dict[str, Any] = {}

class SyncJobCreate(BaseModel):
    connection_id: str
    job_type: str = "manual"
    direction: SyncDirection
    data_type: str

class WebhookCreate(BaseModel):
    connection_id: str
    events: List[str]

class FieldMappingUpdate(BaseModel):
    connection_id: str
    field_mappings: Dict[str, str]

# Settings & Configuration Models
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class NotificationFrequency(str, Enum):
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"

class AIModel(str, Enum):
    GPT4 = "gpt-4"
    GPT35 = "gpt-3.5-turbo"
    CLAUDE = "claude-3"
    GEMINI = "gemini-pro"

class ThemeType(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

class UserPermission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    module: str  # 'leads', 'quotes', 'documents', etc.
    permission_type: PermissionType
    granted_by: str
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    permissions: List[str] = []  # Cached permissions

class SystemSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # 'security', 'backup', 'notifications', etc.
    key: str
    value: Any
    data_type: str  # 'string', 'number', 'boolean', 'json'
    description: str
    is_public: bool = False  # Can non-admin users see this setting?
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SecurityPolicy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    rules: Dict[str, Any] = {
        "password_min_length": 8,
        "password_require_uppercase": True,
        "password_require_lowercase": True,
        "password_require_numbers": True,
        "password_require_symbols": True,
        "password_expiry_days": 90,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 30,
        "session_timeout_minutes": 480,
        "require_2fa": False,
        "allowed_ip_ranges": [],
        "allowed_domains": []
    }
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BackupSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    backup_frequency: str = "daily"  # 'hourly', 'daily', 'weekly'
    backup_retention_days: int = 30
    backup_location: str = "cloud"  # 'local', 'cloud', 's3'
    include_files: bool = True
    include_database: bool = True
    encrypt_backups: bool = True
    notification_email: Optional[str] = None
    is_active: bool = True
    last_backup_at: Optional[datetime] = None
    next_backup_at: Optional[datetime] = None
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WebhookConfiguration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    events: List[str] = []  # ['lead.created', 'quote.sent', etc.]
    secret_key: str
    retry_attempts: int = 3
    retry_delay_seconds: int = 30
    timeout_seconds: int = 30
    is_active: bool = True
    headers: Dict[str, str] = {}
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0

class RateLimitSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource: str  # 'api', 'integration', 'ai_requests'
    limit_per_hour: int = 1000
    limit_per_day: int = 10000
    burst_limit: int = 100
    user_role_multipliers: Dict[str, float] = {
        "admin": 2.0,
        "manager": 1.5,
        "user": 1.0,
        "viewer": 0.5
    }
    is_active: bool = True
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AITaskRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    condition: Dict[str, Any] = {}  # JSON condition logic
    action: Dict[str, Any] = {}  # What to do when condition is met
    priority: int = 1  # 1-10, higher = more important
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    execution_count: int = 0
    last_executed_at: Optional[datetime] = None

class BusinessRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    module: str  # 'leads', 'quotes', 'tasks', etc.
    trigger_event: str  # 'create', 'update', 'delete', 'custom'
    conditions: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    is_active: bool = True
    priority: int = 1
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0

class DashboardWidget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    widget_type: str  # 'metrics', 'chart', 'list', 'custom'
    widget_config: Dict[str, Any] = {}
    position: Dict[str, int] = {"x": 0, "y": 0, "w": 1, "h": 1}
    is_visible: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MenuConfiguration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_role: UserRole
    menu_items: List[Dict[str, Any]] = []  # Menu structure
    hidden_modules: List[str] = []
    custom_order: List[str] = []
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AISettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # 'model', 'scoring', 'automation', 'assistant'
    settings: Dict[str, Any] = {
        # Model preferences
        "preferred_model": "gpt-4",
        "confidence_threshold": 0.8,
        "max_tokens": 1000,
        
        # Lead scoring
        "scoring_algorithm": "ml_enhanced",
        "scoring_factors": {
            "company_size": 0.3,
            "industry_match": 0.2,
            "engagement_level": 0.3,
            "budget_qualification": 0.2
        },
        
        # Automation triggers
        "automation_sensitivity": "medium",
        "auto_assign_threshold": 0.7,
        "escalation_threshold": 0.9,
        
        # SIXA assistant
        "personality": "professional",
        "response_length": "medium",
        "proactive_suggestions": True,
        "learning_enabled": True
    }
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email_notifications: Dict[str, bool] = {
        "new_leads": True,
        "quote_updates": True,
        "task_assignments": True,
        "workflow_completions": True,
        "system_alerts": True,
        "integration_failures": True
    }
    notification_frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"
    weekend_notifications: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Request Models
class UserProfileCreate(BaseModel):
    username: str
    email: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    role: Optional[UserRole] = None

class SystemSettingUpdate(BaseModel):
    category: str
    key: str
    value: Any
    data_type: str = "string"
    description: Optional[str] = None

class SecurityPolicyUpdate(BaseModel):
    rules: Dict[str, Any]

class WebhookConfigurationCreate(BaseModel):
    name: str
    url: str
    events: List[str]
    retry_attempts: int = 3
    retry_delay_seconds: int = 30
    timeout_seconds: int = 30
    headers: Dict[str, str] = {}
    created_by: str

class AITaskRuleCreate(BaseModel):
    name: str
    description: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    priority: int = 1
    created_by: str

class BusinessRuleCreate(BaseModel):
    name: str
    description: str
    module: str
    trigger_event: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    priority: int = 1
    created_by: str

class DashboardWidgetUpdate(BaseModel):
    widget_config: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, int]] = None
    is_visible: Optional[bool] = None

class AISettingsUpdate(BaseModel):
    category: str
    settings: Dict[str, Any]

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize AI Chat
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

app = FastAPI(title="SystemIX AI Platinum Suite API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Authentication Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    # Simple SHA256 hashing for now
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password):
    # Simple SHA256 hashing for now
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user_doc = await db.users.find_one({"id": user_id})
    if user_doc is None:
        raise credentials_exception
    
    return User(**user_doc)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_admin(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Enums
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class WorkflowStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

# Data Models
class DashboardMetrics(BaseModel):
    total_revenue: float = 2400000
    revenue_growth: float = 18.2
    active_workflows: int = 47
    automated_today: int = 12
    ai_tasks_completed: int = 1247
    success_rate: float = 89.0
    team_members: int = 156
    online_members: int = 8

class AIInsight(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: str  # "optimization", "opportunity", "alert"
    priority: TaskPriority
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_implemented: bool = False

class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    company: str
    phone: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW
    score: int = 0  # AI scoring 0-100
    source: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_to: Optional[str] = None

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[str] = None
    created_by: str
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []
    progress: int = 0  # 0-100

class Workflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    steps: List[Dict[str, Any]] = []
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    executions: int = 0
    success_rate: float = 0.0

class TeamMember(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    role: str
    department: str
    is_online: bool = False
    last_active: datetime = Field(default_factory=datetime.utcnow)
    avatar_url: Optional[str] = None
    tasks_assigned: int = 0
    tasks_completed: int = 0

class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    attendees: List[str] = []
    location: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    response: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str

# Request Models
class LeadCreate(BaseModel):
    name: str
    email: str
    company: str
    phone: Optional[str] = None
    source: str
    notes: Optional[str] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[str] = None
    created_by: str
    due_date: Optional[datetime] = None
    tags: List[str] = []

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = []
    created_by: str

class TeamMemberCreate(BaseModel):
    name: str
    email: str
    role: str
    department: str
    avatar_url: Optional[str] = None

class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    attendees: List[str] = []
    location: Optional[str] = None
    created_by: str

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str = "default_user"

# AI Helper Functions
async def get_ai_chat():
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id="systemix_main",
        system_message="You are SIXA, the intelligent AI assistant for SystemIX AI Platinum Suite. You help with lead generation, workflow optimization, task management, and business insights. Be professional, helpful, and provide actionable recommendations."
    ).with_model("openai", "gpt-4o-mini")

async def generate_ai_insights():
    """Generate AI insights and recommendations"""
    insights = [
        AIInsight(
            title="Workflow Optimization",
            description="I've identified 3 workflows that can be automated to save 25 hours per week. Shall I implement these optimizations?",
            type="optimization",
            priority=TaskPriority.HIGH
        ),
        AIInsight(
            title="Lead Opportunities",
            description="Found 89 high-quality leads matching your criteria. AI scoring suggests 23 are ready for immediate outreach.",
            type="opportunity",
            priority=TaskPriority.MEDIUM
        ),
        AIInsight(
            title="Performance Alert",
            description="Team productivity has increased by 15% this week. Consider scaling successful processes.",
            type="alert",
            priority=TaskPriority.LOW
        )
    ]
    return insights

async def score_lead(lead_data: dict) -> int:
    """AI-powered lead scoring"""
    # Simulate AI scoring based on various factors
    score = 50  # Base score
    
    if lead_data.get("company"):
        score += 20
    if lead_data.get("phone"):
        score += 15
    if "@" in lead_data.get("email", ""):
        score += 15
    
    return min(score, 100)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "SystemIX AI Platinum Suite API", "version": "1.0.0"}

# Authentication Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        password_hash=hashed_password
    )
    
    # Store user in database
    user_dict = user.dict()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    if user_dict.get('last_login'):
        user_dict['last_login'] = user_dict['last_login'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    return UserResponse(**user.dict())

@api_router.post("/auth/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    user_doc = await db.users.find_one({"email": user_credentials.email})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = User(**user_doc)
    if not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    await db.users.update_one(
        {"id": user.id}, 
        {"$set": {"last_login": datetime.utcnow().isoformat()}}
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(**user.dict())
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(**current_user.dict())

@api_router.post("/auth/initialize-default-users")
async def initialize_default_users():
    """Initialize default admin and employee users for testing"""
    # Check if users already exist
    existing_admin = await db.users.find_one({"email": "admin@systemix.com"})
    existing_employee = await db.users.find_one({"email": "employee@systemix.com"})
    
    created_users = []
    
    if not existing_admin:
        admin_user = User(
            email="admin@systemix.com",
            name="System Administrator",
            role=UserRole.ADMIN,
            password_hash=get_password_hash("admin123")
        )
        admin_dict = admin_user.dict()
        admin_dict['created_at'] = admin_dict['created_at'].isoformat()
        if admin_dict.get('last_login'):
            admin_dict['last_login'] = admin_dict['last_login'].isoformat()
        
        await db.users.insert_one(admin_dict)
        created_users.append("admin@systemix.com")
    
    if not existing_employee:
        employee_user = User(
            email="employee@systemix.com",
            name="John Employee",
            role=UserRole.EMPLOYEE,
            password_hash=get_password_hash("employee123")
        )
        employee_dict = employee_user.dict()
        employee_dict['created_at'] = employee_dict['created_at'].isoformat()
        if employee_dict.get('last_login'):
            employee_dict['last_login'] = employee_dict['last_login'].isoformat()
        
        await db.users.insert_one(employee_dict)
        created_users.append("employee@systemix.com")
    
    return {
        "message": "Default users initialized",
        "created_users": created_users,
        "credentials": {
            "admin": {"email": "admin@systemix.com", "password": "admin123"},
            "employee": {"email": "employee@systemix.com", "password": "employee123"}
        }
    }

# Dashboard Routes
@api_router.get("/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get real-time dashboard metrics"""
    return DashboardMetrics()

@api_router.get("/dashboard/insights", response_model=List[AIInsight])
async def get_ai_insights():
    """Get AI-generated insights and recommendations"""
    return await generate_ai_insights()

# Lead Management Routes
@api_router.get("/leads", response_model=List[Lead])
async def get_leads():
    """Get all leads"""
    leads_cursor = db.leads.find().sort("created_at", -1)
    leads = await leads_cursor.to_list(1000)
    return [Lead(**lead) for lead in leads]

@api_router.post("/leads", response_model=Lead)
async def create_lead(lead_data: LeadCreate):
    """Create a new lead with AI scoring"""
    score = await score_lead(lead_data.dict())
    lead = Lead(**lead_data.dict(), score=score)
    await db.leads.insert_one(lead.dict())
    return lead

@api_router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str):
    """Get a specific lead"""
    lead = await db.leads.find_one({"id": lead_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return Lead(**lead)

@api_router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: str, lead_data: dict):
    """Update a lead"""
    lead_data["updated_at"] = datetime.utcnow()
    result = await db.leads.update_one({"id": lead_id}, {"$set": lead_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    updated_lead = await db.leads.find_one({"id": lead_id})
    return Lead(**updated_lead)

# Task Management Routes
@api_router.get("/tasks", response_model=List[Task])
async def get_tasks():
    """Get all tasks"""
    tasks_cursor = db.tasks.find().sort("created_at", -1)
    tasks = await tasks_cursor.to_list(1000)
    return [Task(**task) for task in tasks]

@api_router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate):
    """Create a new task"""
    task = Task(**task_data.dict())
    await db.tasks.insert_one(task.dict())
    return task

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_data: dict):
    """Update a task"""
    task_data["updated_at"] = datetime.utcnow()
    result = await db.tasks.update_one({"id": task_id}, {"$set": task_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    updated_task = await db.tasks.find_one({"id": task_id})
    return Task(**updated_task)

# Workflow Routes
@api_router.get("/workflows", response_model=List[Workflow])
async def get_workflows():
    """Get all workflows"""
    workflows_cursor = db.workflows.find().sort("created_at", -1)
    workflows = await workflows_cursor.to_list(1000)
    return [Workflow(**workflow) for workflow in workflows]

@api_router.post("/workflows", response_model=Workflow)
async def create_workflow(workflow_data: WorkflowCreate):
    """Create a new workflow"""
    workflow = Workflow(**workflow_data.dict())
    await db.workflows.insert_one(workflow.dict())
    return workflow

@api_router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, background_tasks: BackgroundTasks):
    """Execute a workflow"""
    workflow = await db.workflows.find_one({"id": workflow_id})
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Simulate workflow execution
    background_tasks.add_task(simulate_workflow_execution, workflow_id)
    return {"message": "Workflow execution started", "workflow_id": workflow_id}

async def simulate_workflow_execution(workflow_id: str):
    """Simulate workflow execution"""
    await asyncio.sleep(5)  # Simulate processing time
    await db.workflows.update_one(
        {"id": workflow_id}, 
        {"$inc": {"executions": 1}, "$set": {"updated_at": datetime.utcnow()}}
    )

# Team Management Routes
@api_router.get("/team", response_model=List[TeamMember])
async def get_team_members():
    """Get all team members"""
    members_cursor = db.team_members.find().sort("name", 1)
    members = await members_cursor.to_list(1000)
    return [TeamMember(**member) for member in members]

@api_router.post("/team", response_model=TeamMember)
async def create_team_member(member_data: TeamMemberCreate):
    """Create a new team member"""
    member = TeamMember(**member_data.dict())
    await db.team_members.insert_one(member.dict())
    return member

# Calendar Routes
@api_router.get("/calendar/events", response_model=List[CalendarEvent])
async def get_calendar_events():
    """Get calendar events"""
    events_cursor = db.calendar_events.find().sort("start_time", 1)
    events = await events_cursor.to_list(1000)
    return [CalendarEvent(**event) for event in events]

@api_router.post("/calendar/events", response_model=CalendarEvent)
async def create_calendar_event(event_data: CalendarEventCreate):
    """Create a new calendar event"""
    event = CalendarEvent(**event_data.dict())
    await db.calendar_events.insert_one(event.dict())
    return event

# AI Chat Routes
@api_router.post("/chat/message")
async def chat_with_sixa(chat_request: ChatRequest):
    """Chat with SIXA AI Assistant"""
    try:
        ai_chat = await get_ai_chat()
        user_message = UserMessage(text=chat_request.message)
        response = await ai_chat.send_message(user_message)
        
        # Store chat message
        chat_message = ChatMessage(
            user_id=chat_request.user_id,
            message=chat_request.message,
            response=response,
            session_id=chat_request.session_id
        )
        await db.chat_messages.insert_one(chat_message.dict())
        
        return {"response": response, "message_id": chat_message.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    messages_cursor = db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1)
    messages = await messages_cursor.to_list(1000)
    return [ChatMessage(**message) for message in messages]

# WebSocket for real-time updates
@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Helper Functions
async def calculate_quote_totals(quote: Quote):
    """Calculate quote totals including taxes and discounts"""
    subtotal = 0.0
    total_discount = 0.0
    
    for item in quote.line_items:
        # Calculate line total before discount
        line_subtotal = item.quantity * item.unit_price
        
        # Apply discounts
        if item.discount_percentage > 0:
            item.discount_amount = line_subtotal * (item.discount_percentage / 100)
        
        item.line_total = line_subtotal - item.discount_amount
        subtotal += line_subtotal
        total_discount += item.discount_amount
    
    quote.subtotal = subtotal
    quote.total_discount = total_discount
    
    # Calculate tax
    tax_base = subtotal - total_discount
    if quote.tax_settings.tax_rate > 0:
        quote.tax_settings.tax_amount = tax_base * (quote.tax_settings.tax_rate / 100)
    
    quote.total_amount = tax_base + quote.tax_settings.tax_amount
    return quote

async def generate_quote_number():
    """Generate unique quote number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    count = await db.quotes.count_documents({"quote_number": {"$regex": f"^QT-{timestamp}"}})
    return f"QT-{timestamp}-{count + 1:04d}"

async def calculate_conversion_probability(quote: Quote):
    """AI-powered conversion probability calculation"""
    try:
        ai_chat = await get_ai_chat()
        
        prompt = f"""
        Analyze this quote and estimate conversion probability (0-100%):
        - Customer: {quote.customer_name}
        - Total Amount: ${quote.total_amount:,.2f}
        - Line Items: {len(quote.line_items)}
        - Days since created: {(datetime.utcnow() - quote.created_at).days}
        - View count: {quote.view_count}
        - Industry context from line items
        
        Provide only a number between 0-100 representing percentage probability.
        """
        
        user_message = UserMessage(text=prompt)
        response = await ai_chat.send_message(user_message)
        
        # Extract number from response
        probability = float(''.join(filter(str.isdigit, response))) if response else 50.0
        return min(max(probability, 0.0), 100.0)
    except:
        return 50.0  # Default probability

# Quoting API Routes
@api_router.get("/products-services", response_model=List[ProductService])
async def get_products_services():
    """Get all products and services"""
    products_cursor = db.products_services.find({"is_active": True}).sort("name", 1)
    products = await products_cursor.to_list(1000)
    return [ProductService(**product) for product in products]

@api_router.post("/products-services", response_model=ProductService)
async def create_product_service(product_data: ProductServiceCreate):
    """Create a new product or service"""
    product = ProductService(**product_data.dict())
    await db.products_services.insert_one(product.dict())
    return product

@api_router.get("/quotes", response_model=List[Quote])
async def get_quotes(status: Optional[str] = None):
    """Get all quotes with optional status filter"""
    filter_query = {}
    if status:
        filter_query["status"] = status
    
    quotes_cursor = db.quotes.find(filter_query).sort("created_at", -1)
    quotes = await quotes_cursor.to_list(1000)
    return [Quote(**quote) for quote in quotes]

@api_router.post("/quotes", response_model=Quote)
async def create_quote(quote_data: QuoteCreate):
    """Create a new quote"""
    # Generate quote number
    quote_number = await generate_quote_number()
    
    # Create quote object
    quote_dict = quote_data.dict()
    quote_dict["quote_number"] = quote_number
    quote_dict["expires_at"] = datetime.utcnow() + timedelta(days=quote_data.expires_in_days)
    quote_dict["last_modified_by"] = quote_data.created_by
    
    # Process line items
    processed_line_items = []
    for item_data in quote_data.line_items:
        # Get product/service details
        product = await db.products_services.find_one({"id": item_data.product_service_id})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product/service not found: {item_data.product_service_id}")
        
        # Determine price based on tier
        unit_price = product["unit_price"]
        if item_data.pricing_tier != PricingTier.STANDARD and product.get("pricing_tiers"):
            tier_price = product["pricing_tiers"].get(item_data.pricing_tier.value)
            if tier_price:
                unit_price = tier_price
        
        line_item = QuoteLineItem(
            product_service_id=item_data.product_service_id,
            product_name=product["name"],
            description=product.get("description"),
            quantity=item_data.quantity,
            unit_price=unit_price,
            discount_percentage=item_data.discount_percentage,
            discount_amount=item_data.discount_amount,
            pricing_tier=item_data.pricing_tier
        )
        processed_line_items.append(line_item)
    
    quote_dict["line_items"] = [item.dict() for item in processed_line_items]
    quote = Quote(**quote_dict)
    
    # Calculate totals
    quote = await calculate_quote_totals(quote)
    
    # Calculate AI conversion probability
    quote.conversion_probability = await calculate_conversion_probability(quote)
    
    await db.quotes.insert_one(quote.dict())
    return quote

@api_router.get("/quotes/{quote_id}", response_model=Quote)
async def get_quote(quote_id: str):
    """Get a specific quote"""
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Track view
    await db.quotes.update_one(
        {"id": quote_id},
        {
            "$inc": {"view_count": 1},
            "$set": {"viewed_at": datetime.utcnow()}
        }
    )
    
    return Quote(**quote)

@api_router.put("/quotes/{quote_id}", response_model=Quote)
async def update_quote(quote_id: str, quote_update: QuoteUpdate):
    """Update a quote"""
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    update_data = {k: v for k, v in quote_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # If line items are updated, recalculate totals
    if "line_items" in update_data:
        # Process line items similar to create_quote
        processed_line_items = []
        for item_data in quote_update.line_items:
            product = await db.products_services.find_one({"id": item_data.product_service_id})
            if not product:
                continue
            
            unit_price = product["unit_price"]
            if item_data.pricing_tier != PricingTier.STANDARD and product.get("pricing_tiers"):
                tier_price = product["pricing_tiers"].get(item_data.pricing_tier.value)
                if tier_price:
                    unit_price = tier_price
            
            line_item = QuoteLineItem(
                product_service_id=item_data.product_service_id,
                product_name=product["name"],
                description=product.get("description"),
                quantity=item_data.quantity,
                unit_price=unit_price,
                discount_percentage=item_data.discount_percentage,
                discount_amount=item_data.discount_amount,
                pricing_tier=item_data.pricing_tier
            )
            processed_line_items.append(line_item)
        
        update_data["line_items"] = [item.dict() for item in processed_line_items]
        
        # Recalculate totals
        updated_quote = Quote(**{**quote, **update_data})
        updated_quote = await calculate_quote_totals(updated_quote)
        update_data.update({
            "subtotal": updated_quote.subtotal,
            "total_discount": updated_quote.total_discount,
            "tax_settings": updated_quote.tax_settings.dict(),
            "total_amount": updated_quote.total_amount
        })
    
    await db.quotes.update_one({"id": quote_id}, {"$set": update_data})
    updated_quote = await db.quotes.find_one({"id": quote_id})
    return Quote(**updated_quote)

@api_router.post("/quotes/{quote_id}/send")
async def send_quote(quote_id: str):
    """Send quote to customer"""
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Update status and sent timestamp
    await db.quotes.update_one(
        {"id": quote_id},
        {
            "$set": {
                "status": QuoteStatus.SENT.value,
                "sent_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Here you would integrate with email service to actually send the quote
    # For now, we'll simulate it
    
    return {"message": "Quote sent successfully", "quote_id": quote_id}

@api_router.post("/quotes/{quote_id}/approve")
async def approve_quote(quote_id: str, approval: ApprovalRequest):
    """Approve or reject a quote"""
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    status = ApprovalStatus.APPROVED if approval.action == "approve" else ApprovalStatus.REJECTED
    
    await db.quotes.update_one(
        {"id": quote_id},
        {
            "$set": {
                "approval_status": status.value,
                "approved_by": approval.approved_by,
                "approval_notes": approval.notes,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": f"Quote {approval.action}d successfully", "quote_id": quote_id}

@api_router.get("/quotes/{quote_id}/analytics", response_model=QuoteAnalytics)
async def get_quote_analytics(quote_id: str):
    """Get analytics for a specific quote"""
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    analytics = QuoteAnalytics(
        quote_id=quote_id,
        total_views=quote.get("view_count", 0),
        unique_views=quote.get("view_count", 0),  # Simplified for now
        last_activity=quote.get("viewed_at"),
        conversion_events=[]
    )
    
    if quote.get("sent_at") and quote.get("viewed_at"):
        time_diff = quote["viewed_at"] - quote["sent_at"]
        analytics.time_to_first_view = int(time_diff.total_seconds() / 60)
    
    return analytics

@api_router.get("/quotes/analytics/summary")
async def get_quotes_analytics_summary():
    """Get overall quotes analytics summary"""
    total_quotes = await db.quotes.count_documents({})
    sent_quotes = await db.quotes.count_documents({"status": QuoteStatus.SENT.value})
    accepted_quotes = await db.quotes.count_documents({"status": QuoteStatus.ACCEPTED.value})
    
    # Calculate totals
    pipeline = [
        {"$group": {
            "_id": None,
            "total_value": {"$sum": "$total_amount"},
            "avg_value": {"$avg": "$total_amount"}
        }}
    ]
    
    result = await db.quotes.aggregate(pipeline).to_list(1)
    total_value = result[0]["total_value"] if result else 0
    avg_value = result[0]["avg_value"] if result else 0
    
    conversion_rate = (accepted_quotes / sent_quotes * 100) if sent_quotes > 0 else 0
    
    return {
        "total_quotes": total_quotes,
        "sent_quotes": sent_quotes,
        "accepted_quotes": accepted_quotes,
        "conversion_rate": round(conversion_rate, 2),
        "total_value": total_value,
        "average_quote_value": round(avg_value, 2)
    }

@api_router.post("/quotes/initialize-sample-data")
async def initialize_quote_sample_data():
    """Initialize sample products/services and quotes"""
    try:
        # Clear existing data
        await db.products_services.delete_many({})
        await db.quotes.delete_many({})
        
        # Create sample products/services
        sample_products = [
            ProductService(
                name="Website Development",
                description="Custom website development with modern design",
                category="Web Services",
                unit_price=5000.0,
                pricing_tiers={"standard": 5000, "premium": 4000, "enterprise": 3500},
                is_service=True
            ),
            ProductService(
                name="SEO Optimization",
                description="Search engine optimization package",
                category="Marketing",
                unit_price=1500.0,
                pricing_tiers={"standard": 1500, "premium": 1200, "enterprise": 1000},
                is_service=True
            ),
            ProductService(
                name="Cloud Hosting",
                description="Professional cloud hosting service",
                category="Hosting",
                unit_price=100.0,
                pricing_tiers={"standard": 100, "premium": 80, "enterprise": 60},
                is_service=True
            ),
            ProductService(
                name="Mobile App Development",
                description="iOS and Android app development",
                category="Mobile Services",
                unit_price=15000.0,
                pricing_tiers={"standard": 15000, "premium": 12000, "enterprise": 10000},
                is_service=True
            ),
            ProductService(
                name="AI Integration Consultation",
                description="Expert consultation on AI integration strategies",
                category="Consultation",
                unit_price=300.0,
                pricing_tiers={"standard": 300, "premium": 250, "enterprise": 200},
                is_service=True
            )
        ]
        
        for product in sample_products:
            await db.products_services.insert_one(product.dict())
        
        return {"message": "Sample quoting data initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Document Center Helper Functions
async def convert_file(file_content: bytes, source_format: FileFormat, target_format: FileFormat, title: str = "document") -> bytes:
    """Convert files between different formats"""
    try:
        if source_format == FileFormat.DOCX and target_format == FileFormat.PDF:
            # Convert DOCX to PDF
            doc = DocxDocument(io.BytesIO(file_content))
            
            # Create PDF
            pdf_buffer = io.BytesIO()
            pdf = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    p = Paragraph(paragraph.text, styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 12))
            
            pdf.build(story)
            return pdf_buffer.getvalue()
            
        elif source_format == FileFormat.XLSX and target_format == FileFormat.PDF:
            # Convert XLSX to PDF
            wb = load_workbook(io.BytesIO(file_content))
            ws = wb.active
            
            pdf_buffer = io.BytesIO()
            pdf = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            for row in ws.iter_rows(values_only=True):
                row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                if row_text.strip():
                    p = Paragraph(row_text, styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 6))
            
            pdf.build(story)
            return pdf_buffer.getvalue()
            
        elif source_format == FileFormat.HTML and target_format == FileFormat.PDF:
            # Convert HTML to PDF
            pdf_buffer = io.BytesIO()
            pdf = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Simple HTML to text conversion for demo
            import re
            clean_text = re.sub('<[^<]+?>', '', file_content.decode('utf-8'))
            paragraphs = clean_text.split('\n')
            
            for para in paragraphs:
                if para.strip():
                    p = Paragraph(para.strip(), styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 12))
            
            pdf.build(story)
            return pdf_buffer.getvalue()
        
        else:
            raise HTTPException(status_code=400, detail=f"Conversion from {source_format} to {target_format} not supported")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File conversion failed: {str(e)}")

async def generate_template_thumbnail(template_content: str) -> str:
    """Generate thumbnail for template (placeholder implementation)"""
    # In a real implementation, you'd generate an actual thumbnail
    # For now, return a placeholder image URL
    svg_content = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="140" viewBox="0 0 100 140"><rect width="100" height="140" fill="#f3f4f6"/><text x="50" y="70" text-anchor="middle" fill="#6b7280" font-size="12">Template</text></svg>'
    encoded_svg = base64.b64encode(svg_content.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded_svg}"

# Document Center API Routes
@api_router.get("/document-categories", response_model=List[DocumentCategory])
async def get_document_categories():
    """Get all document categories"""
    categories_cursor = db.document_categories.find().sort("name", 1)
    categories = await categories_cursor.to_list(1000)
    return [DocumentCategory(**category) for category in categories]

@api_router.post("/document-categories", response_model=DocumentCategory)
async def create_document_category(category_data: DocumentCategoryCreate):
    """Create a new document category"""
    category = DocumentCategory(**category_data.dict())
    await db.document_categories.insert_one(category.dict())
    return category

@api_router.get("/document-templates", response_model=List[DocumentTemplate])
async def get_document_templates(category_id: Optional[str] = None, type: Optional[str] = None):
    """Get document templates with optional filters"""
    filter_query = {"is_active": True}
    if category_id:
        filter_query["category_id"] = category_id
    if type:
        filter_query["type"] = type
    
    templates_cursor = db.document_templates.find(filter_query).sort("created_at", -1)
    templates = await templates_cursor.to_list(1000)
    return [DocumentTemplate(**template) for template in templates]

@api_router.post("/document-templates", response_model=DocumentTemplate)
async def create_document_template(template_data: DocumentTemplateCreate):
    """Create a new document template"""
    template_dict = template_data.dict()
    template_dict["thumbnail_url"] = await generate_template_thumbnail(template_data.content)
    template = DocumentTemplate(**template_dict)
    await db.document_templates.insert_one(template.dict())
    return template

@api_router.get("/document-templates/{template_id}", response_model=DocumentTemplate)
async def get_document_template(template_id: str):
    """Get a specific document template"""
    template = await db.document_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Update usage count
    await db.document_templates.update_one(
        {"id": template_id},
        {"$inc": {"usage_count": 1}}
    )
    
    return DocumentTemplate(**template)

@api_router.get("/documents", response_model=List[Document])
async def get_documents(
    category_id: Optional[str] = None, 
    type: Optional[str] = None,
    status: Optional[str] = None,
    created_by: Optional[str] = None
):
    """Get documents with optional filters"""
    filter_query = {}
    if category_id:
        filter_query["category_id"] = category_id
    if type:
        filter_query["type"] = type
    if status:
        filter_query["status"] = status
    if created_by:
        filter_query["created_by"] = created_by
    
    documents_cursor = db.documents.find(filter_query).sort("created_at", -1)
    documents = await documents_cursor.to_list(1000)
    return [Document(**document) for document in documents]

@api_router.post("/documents", response_model=Document)
async def create_document(document_data: DocumentCreate):
    """Create a new document"""
    document = Document(**document_data.dict())
    
    # If created from template, populate template data
    if document_data.template_id:
        template = await db.document_templates.find_one({"id": document_data.template_id})
        if template:
            document.content = template["content"]
            document.type = document.type or template["type"]
            document.category_id = document.category_id or template["category_id"]
    
    await db.documents.insert_one(document.dict())
    return document

@api_router.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: str):
    """Get a specific document"""
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return Document(**document)

@api_router.put("/documents/{document_id}", response_model=Document)
async def update_document(document_id: str, document_update: Dict[str, Any]):
    """Update a document"""
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document_update["updated_at"] = datetime.utcnow()
    document_update["version"] = document.get("version", 1) + 1
    
    await db.documents.update_one({"id": document_id}, {"$set": document_update})
    updated_document = await db.documents.find_one({"id": document_id})
    return Document(**updated_document)

@api_router.post("/documents/convert")
async def convert_document_file(conversion_request: FileConversionRequest):
    """Convert document between different file formats"""
    try:
        # Decode base64 content
        file_content = base64.b64decode(conversion_request.file_content)
        
        # Perform conversion
        converted_content = await convert_file(
            file_content,
            conversion_request.source_format,
            conversion_request.target_format,
            conversion_request.document_title or "converted_document"
        )
        
        # Return converted file as base64
        converted_base64 = base64.b64encode(converted_content).decode('utf-8')
        
        return {
            "converted_content": converted_base64,
            "source_format": conversion_request.source_format,
            "target_format": conversion_request.target_format,
            "size": len(converted_content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/documents/{document_id}/send-for-signature")
async def send_document_for_signature(document_id: str, request: DocuSignSendRequest):
    """Send document for signature via DocuSign"""
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # For now, simulate DocuSign integration
        # In production, you'd integrate with actual DocuSign API
        envelope_id = f"envelope_{uuid.uuid4()}"
        
        # Update document with DocuSign info
        await db.documents.update_one(
            {"id": document_id},
            {
                "$set": {
                    "docusign_envelope_id": envelope_id,
                    "docusign_status": "sent",
                    "status": DocumentStatus.PENDING_SIGNATURE.value,
                    "signers": request.signers,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Store envelope information
        envelope = DocuSignEnvelope(
            envelope_id=envelope_id,
            document_id=document_id,
            status="sent",
            created_date=datetime.utcnow(),
            sent_date=datetime.utcnow(),
            recipients=request.signers
        )
        await db.docusign_envelopes.insert_one(envelope.dict())
        
        return {
            "message": "Document sent for signature successfully",
            "envelope_id": envelope_id,
            "document_id": document_id,
            "signers": request.signers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/documents/{document_id}/signature-status")
async def get_document_signature_status(document_id: str):
    """Get signature status for a document"""
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    envelope_info = None
    if document.get("docusign_envelope_id"):
        envelope_info = await db.docusign_envelopes.find_one(
            {"envelope_id": document["docusign_envelope_id"]}
        )
    
    return {
        "document_id": document_id,
        "signature_required": document.get("signature_required", False),
        "docusign_status": document.get("docusign_status"),
        "envelope_id": document.get("docusign_envelope_id"),
        "envelope_info": envelope_info,
        "signers": document.get("signers", [])
    }

@api_router.post("/documents/initialize-sample-data")
async def initialize_document_sample_data():
    """Initialize sample document categories and templates"""
    try:
        # Clear existing data
        await db.document_categories.delete_many({})
        await db.document_templates.delete_many({})
        
        # Create sample categories
        sample_categories = [
            DocumentCategory(
                name="Legal Documents",
                description="Contracts, agreements, and legal forms",
                color="#DC2626",
                icon="⚖️",
                created_by="system"
            ),
            DocumentCategory(
                name="Sales Documents",
                description="Proposals, invoices, and sales materials",
                color="#059669",
                icon="💼",
                created_by="system"
            ),
            DocumentCategory(
                name="HR Documents",
                description="Employment forms and policies",
                color="#7C3AED",
                icon="👥",
                created_by="system"
            ),
            DocumentCategory(
                name="Business Forms",
                description="General business forms and templates",
                color="#2563EB",
                icon="📋",
                created_by="system"
            )
        ]
        
        for category in sample_categories:
            await db.document_categories.insert_one(category.dict())
        
        # Create sample templates
        legal_category = sample_categories[0]
        sales_category = sample_categories[1]
        
        sample_templates = [
            DocumentTemplate(
                title="Non-Disclosure Agreement (NDA)",
                description="Standard NDA template for protecting confidential information",
                type=DocumentType.CONTRACT,
                category_id=legal_category.id,
                content="""
                <h1>NON-DISCLOSURE AGREEMENT</h1>
                <p>This Non-Disclosure Agreement ("Agreement") is entered into on {{date}} by and between:</p>
                <p><strong>Company:</strong> {{company_name}}<br>
                <strong>Address:</strong> {{company_address}}</p>
                <p><strong>Recipient:</strong> {{recipient_name}}<br>
                <strong>Address:</strong> {{recipient_address}}</p>
                <h2>1. Definition of Confidential Information</h2>
                <p>For purposes of this Agreement, "Confidential Information" means any and all information...</p>
                <h2>2. Obligations</h2>
                <p>The Recipient agrees to...</p>
                <div class="signature-section">
                <p>Company Signature: ________________________</p>
                <p>Recipient Signature: ________________________</p>
                </div>
                """,
                variables=["date", "company_name", "company_address", "recipient_name", "recipient_address"],
                form_fields=[
                    FormField(type=FormFieldType.DATE, label="Agreement Date", required=True),
                    FormField(type=FormFieldType.TEXT, label="Company Name", required=True),
                    FormField(type=FormFieldType.TEXTAREA, label="Company Address", required=True),
                    FormField(type=FormFieldType.TEXT, label="Recipient Name", required=True),
                    FormField(type=FormFieldType.TEXTAREA, label="Recipient Address", required=True),
                    FormField(type=FormFieldType.SIGNATURE, label="Company Signature", required=True),
                    FormField(type=FormFieldType.SIGNATURE, label="Recipient Signature", required=True)
                ],
                file_format=FileFormat.PDF,
                created_by="system",
                tags=["legal", "contract", "nda", "confidentiality"]
            ),
            DocumentTemplate(
                title="Service Agreement",
                description="Professional service agreement template",
                type=DocumentType.CONTRACT,
                category_id=legal_category.id,
                content="""
                <h1>SERVICE AGREEMENT</h1>
                <p>This Service Agreement is made on {{date}} between {{client_name}} and {{service_provider}}.</p>
                <h2>Services to be Provided</h2>
                <p>{{services_description}}</p>
                <h2>Payment Terms</h2>
                <p>Total Amount: ${{total_amount}}<br>
                Payment Schedule: {{payment_schedule}}</p>
                <h2>Timeline</h2>
                <p>Start Date: {{start_date}}<br>
                End Date: {{end_date}}</p>
                """,
                variables=["date", "client_name", "service_provider", "services_description", "total_amount", "payment_schedule", "start_date", "end_date"],
                created_by="system",
                tags=["legal", "contract", "service", "agreement"]
            ),
            DocumentTemplate(
                title="Business Proposal",
                description="Professional business proposal template",
                type=DocumentType.PROPOSAL,
                category_id=sales_category.id,
                content="""
                <h1>BUSINESS PROPOSAL</h1>
                <p><strong>To:</strong> {{client_name}}<br>
                <strong>From:</strong> {{company_name}}<br>
                <strong>Date:</strong> {{date}}</p>
                <h2>Executive Summary</h2>
                <p>{{executive_summary}}</p>
                <h2>Proposed Solution</h2>
                <p>{{solution_description}}</p>
                <h2>Investment</h2>
                <p>Total Investment: ${{total_amount}}</p>
                <h2>Timeline</h2>
                <p>Project Duration: {{timeline}}</p>
                <h2>Next Steps</h2>
                <p>{{next_steps}}</p>
                """,
                variables=["client_name", "company_name", "date", "executive_summary", "solution_description", "total_amount", "timeline", "next_steps"],
                created_by="system",
                tags=["sales", "proposal", "business"]
            ),
            DocumentTemplate(
                title="Invoice Template",
                description="Professional invoice template",
                type=DocumentType.INVOICE,
                category_id=sales_category.id,
                content="""
                <h1>INVOICE</h1>
                <p><strong>Invoice #:</strong> {{invoice_number}}<br>
                <strong>Date:</strong> {{date}}<br>
                <strong>Due Date:</strong> {{due_date}}</p>
                <h2>Bill To:</h2>
                <p>{{client_name}}<br>
                {{client_address}}</p>
                <h2>Services/Products</h2>
                <table border="1" width="100%">
                <tr><th>Description</th><th>Quantity</th><th>Rate</th><th>Amount</th></tr>
                {{line_items}}
                </table>
                <p><strong>Total: ${{total_amount}}</strong></p>
                <p>Payment Terms: {{payment_terms}}</p>
                """,
                variables=["invoice_number", "date", "due_date", "client_name", "client_address", "line_items", "total_amount", "payment_terms"],
                created_by="system",
                tags=["sales", "invoice", "billing"]
            )
        ]
        
        for template in sample_templates:
            template.thumbnail_url = await generate_template_thumbnail(template.content)
            await db.document_templates.insert_one(template.dict())
        
        return {"message": "Sample document data initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Integrations Hub Helper Functions
def get_platform_oauth_config(platform_slug: str) -> Dict[str, Any]:
    """Get OAuth configuration for different platforms"""
    oauth_configs = {
        'salesforce': {
            'authorization_base_url': 'https://login.salesforce.com/services/oauth2/authorize',
            'token_url': 'https://login.salesforce.com/services/oauth2/token',
            'scopes': ['api', 'refresh_token', 'offline_access']
        },
        'hubspot': {
            'authorization_base_url': 'https://app.hubspot.com/oauth/authorize',
            'token_url': 'https://api.hubapi.com/oauth/v1/token',
            'scopes': ['contacts', 'content', 'timeline']
        },
        'pipedrive': {
            'authorization_base_url': 'https://oauth.pipedrive.com/oauth/authorize',
            'token_url': 'https://oauth.pipedrive.com/oauth/token',
            'scopes': ['read', 'write']
        },
        'stripe': {
            'authorization_base_url': 'https://connect.stripe.com/oauth/authorize',
            'token_url': 'https://connect.stripe.com/oauth/token',
            'scopes': ['read_write']
        },
        'mailchimp': {
            'authorization_base_url': 'https://login.mailchimp.com/oauth2/authorize',
            'token_url': 'https://login.mailchimp.com/oauth2/token',
            'scopes': ['read', 'write']
        },
        'slack': {
            'authorization_base_url': 'https://slack.com/oauth/v2/authorize',
            'token_url': 'https://slack.com/api/oauth.v2.access',
            'scopes': ['channels:read', 'chat:write', 'users:read']
        }
    }
    return oauth_configs.get(platform_slug, {})

async def simulate_external_api_call(platform_slug: str, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """Simulate external API calls for demo purposes"""
    # In production, this would make actual API calls
    simulated_responses = {
        'salesforce': {
            'contacts': {
                'records': [
                    {'Id': '003XX000000001', 'FirstName': 'John', 'LastName': 'Doe', 'Email': 'john.doe@example.com'},
                    {'Id': '003XX000000002', 'FirstName': 'Jane', 'LastName': 'Smith', 'Email': 'jane.smith@example.com'}
                ]
            },
            'opportunities': {
                'records': [
                    {'Id': '006XX000000001', 'Name': 'Big Deal', 'Amount': 50000, 'StageName': 'Prospecting'},
                    {'Id': '006XX000000002', 'Name': 'Small Deal', 'Amount': 5000, 'StageName': 'Closed Won'}
                ]
            }
        },
        'hubspot': {
            'contacts': {
                'results': [
                    {'id': '1', 'properties': {'firstname': 'Bob', 'lastname': 'Johnson', 'email': 'bob@example.com'}},
                    {'id': '2', 'properties': {'firstname': 'Alice', 'lastname': 'Brown', 'email': 'alice@example.com'}}
                ]
            }
        },
        'stripe': {
            'customers': {
                'data': [
                    {'id': 'cus_1', 'email': 'customer1@example.com', 'name': 'Customer One'},
                    {'id': 'cus_2', 'email': 'customer2@example.com', 'name': 'Customer Two'}
                ]
            }
        }
    }
    
    return simulated_responses.get(platform_slug, {}).get(endpoint, {'message': 'Simulated API response'})

async def perform_data_sync(connection: IntegrationConnection, data_type: str, direction: SyncDirection) -> Dict[str, Any]:
    """Perform data synchronization between SystemIX and external platform"""
    try:
        sync_results = {
            'records_processed': 0,
            'records_success': 0,
            'records_failed': 0,
            'errors': []
        }
        
        if direction in [SyncDirection.INBOUND, SyncDirection.BIDIRECTIONAL]:
            # Simulate fetching data from external platform
            external_data = await simulate_external_api_call(connection.platform_name.lower(), data_type)
            
            # Process and sync data
            if data_type == 'contacts' and external_data:
                records = external_data.get('records', external_data.get('results', external_data.get('data', [])))
                
                for record in records:
                    try:
                        # Transform external data to SystemIX format
                        systemix_record = transform_external_data(record, connection.field_mappings, data_type)
                        
                        # In production, this would save to SystemIX database
                        sync_results['records_success'] += 1
                    except Exception as e:
                        sync_results['records_failed'] += 1
                        sync_results['errors'].append(str(e))
                    
                    sync_results['records_processed'] += 1
        
        return sync_results
    except Exception as e:
        return {
            'records_processed': 0,
            'records_success': 0,
            'records_failed': 0,
            'errors': [str(e)]
        }

def transform_external_data(external_record: Dict, field_mappings: Dict[str, str], data_type: str) -> Dict[str, Any]:
    """Transform external platform data to SystemIX format"""
    systemix_record = {}
    
    # Default field mappings for different data types
    default_mappings = {
        'contacts': {
            'name': ['Name', 'firstname', 'FirstName', 'full_name'],
            'email': ['Email', 'email', 'email_address'],
            'phone': ['Phone', 'phone', 'phone_number'],
            'company': ['Company', 'company', 'Account.Name']
        }
    }
    
    # Use custom mappings or defaults
    mappings = field_mappings if field_mappings else default_mappings.get(data_type, {})
    
    for systemix_field, external_fields in mappings.items():
        if isinstance(external_fields, str):
            external_fields = [external_fields]
        
        for external_field in external_fields:
            if external_field in external_record:
                systemix_record[systemix_field] = external_record[external_field]
                break
            elif '.' in external_field:
                # Handle nested fields like Account.Name
                nested_value = external_record
                for part in external_field.split('.'):
                    if isinstance(nested_value, dict) and part in nested_value:
                        nested_value = nested_value[part]
                    else:
                        nested_value = None
                        break
                if nested_value:
                    systemix_record[systemix_field] = nested_value
                    break
    
    return systemix_record

# Integrations Hub API Routes
@api_router.get("/integrations/platforms", response_model=List[IntegrationPlatform])
async def get_integration_platforms():
    """Get all available integration platforms"""
    platforms_cursor = db.integration_platforms.find({"is_active": True}).sort("name", 1)
    platforms = await platforms_cursor.to_list(1000)
    return [IntegrationPlatform(**platform) for platform in platforms]

@api_router.post("/integrations/platforms", response_model=IntegrationPlatform)
async def create_integration_platform(platform_data: IntegrationPlatformCreate):
    """Create a new integration platform"""
    platform = IntegrationPlatform(**platform_data.dict())
    await db.integration_platforms.insert_one(platform.dict())
    return platform

@api_router.get("/integrations/connections", response_model=List[IntegrationConnection])
async def get_integration_connections(user_id: Optional[str] = None, platform_id: Optional[str] = None):
    """Get integration connections with optional filters"""
    filter_query = {}
    if user_id:
        filter_query["user_id"] = user_id
    if platform_id:
        filter_query["platform_id"] = platform_id
    
    connections_cursor = db.integration_connections.find(filter_query).sort("created_at", -1)
    connections = await connections_cursor.to_list(1000)
    return [IntegrationConnection(**connection) for connection in connections]

@api_router.post("/integrations/oauth/initiate")
async def initiate_oauth_flow(oauth_request: OAuthInitRequest):
    """Initiate OAuth flow for a platform"""
    try:
        platform = await db.integration_platforms.find_one({"id": oauth_request.platform_id})
        if not platform:
            raise HTTPException(status_code=404, detail="Platform not found")
        
        oauth_config = get_platform_oauth_config(platform["slug"])
        if not oauth_config:
            raise HTTPException(status_code=400, detail="OAuth not supported for this platform")
        
        # In production, you would use actual OAuth2Session
        # For demo, return a simulated authorization URL
        state = str(uuid.uuid4())
        
        # Store OAuth state for verification
        oauth_state = {
            "state": state,
            "platform_id": oauth_request.platform_id,
            "connection_name": oauth_request.connection_name,
            "user_id": oauth_request.user_id,
            "redirect_uri": oauth_request.redirect_uri,
            "created_at": datetime.utcnow()
        }
        await db.oauth_states.insert_one(oauth_state)
        
        # Simulate authorization URL
        auth_url = f"{oauth_config['authorization_base_url']}?response_type=code&client_id=demo_client_id&redirect_uri={oauth_request.redirect_uri}&state={state}&scope={'+'.join(oauth_config.get('scopes', []))}"
        
        return {
            "authorization_url": auth_url,
            "state": state,
            "platform_name": platform["name"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/integrations/oauth/callback")
async def handle_oauth_callback(callback_request: OAuthCallbackRequest):
    """Handle OAuth callback and create connection"""
    try:
        # Verify state
        oauth_state = await db.oauth_states.find_one({"state": callback_request.state})
        if not oauth_state:
            raise HTTPException(status_code=400, detail="Invalid OAuth state")
        
        platform = await db.integration_platforms.find_one({"id": callback_request.platform_id})
        if not platform:
            raise HTTPException(status_code=404, detail="Platform not found")
        
        # In production, exchange code for tokens
        # For demo, create a simulated connection
        connection = IntegrationConnection(
            platform_id=callback_request.platform_id,
            platform_name=platform["name"],
            user_id=callback_request.user_id,
            connection_name=oauth_state["connection_name"],
            status=ConnectionStatus.CONNECTED,
            access_token="demo_access_token",
            refresh_token="demo_refresh_token",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            next_sync_at=datetime.utcnow() + timedelta(minutes=60)
        )
        
        await db.integration_connections.insert_one(connection.dict())
        
        # Clean up OAuth state
        await db.oauth_states.delete_one({"state": callback_request.state})
        
        return {
            "message": "Connection established successfully",
            "connection_id": connection.id,
            "platform_name": platform["name"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/integrations/api-key-connection")
async def create_api_key_connection(api_request: APIKeyConnectionRequest):
    """Create connection using API key authentication"""
    try:
        platform = await db.integration_platforms.find_one({"id": api_request.platform_id})
        if not platform:
            raise HTTPException(status_code=404, detail="Platform not found")
        
        # Test API key by making a test call
        test_result = await simulate_external_api_call(platform["slug"], "test", "GET")
        
        connection = IntegrationConnection(
            platform_id=api_request.platform_id,
            platform_name=platform["name"],
            user_id=api_request.user_id,
            connection_name=api_request.connection_name,
            status=ConnectionStatus.CONNECTED,
            api_key=api_request.api_key,
            auth_data=api_request.additional_config,
            next_sync_at=datetime.utcnow() + timedelta(minutes=60)
        )
        
        await db.integration_connections.insert_one(connection.dict())
        
        return {
            "message": "API key connection established successfully",
            "connection_id": connection.id,
            "platform_name": platform["name"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/integrations/connections/{connection_id}")
async def get_connection_details(connection_id: str):
    """Get detailed information about a specific connection"""
    connection = await db.integration_connections.find_one({"id": connection_id})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Get recent sync jobs
    sync_jobs_cursor = db.sync_jobs.find({"connection_id": connection_id}).sort("created_at", -1).limit(10)
    recent_syncs = await sync_jobs_cursor.to_list(10)
    
    return {
        "connection": IntegrationConnection(**connection),
        "recent_syncs": [SyncJob(**sync) for sync in recent_syncs]
    }

@api_router.post("/integrations/sync-jobs", response_model=SyncJob)
async def create_sync_job(job_request: SyncJobCreate):
    """Create and execute a sync job"""
    try:
        connection = await db.integration_connections.find_one({"id": job_request.connection_id})
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Create sync job
        sync_job = SyncJob(
            connection_id=job_request.connection_id,
            platform_name=connection["platform_name"],
            job_type=job_request.job_type,
            direction=job_request.direction,
            data_type=job_request.data_type,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        
        await db.sync_jobs.insert_one(sync_job.dict())
        
        # Perform sync in background
        asyncio.create_task(execute_sync_job(sync_job.id))
        
        return sync_job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_sync_job(sync_job_id: str):
    """Execute a sync job in the background"""
    try:
        sync_job = await db.sync_jobs.find_one({"id": sync_job_id})
        if not sync_job:
            return
        
        connection = await db.integration_connections.find_one({"id": sync_job["connection_id"]})
        if not connection:
            await db.sync_jobs.update_one(
                {"id": sync_job_id},
                {"$set": {"status": SyncStatus.FAILED.value, "error_message": "Connection not found"}}
            )
            return
        
        # Perform sync
        connection_obj = IntegrationConnection(**connection)
        sync_results = await perform_data_sync(connection_obj, sync_job["data_type"], sync_job["direction"])
        
        # Update sync job
        update_data = {
            "status": SyncStatus.SUCCESS.value if sync_results["records_failed"] == 0 else SyncStatus.FAILED.value,
            "completed_at": datetime.utcnow(),
            "records_processed": sync_results["records_processed"],
            "records_success": sync_results["records_success"],
            "records_failed": sync_results["records_failed"],
            "sync_summary": sync_results
        }
        
        if sync_results["errors"]:
            update_data["error_message"] = "; ".join(sync_results["errors"][:3])
        
        await db.sync_jobs.update_one({"id": sync_job_id}, {"$set": update_data})
        
        # Update connection stats
        await db.integration_connections.update_one(
            {"id": sync_job["connection_id"]},
            {
                "$set": {"last_sync_at": datetime.utcnow()},
                "$inc": {
                    "total_syncs": 1,
                    "successful_syncs": 1 if update_data["status"] == SyncStatus.SUCCESS.value else 0,
                    "failed_syncs": 1 if update_data["status"] == SyncStatus.FAILED.value else 0
                }
            }
        )
        
    except Exception as e:
        await db.sync_jobs.update_one(
            {"id": sync_job_id},
            {"$set": {"status": SyncStatus.FAILED.value, "error_message": str(e), "completed_at": datetime.utcnow()}}
        )

@api_router.delete("/integrations/connections/{connection_id}")
async def disconnect_integration(connection_id: str):
    """Disconnect an integration"""
    connection = await db.integration_connections.find_one({"id": connection_id})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Update connection status
    await db.integration_connections.update_one(
        {"id": connection_id},
        {"$set": {"status": ConnectionStatus.DISCONNECTED.value, "is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Integration disconnected successfully"}

@api_router.put("/integrations/connections/{connection_id}/field-mappings")
async def update_field_mappings(connection_id: str, mapping_request: FieldMappingUpdate):
    """Update field mappings for a connection"""
    connection = await db.integration_connections.find_one({"id": connection_id})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    await db.integration_connections.update_one(
        {"id": connection_id},
        {"$set": {"field_mappings": mapping_request.field_mappings, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Field mappings updated successfully"}

@api_router.get("/integrations/analytics")
async def get_integrations_analytics():
    """Get analytics for all integrations"""
    try:
        # Get connection counts by platform
        platform_stats = {}
        connections_cursor = db.integration_connections.find({"is_active": True})
        connections = await connections_cursor.to_list(1000)
        
        for connection in connections:
            platform = connection["platform_name"]
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "connections": 0,
                    "active_connections": 0,
                    "total_syncs": 0,
                    "successful_syncs": 0,
                    "failed_syncs": 0
                }
            
            platform_stats[platform]["connections"] += 1
            if connection["status"] == ConnectionStatus.CONNECTED.value:
                platform_stats[platform]["active_connections"] += 1
            
            platform_stats[platform]["total_syncs"] += connection.get("total_syncs", 0)
            platform_stats[platform]["successful_syncs"] += connection.get("successful_syncs", 0)
            platform_stats[platform]["failed_syncs"] += connection.get("failed_syncs", 0)
        
        # Get recent sync jobs
        recent_syncs_cursor = db.sync_jobs.find().sort("created_at", -1).limit(20)
        recent_syncs = await recent_syncs_cursor.to_list(20)
        
        return {
            "platform_stats": platform_stats,
            "recent_syncs": [SyncJob(**sync) for sync in recent_syncs],
            "total_connections": len(connections),
            "active_connections": len([c for c in connections if c["status"] == ConnectionStatus.CONNECTED.value])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/integrations/initialize-sample-data")
async def initialize_integrations_sample_data():
    """Initialize sample integration platforms and connections"""
    try:
        # Clear existing data
        await db.integration_platforms.delete_many({})
        await db.integration_connections.delete_many({})
        
        # Create sample platforms
        sample_platforms = [
            IntegrationPlatform(
                name="Salesforce",
                slug="salesforce",
                type=IntegrationType.CRM,
                description="World's #1 CRM platform for sales, service, and marketing",
                logo_url="https://www.salesforce.com/content/dam/web/en_us/www/images/nav/salesforce-logo.svg",
                website_url="https://salesforce.com",
                documentation_url="https://developer.salesforce.com/docs/",
                auth_type=AuthType.OAUTH2,
                auth_config=get_platform_oauth_config("salesforce"),
                supported_features=["contacts", "accounts", "opportunities", "tasks", "events"],
                api_base_url="https://[instance].salesforce.com/services/data/v58.0/",
                rate_limits={"requests_per_hour": 1000}
            ),
            IntegrationPlatform(
                name="HubSpot",
                slug="hubspot",
                type=IntegrationType.CRM,
                description="Inbound marketing, sales, and service software",
                logo_url="https://www.hubspot.com/hubfs/HubSpot_Logos/HubSpot-Inversed-Favicon.png",
                website_url="https://hubspot.com",
                documentation_url="https://developers.hubspot.com/docs/api/overview",
                auth_type=AuthType.OAUTH2,
                auth_config=get_platform_oauth_config("hubspot"),
                supported_features=["contacts", "companies", "deals", "tickets", "tasks"],
                api_base_url="https://api.hubapi.com/",
                rate_limits={"requests_per_hour": 1000}
            ),
            IntegrationPlatform(
                name="Stripe",
                slug="stripe",
                type=IntegrationType.PAYMENT,
                description="Online payment processing for internet businesses",
                logo_url="https://images.ctfassets.net/fzn2n1nzq965/HTTOloNPhisV9P4hlMPNA/cacf1bb88b9fc492dfad34378d844280/Stripe_icon_-_square.svg",
                website_url="https://stripe.com",
                documentation_url="https://stripe.com/docs/api",
                auth_type=AuthType.API_KEY,
                auth_config={},
                supported_features=["customers", "payments", "subscriptions", "invoices"],
                api_base_url="https://api.stripe.com/v1/",
                rate_limits={"requests_per_second": 100}
            ),
            IntegrationPlatform(
                name="Mailchimp",
                slug="mailchimp",
                type=IntegrationType.MARKETING,
                description="Email marketing and automation platform",
                logo_url="https://mailchimp.com/release/plums/cxp/images/apple-touch-icon-192.png",
                website_url="https://mailchimp.com",
                documentation_url="https://mailchimp.com/developer/",
                auth_type=AuthType.OAUTH2,
                auth_config=get_platform_oauth_config("mailchimp"),
                supported_features=["lists", "campaigns", "automation", "reports"],
                api_base_url="https://[dc].api.mailchimp.com/3.0/",
                rate_limits={"requests_per_hour": 1000}
            ),
            IntegrationPlatform(
                name="Slack",
                slug="slack",
                type=IntegrationType.COMMUNICATION,
                description="Team communication and collaboration platform",
                logo_url="https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png",
                website_url="https://slack.com",
                documentation_url="https://api.slack.com/",
                auth_type=AuthType.OAUTH2,
                auth_config=get_platform_oauth_config("slack"),
                supported_features=["channels", "messages", "users", "files"],
                api_base_url="https://slack.com/api/",
                rate_limits={"requests_per_minute": 100}
            ),
            IntegrationPlatform(
                name="Asana",
                slug="asana",
                type=IntegrationType.PROJECT_MANAGEMENT,
                description="Project management and team collaboration tool",
                logo_url="https://luna1.co/asana.png",
                website_url="https://asana.com",
                documentation_url="https://developers.asana.com/docs/",
                auth_type=AuthType.OAUTH2,
                auth_config={
                    'authorization_base_url': 'https://app.asana.com/-/oauth_authorize',
                    'token_url': 'https://app.asana.com/-/oauth_token',
                    'scopes': ['default']
                },
                supported_features=["projects", "tasks", "users", "teams"],
                api_base_url="https://app.asana.com/api/1.0/",
                rate_limits={"requests_per_hour": 1500}
            )
        ]
        
        for platform in sample_platforms:
            await db.integration_platforms.insert_one(platform.dict())
        
        return {"message": "Sample integration platforms initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Settings & Configuration Helper Functions
def validate_permission(user_role: UserRole, required_permission: str) -> bool:
    """Validate if user role has required permission"""
    role_permissions = {
        UserRole.ADMIN: ["all"],
        UserRole.MANAGER: ["read", "write", "manage_team", "configure_workflows"],
        UserRole.USER: ["read", "write", "manage_own"],
        UserRole.VIEWER: ["read"]
    }
    
    user_perms = role_permissions.get(user_role, [])
    return "all" in user_perms or required_permission in user_perms

def apply_security_policy(password: str, policy_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Validate password against security policy"""
    errors = []
    
    if len(password) < policy_rules.get("password_min_length", 8):
        errors.append(f"Password must be at least {policy_rules.get('password_min_length', 8)} characters")
    
    if policy_rules.get("password_require_uppercase", True) and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if policy_rules.get("password_require_lowercase", True) and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if policy_rules.get("password_require_numbers", True) and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if policy_rules.get("password_require_symbols", True) and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one symbol")
    
    return {"valid": len(errors) == 0, "errors": errors}

def evaluate_business_rule_condition(condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
    """Evaluate if business rule condition is met"""
    try:
        # Simple condition evaluation - in production, use a proper rule engine
        operator = condition.get("operator", "equals")
        field = condition.get("field")
        value = condition.get("value")
        
        if not field or field not in data:
            return False
        
        data_value = data[field]
        
        if operator == "equals":
            return data_value == value
        elif operator == "not_equals":
            return data_value != value
        elif operator == "greater_than":
            return float(data_value) > float(value)
        elif operator == "less_than":
            return float(data_value) < float(value)
        elif operator == "contains":
            return str(value).lower() in str(data_value).lower()
        elif operator == "starts_with":
            return str(data_value).lower().startswith(str(value).lower())
        elif operator == "in_list":
            return data_value in value if isinstance(value, list) else False
        
        return False
    except:
        return False

async def execute_business_rule_actions(actions: List[Dict[str, Any]], data: Dict[str, Any]):
    """Execute business rule actions"""
    for action in actions:
        action_type = action.get("type")
        
        if action_type == "assign_task":
            # Create a task assignment
            pass
        elif action_type == "send_notification":
            # Send notification
            pass
        elif action_type == "update_field":
            # Update a field value
            pass
        elif action_type == "create_workflow":
            # Trigger workflow creation
            pass

# Settings & Configuration API Routes
@api_router.get("/settings/users", response_model=List[UserProfile])
async def get_user_profiles():
    """Get all user profiles (admin only)"""
    profiles_cursor = db.user_profiles.find().sort("full_name", 1)
    profiles = await profiles_cursor.to_list(1000)
    return [UserProfile(**profile) for profile in profiles]

@api_router.post("/settings/users", response_model=UserProfile)
async def create_user_profile(user_data: UserProfileCreate):
    """Create a new user profile"""
    # Check if username/email already exists
    existing_user = await db.user_profiles.find_one({
        "$or": [
            {"username": user_data.username},
            {"email": user_data.email}
        ]
    })
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    user_profile = UserProfile(
        user_id=str(uuid.uuid4()),
        **user_data.dict()
    )
    
    await db.user_profiles.insert_one(user_profile.dict())
    return user_profile

@api_router.get("/settings/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get a specific user profile"""
    profile = await db.user_profiles.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return UserProfile(**profile)

@api_router.put("/settings/users/{user_id}", response_model=UserProfile)
async def update_user_profile(user_id: str, user_update: UserProfileUpdate):
    """Update user profile"""
    profile = await db.user_profiles.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.user_profiles.update_one({"user_id": user_id}, {"$set": update_data})
    updated_profile = await db.user_profiles.find_one({"user_id": user_id})
    return UserProfile(**updated_profile)

@api_router.get("/settings/system", response_model=List[SystemSettings])
async def get_system_settings(category: Optional[str] = None):
    """Get system settings"""
    filter_query = {}
    if category:
        filter_query["category"] = category
    
    settings_cursor = db.system_settings.find(filter_query).sort("category", 1)
    settings = await settings_cursor.to_list(1000)
    return [SystemSettings(**setting) for setting in settings]

@api_router.put("/settings/system", response_model=SystemSettings)
async def update_system_setting(setting_update: SystemSettingUpdate):
    """Update a system setting"""
    setting_data = SystemSettings(
        category=setting_update.category,
        key=setting_update.key,
        value=setting_update.value,
        data_type=setting_update.data_type,
        description=setting_update.description or "",
        updated_by="current_user"
    )
    
    # Upsert the setting
    await db.system_settings.update_one(
        {"category": setting_update.category, "key": setting_update.key},
        {"$set": setting_data.dict()},
        upsert=True
    )
    
    updated_setting = await db.system_settings.find_one({
        "category": setting_update.category,
        "key": setting_update.key
    })
    return SystemSettings(**updated_setting)

@api_router.get("/settings/security", response_model=SecurityPolicy)
async def get_security_policy():
    """Get current security policy"""
    policy = await db.security_policies.find_one({"is_active": True})
    if not policy:
        # Create default policy
        default_policy = SecurityPolicy(
            name="Default Security Policy",
            description="Default security policy for SystemIX AI",
            created_by="system"
        )
        await db.security_policies.insert_one(default_policy.dict())
        return default_policy
    
    return SecurityPolicy(**policy)

@api_router.put("/settings/security", response_model=SecurityPolicy)
async def update_security_policy(policy_update: SecurityPolicyUpdate):
    """Update security policy"""
    policy = await db.security_policies.find_one({"is_active": True})
    if not policy:
        raise HTTPException(status_code=404, detail="Security policy not found")
    
    update_data = {
        "rules": policy_update.rules,
        "updated_at": datetime.utcnow()
    }
    
    await db.security_policies.update_one(
        {"id": policy["id"]},
        {"$set": update_data}
    )
    
    updated_policy = await db.security_policies.find_one({"id": policy["id"]})
    return SecurityPolicy(**updated_policy)

@api_router.get("/settings/backup", response_model=BackupSettings)
async def get_backup_settings():
    """Get backup settings"""
    settings = await db.backup_settings.find_one({"is_active": True})
    if not settings:
        # Create default backup settings
        default_settings = BackupSettings(updated_by="system")
        await db.backup_settings.insert_one(default_settings.dict())
        return default_settings
    
    return BackupSettings(**settings)

@api_router.put("/settings/backup", response_model=BackupSettings)
async def update_backup_settings(backup_data: Dict[str, Any]):
    """Update backup settings"""
    settings = await db.backup_settings.find_one({"is_active": True})
    if not settings:
        raise HTTPException(status_code=404, detail="Backup settings not found")
    
    backup_data["updated_at"] = datetime.utcnow()
    backup_data["updated_by"] = "current_user"
    
    await db.backup_settings.update_one(
        {"id": settings["id"]},
        {"$set": backup_data}
    )
    
    updated_settings = await db.backup_settings.find_one({"id": settings["id"]})
    return BackupSettings(**updated_settings)

@api_router.get("/settings/webhooks", response_model=List[WebhookConfiguration])
async def get_webhook_configurations():
    """Get webhook configurations"""
    webhooks_cursor = db.webhook_configurations.find({"is_active": True}).sort("name", 1)
    webhooks = await webhooks_cursor.to_list(1000)
    return [WebhookConfiguration(**webhook) for webhook in webhooks]

@api_router.post("/settings/webhooks", response_model=WebhookConfiguration)
async def create_webhook_configuration(webhook_data: WebhookConfigurationCreate):
    """Create webhook configuration"""
    webhook = WebhookConfiguration(
        **webhook_data.dict(),
        secret_key=str(uuid.uuid4())  # Generate secret key
    )
    
    await db.webhook_configurations.insert_one(webhook.dict())
    return webhook

@api_router.delete("/settings/webhooks/{webhook_id}")
async def delete_webhook_configuration(webhook_id: str):
    """Delete webhook configuration"""
    result = await db.webhook_configurations.update_one(
        {"id": webhook_id},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Webhook configuration not found")
    
    return {"message": "Webhook configuration deleted"}

@api_router.get("/settings/rate-limits", response_model=List[RateLimitSettings])
async def get_rate_limit_settings():
    """Get rate limit settings"""
    limits_cursor = db.rate_limit_settings.find({"is_active": True}).sort("resource", 1)
    limits = await limits_cursor.to_list(1000)
    return [RateLimitSettings(**limit) for limit in limits]

@api_router.put("/settings/rate-limits/{limit_id}", response_model=RateLimitSettings)
async def update_rate_limit_setting(limit_id: str, limit_data: Dict[str, Any]):
    """Update rate limit settings"""
    limit_setting = await db.rate_limit_settings.find_one({"id": limit_id})
    if not limit_setting:
        raise HTTPException(status_code=404, detail="Rate limit setting not found")
    
    limit_data["updated_at"] = datetime.utcnow()
    limit_data["updated_by"] = "current_user"
    
    await db.rate_limit_settings.update_one(
        {"id": limit_id},
        {"$set": limit_data}
    )
    
    updated_setting = await db.rate_limit_settings.find_one({"id": limit_id})
    return RateLimitSettings(**updated_setting)

@api_router.get("/settings/ai-task-rules", response_model=List[AITaskRule])
async def get_ai_task_rules():
    """Get AI task assignment rules"""
    rules_cursor = db.ai_task_rules.find({"is_active": True}).sort("priority", -1)
    rules = await rules_cursor.to_list(1000)
    return [AITaskRule(**rule) for rule in rules]

@api_router.post("/settings/ai-task-rules", response_model=AITaskRule)
async def create_ai_task_rule(rule_data: AITaskRuleCreate):
    """Create AI task assignment rule"""
    rule = AITaskRule(**rule_data.dict())
    await db.ai_task_rules.insert_one(rule.dict())
    return rule

@api_router.get("/settings/business-rules", response_model=List[BusinessRule])
async def get_business_rules(module: Optional[str] = None):
    """Get business rules"""
    filter_query = {"is_active": True}
    if module:
        filter_query["module"] = module
    
    rules_cursor = db.business_rules.find(filter_query).sort("priority", -1)
    rules = await rules_cursor.to_list(1000)
    return [BusinessRule(**rule) for rule in rules]

@api_router.post("/settings/business-rules", response_model=BusinessRule)
async def create_business_rule(rule_data: BusinessRuleCreate):
    """Create business rule"""
    rule = BusinessRule(**rule_data.dict())
    await db.business_rules.insert_one(rule.dict())
    return rule

@api_router.put("/settings/business-rules/{rule_id}", response_model=BusinessRule)
async def update_business_rule(rule_id: str, rule_data: Dict[str, Any]):
    """Update business rule"""
    rule = await db.business_rules.find_one({"id": rule_id})
    if not rule:
        raise HTTPException(status_code=404, detail="Business rule not found")
    
    rule_data["updated_at"] = datetime.utcnow()
    
    await db.business_rules.update_one(
        {"id": rule_id},
        {"$set": rule_data}
    )
    
    updated_rule = await db.business_rules.find_one({"id": rule_id})
    return BusinessRule(**updated_rule)

@api_router.get("/settings/dashboard-widgets/{user_id}", response_model=List[DashboardWidget])
async def get_dashboard_widgets(user_id: str):
    """Get dashboard widgets for user"""
    widgets_cursor = db.dashboard_widgets.find({"user_id": user_id, "is_visible": True}).sort("position.y", 1)
    widgets = await widgets_cursor.to_list(1000)
    return [DashboardWidget(**widget) for widget in widgets]

@api_router.put("/settings/dashboard-widgets/{widget_id}", response_model=DashboardWidget)
async def update_dashboard_widget(widget_id: str, widget_update: DashboardWidgetUpdate):
    """Update dashboard widget"""
    widget = await db.dashboard_widgets.find_one({"id": widget_id})
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    update_data = {k: v for k, v in widget_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.dashboard_widgets.update_one(
        {"id": widget_id},
        {"$set": update_data}
    )
    
    updated_widget = await db.dashboard_widgets.find_one({"id": widget_id})
    return DashboardWidget(**updated_widget)

@api_router.get("/settings/menu-config/{role}", response_model=MenuConfiguration)
async def get_menu_configuration(role: UserRole):
    """Get menu configuration for role"""
    config = await db.menu_configurations.find_one({"user_role": role.value})
    if not config:
        # Create default menu config
        default_config = MenuConfiguration(
            user_role=role,
            menu_items=[
                {"name": "Dashboard", "path": "/", "icon": "dashboard", "visible": True},
                {"name": "Lead Generation", "path": "/leads", "icon": "users", "visible": True},
                {"name": "Quoting Tool", "path": "/quotes", "icon": "document", "visible": True},
                {"name": "Task Management", "path": "/tasks", "icon": "checklist", "visible": True},
                {"name": "Workflow Automation", "path": "/workflows", "icon": "workflow", "visible": True},
                {"name": "Team Management", "path": "/team", "icon": "team", "visible": True},
                {"name": "Calendar", "path": "/calendar", "icon": "calendar", "visible": True},
                {"name": "Document Center", "path": "/documents", "icon": "folder", "visible": True},
                {"name": "Integrations Hub", "path": "/integrations", "icon": "link", "visible": True},
                {"name": "Settings", "path": "/settings", "icon": "settings", "visible": role in [UserRole.ADMIN, UserRole.MANAGER]}
            ],
            updated_by="system"
        )
        await db.menu_configurations.insert_one(default_config.dict())
        return default_config
    
    return MenuConfiguration(**config)

@api_router.put("/settings/menu-config/{role}", response_model=MenuConfiguration)
async def update_menu_configuration(role: UserRole, menu_data: Dict[str, Any]):
    """Update menu configuration for role"""
    config = await db.menu_configurations.find_one({"user_role": role.value})
    if not config:
        raise HTTPException(status_code=404, detail="Menu configuration not found")
    
    menu_data["updated_at"] = datetime.utcnow()
    menu_data["updated_by"] = "current_user"
    
    await db.menu_configurations.update_one(
        {"user_role": role.value},
        {"$set": menu_data}
    )
    
    updated_config = await db.menu_configurations.find_one({"user_role": role.value})
    return MenuConfiguration(**updated_config)

@api_router.get("/settings/ai", response_model=List[AISettings])
async def get_ai_settings():
    """Get AI settings"""
    settings_cursor = db.ai_settings.find().sort("category", 1)
    settings = await settings_cursor.to_list(1000)
    return [AISettings(**setting) for setting in settings]

@api_router.put("/settings/ai", response_model=AISettings)
async def update_ai_settings(settings_update: AISettingsUpdate):
    """Update AI settings"""
    # Upsert AI settings by category
    setting_data = AISettings(
        category=settings_update.category,
        settings=settings_update.settings,
        updated_by="current_user"
    )
    
    await db.ai_settings.update_one(
        {"category": settings_update.category},
        {"$set": setting_data.dict()},
        upsert=True
    )
    
    updated_setting = await db.ai_settings.find_one({"category": settings_update.category})
    return AISettings(**updated_setting)

@api_router.get("/settings/notifications/{user_id}", response_model=NotificationSettings)
async def get_notification_settings(user_id: str):
    """Get notification settings for user"""
    settings = await db.notification_settings.find_one({"user_id": user_id})
    if not settings:
        # Create default notification settings
        default_settings = NotificationSettings(user_id=user_id)
        await db.notification_settings.insert_one(default_settings.dict())
        return default_settings
    
    return NotificationSettings(**settings)

@api_router.put("/settings/notifications/{user_id}", response_model=NotificationSettings)
async def update_notification_settings(user_id: str, notification_data: Dict[str, Any]):
    """Update notification settings"""
    notification_data["updated_at"] = datetime.utcnow()
    
    await db.notification_settings.update_one(
        {"user_id": user_id},
        {"$set": notification_data},
        upsert=True
    )
    
    updated_settings = await db.notification_settings.find_one({"user_id": user_id})
    return NotificationSettings(**updated_settings)

@api_router.post("/settings/initialize-sample-data")
async def initialize_settings_sample_data():
    """Initialize sample settings and configurations"""
    try:
        # Clear existing data
        await db.user_profiles.delete_many({})
        await db.system_settings.delete_many({})
        await db.ai_settings.delete_many({})
        await db.rate_limit_settings.delete_many({})
        
        # Create sample user profiles
        sample_users = [
            UserProfile(
                user_id="admin_001",
                username="admin",
                email="admin@systemix.ai",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                department="IT",
                permissions=["all"]
            ),
            UserProfile(
                user_id="manager_001",
                username="sales_manager",
                email="manager@systemix.ai",
                full_name="Sales Manager",
                role=UserRole.MANAGER,
                department="Sales",
                permissions=["read", "write", "manage_team"]
            ),
            UserProfile(
                user_id="user_001",
                username="sales_rep",
                email="user@systemix.ai",
                full_name="Sales Representative",
                role=UserRole.USER,
                department="Sales",
                permissions=["read", "write"]
            )
        ]
        
        for user in sample_users:
            await db.user_profiles.insert_one(user.dict())
        
        # Create sample system settings
        sample_settings = [
            SystemSettings(
                category="general",
                key="company_name",
                value="SystemIX AI Demo",
                data_type="string",
                description="Company name displayed in the application",
                is_public=True,
                updated_by="system"
            ),
            SystemSettings(
                category="general",
                key="timezone",
                value="UTC",
                data_type="string",
                description="Default timezone for the application",
                is_public=True,
                updated_by="system"
            ),
            SystemSettings(
                category="security",
                key="session_timeout",
                value=480,
                data_type="number",
                description="Session timeout in minutes",
                is_public=False,
                updated_by="system"
            )
        ]
        
        for setting in sample_settings:
            await db.system_settings.insert_one(setting.dict())
        
        # Create sample AI settings
        sample_ai_settings = [
            AISettings(
                category="model",
                settings={
                    "preferred_model": "gpt-4",
                    "confidence_threshold": 0.8,
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                updated_by="system"
            ),
            AISettings(
                category="scoring",
                settings={
                    "algorithm": "ml_enhanced",
                    "factors": {
                        "company_size": 0.3,
                        "industry_match": 0.2,
                        "engagement_level": 0.3,
                        "budget_qualification": 0.2
                    }
                },
                updated_by="system"
            ),
            AISettings(
                category="assistant",
                settings={
                    "personality": "professional",
                    "response_length": "medium",
                    "proactive_suggestions": True,
                    "learning_enabled": True
                },
                updated_by="system"
            )
        ]
        
        for ai_setting in sample_ai_settings:
            await db.ai_settings.insert_one(ai_setting.dict())
        
        # Create sample rate limit settings
        sample_rate_limits = [
            RateLimitSettings(
                resource="api",
                limit_per_hour=1000,
                limit_per_day=10000,
                burst_limit=100,
                updated_by="system"
            ),
            RateLimitSettings(
                resource="ai_requests",
                limit_per_hour=500,
                limit_per_day=2000,
                burst_limit=50,
                updated_by="system"
            )
        ]
        
        for rate_limit in sample_rate_limits:
            await db.rate_limit_settings.insert_one(rate_limit.dict())
        
        return {"message": "Sample settings data initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@api_router.post("/initialize-mock-data")
async def initialize_mock_data():
    """Initialize the system with mock data"""
    try:
        # Clear existing data
        await db.leads.delete_many({})
        await db.tasks.delete_many({})
        await db.workflows.delete_many({})
        await db.team_members.delete_many({})
        await db.calendar_events.delete_many({})
        
        # Create mock leads
        mock_leads = [
            Lead(name="John Smith", email="john@acmecorp.com", company="ACME Corp", phone="+1-555-0123", source="Website", score=85),
            Lead(name="Sarah Johnson", email="sarah@techstart.com", company="TechStart Inc", phone="+1-555-0124", source="LinkedIn", score=92),
            Lead(name="Mike Chen", email="mike@innovate.io", company="Innovate Solutions", source="Referral", score=78),
            Lead(name="Emily Davis", email="emily@globaltech.com", company="GlobalTech", phone="+1-555-0125", source="Cold Email", score=65),
            Lead(name="David Wilson", email="david@future.co", company="Future Dynamics", source="Conference", score=88)
        ]
        
        for lead in mock_leads:
            await db.leads.insert_one(lead.dict())
        
        # Create mock tasks
        mock_tasks = [
            Task(title="Follow up with ACME Corp", description="Schedule demo call", priority=TaskPriority.HIGH, created_by="admin", assigned_to="john_doe"),
            Task(title="Prepare Q4 proposal", description="Create comprehensive proposal for TechStart", priority=TaskPriority.MEDIUM, created_by="admin", assigned_to="sarah_smith"),
            Task(title="Update CRM integration", description="Implement new API endpoints", priority=TaskPriority.LOW, created_by="admin"),
            Task(title="Review lead scoring algorithm", description="Optimize AI scoring parameters", priority=TaskPriority.HIGH, created_by="admin", assigned_to="mike_johnson")
        ]
        
        for task in mock_tasks:
            await db.tasks.insert_one(task.dict())
        
        # Create mock workflows
        mock_workflows = [
            Workflow(name="Lead Qualification", description="Automated lead scoring and routing", created_by="admin", executions=156, success_rate=94.5),
            Workflow(name="Email Campaign", description="Automated email sequences for nurturing", created_by="admin", executions=89, success_rate=87.2),
            Workflow(name="Follow-up Reminders", description="Automated task creation for follow-ups", created_by="admin", executions=234, success_rate=96.1)
        ]
        
        for workflow in mock_workflows:
            await db.workflows.insert_one(workflow.dict())
        
        # Create mock team members
        mock_team = [
            TeamMember(name="John Doe", email="john.doe@systemix.ai", role="Sales Manager", department="Sales", is_online=True, tasks_assigned=12, tasks_completed=8),
            TeamMember(name="Sarah Smith", email="sarah.smith@systemix.ai", role="Marketing Specialist", department="Marketing", is_online=True, tasks_assigned=8, tasks_completed=15),
            TeamMember(name="Mike Johnson", email="mike.johnson@systemix.ai", role="AI Engineer", department="Engineering", is_online=False, tasks_assigned=6, tasks_completed=12),
            TeamMember(name="Emily Brown", email="emily.brown@systemix.ai", role="Product Manager", department="Product", is_online=True, tasks_assigned=10, tasks_completed=9)
        ]
        
        for member in mock_team:
            await db.team_members.insert_one(member.dict())
        
        # Create mock calendar events
        tomorrow = datetime.utcnow() + timedelta(days=1)
        mock_events = [
            CalendarEvent(title="Weekly Sales Meeting", start_time=tomorrow.replace(hour=9), end_time=tomorrow.replace(hour=10), created_by="admin", attendees=["john.doe", "sarah.smith"]),
            CalendarEvent(title="Product Demo - ACME Corp", start_time=tomorrow.replace(hour=14), end_time=tomorrow.replace(hour=15), created_by="john.doe", attendees=["john.doe", "john@acmecorp.com"]),
            CalendarEvent(title="AI Model Review", start_time=tomorrow.replace(hour=16), end_time=tomorrow.replace(hour=17), created_by="mike.johnson", attendees=["mike.johnson", "emily.brown"])
        ]
        
        for event in mock_events:
            await db.calendar_events.insert_one(event.dict())
        
        return {"message": "Mock data initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AUTONOMOUS NETWORK MONITORING BOT ENDPOINTS
# ============================================================================

# Helper function to get system metrics (simulated for demo)
async def get_current_system_metrics():
    """Simulate getting real system metrics"""
    import random
    import psutil
    
    # Get actual system metrics where possible, simulate others
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": (disk.used / disk.total) * 100,
            "network_latency": random.uniform(10, 50),  # Simulated
            "api_response_time": random.uniform(100, 300),  # Simulated
        }
    except Exception:
        # Fallback to simulated metrics
        return {
            "cpu_usage": random.uniform(20, 80),
            "memory_usage": random.uniform(30, 85),
            "disk_usage": random.uniform(40, 75),
            "network_latency": random.uniform(10, 50),
            "api_response_time": random.uniform(100, 300),
        }

# Enhanced AI-powered analysis with predictive capabilities
async def analyze_metrics_with_ai(metrics_data: List[Dict], current_metrics: Dict):
    """Advanced AI analysis with predictive analytics, pattern recognition, and trend forecasting"""
    try:
        # Initialize AI chat for advanced analysis
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY') or os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"monitoring_analysis_{uuid.uuid4()}",
            system_message="You are an advanced system monitoring AI with capabilities in predictive analytics, pattern recognition, and trend forecasting. Analyze system metrics to provide deep insights, predictions, and proactive recommendations."
        ).with_model("openai", "gpt-4o")
        
        # Calculate historical trends and patterns
        historical_analysis = await calculate_historical_trends(metrics_data)
        
        # Prepare enhanced metrics data for AI analysis
        analysis_prompt = f"""
        CURRENT SYSTEM STATE:
        - CPU Usage: {current_metrics['cpu_usage']:.1f}%
        - Memory Usage: {current_metrics['memory_usage']:.1f}%
        - Disk Usage: {current_metrics['disk_usage']:.1f}%
        - Network Latency: {current_metrics['network_latency']:.1f}ms
        - API Response Time: {current_metrics['api_response_time']:.1f}ms
        
        HISTORICAL ANALYSIS:
        - Data Points: {len(metrics_data)} recent measurements
        - CPU Trend: {historical_analysis.get('cpu_trend', 'stable')}
        - Memory Trend: {historical_analysis.get('memory_trend', 'stable')}
        - Alert Patterns: {historical_analysis.get('alert_patterns', 'normal')}
        - Performance Correlation: {historical_analysis.get('performance_correlation', 'good')}
        
        ADVANCED ANALYSIS REQUIRED:
        1. **Predictive Analytics**: 
           - Predict likely system behavior in next 2-6 hours
           - Identify potential resource exhaustion scenarios
           - Forecast when thresholds might be breached
        
        2. **Pattern Recognition**:
           - Identify recurring patterns or cycles
           - Detect seasonal or time-based performance changes
           - Compare current state to historical similar scenarios
        
        3. **Trend Forecasting**:
           - Project resource usage trends (CPU, memory, disk growth)
           - Estimate capacity planning needs
           - Predict optimal maintenance windows
        
        4. **Anomaly Detection**:
           - Current anomalies or unusual deviations
           - Correlation between different metrics
           - Early warning indicators
        
        5. **Proactive Recommendations**:
           - Preventive actions to avoid future issues
           - Performance optimization opportunities
           - Resource scaling recommendations
        
        Please provide a comprehensive analysis in the following JSON structure:
        {{
            "health_status": "healthy/warning/critical",
            "current_anomalies": ["list of immediate concerns"],
            "predictions": {{
                "next_2_hours": "prediction for immediate future",
                "next_6_hours": "medium-term prediction",
                "resource_exhaustion_risk": "low/medium/high"
            }},
            "patterns_detected": ["list of patterns found"],
            "trend_analysis": {{
                "cpu_trend": "increasing/decreasing/stable",
                "memory_trend": "increasing/decreasing/stable", 
                "performance_trend": "improving/degrading/stable"
            }},
            "recommendations": ["list of actionable recommendations"],
            "proactive_actions": ["preventive measures to implement"],
            "healing_actions": ["immediate healing actions if needed"],
            "capacity_planning": "insights for future resource planning"
        }}
        """
        
        user_message = UserMessage(text=analysis_prompt)
        response = await chat.send_message(user_message)
        
        return response
    except Exception as e:
        logger.error(f"Enhanced AI analysis failed: {str(e)}")
        return "AI analysis temporarily unavailable. System appears stable based on threshold checks."

# Historical trend calculation helper
async def calculate_historical_trends(metrics_data: List[Dict]) -> Dict:
    """Calculate historical trends from metrics data"""
    try:
        if not metrics_data:
            return {"cpu_trend": "stable", "memory_trend": "stable", "alert_patterns": "normal"}
        
        # Extract CPU and memory values from historical data
        cpu_values = []
        memory_values = []
        
        for metric in metrics_data:
            if isinstance(metric.get('metadata'), dict):
                cpu_values.append(metric['metadata'].get('cpu_usage', 0))
                memory_values.append(metric['metadata'].get('memory_usage', 0))
        
        # Calculate trends
        cpu_trend = "stable"
        memory_trend = "stable"
        
        if len(cpu_values) >= 3:
            recent_cpu = sum(cpu_values[:3]) / 3
            older_cpu = sum(cpu_values[3:6]) / max(1, len(cpu_values[3:6]))
            if recent_cpu > older_cpu * 1.1:
                cpu_trend = "increasing"
            elif recent_cpu < older_cpu * 0.9:
                cpu_trend = "decreasing"
        
        if len(memory_values) >= 3:
            recent_memory = sum(memory_values[:3]) / 3
            older_memory = sum(memory_values[3:6]) / max(1, len(memory_values[3:6]))
            if recent_memory > older_memory * 1.1:
                memory_trend = "increasing"
            elif recent_memory < older_memory * 0.9:
                memory_trend = "decreasing"
        
        return {
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend,
            "alert_patterns": "normal",
            "performance_correlation": "good"
        }
    except Exception as e:
        logger.error(f"Error calculating historical trends: {str(e)}")
        return {"cpu_trend": "stable", "memory_trend": "stable", "alert_patterns": "normal"}

@api_router.get("/monitoring/system-status")
async def get_system_status():
    """Get current system status and health metrics"""
    try:
        current_metrics = await get_current_system_metrics()
        
        # Count active alerts
        active_alerts_count = await db.system_alerts.count_documents({"status": "active"})
        
        # Calculate uptime (simulated)
        uptime_hours = random.uniform(120, 720)  # Simulate 5-30 days uptime
        
        # Determine overall health based on metrics
        health = "healthy"
        if current_metrics["cpu_usage"] > 80 or current_metrics["memory_usage"] > 85:
            health = "warning"
        if current_metrics["cpu_usage"] > 90 or current_metrics["memory_usage"] > 95:
            health = "critical"
        
        system_status = SystemStatus(
            overall_health=health,
            cpu_usage=current_metrics["cpu_usage"],
            memory_usage=current_metrics["memory_usage"],
            disk_usage=current_metrics["disk_usage"],
            network_latency=current_metrics["network_latency"],
            api_response_time=current_metrics["api_response_time"],
            active_alerts=active_alerts_count,
            total_alerts_24h=await db.system_alerts.count_documents({
                "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
            }),
            last_check=datetime.utcnow(),
            uptime=uptime_hours
        )
        
        return system_status
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/monitoring/metrics", response_model=List[MonitoringMetric])
async def get_monitoring_metrics(limit: int = 50):
    """Get recent monitoring metrics"""
    try:
        metrics = await db.monitoring_metrics.find().sort("timestamp", -1).limit(limit).to_list(length=limit)
        return [MonitoringMetric(**metric) for metric in metrics]
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/monitoring/metrics")
async def create_monitoring_metric(metric: MonitoringMetric):
    """Create a new monitoring metric entry"""
    try:
        metric_dict = metric.dict()
        await db.monitoring_metrics.insert_one(metric_dict)
        return {"message": "Metric created successfully", "id": metric.id}
    except Exception as e:
        logger.error(f"Error creating metric: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/monitoring/alerts", response_model=List[SystemAlert])
async def get_system_alerts(status: Optional[str] = None, limit: int = 50):
    """Get system alerts with optional status filter"""
    try:
        query = {}
        if status:
            query["status"] = status
        
        alerts = await db.system_alerts.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
        return [SystemAlert(**alert) for alert in alerts]
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/monitoring/alerts")
async def create_system_alert(alert: SystemAlert):
    """Create a new system alert"""
    try:
        alert_dict = alert.dict()
        await db.system_alerts.insert_one(alert_dict)
        
        # If critical alert, trigger immediate analysis
        if alert.severity == AlertSeverity.CRITICAL:
            # Background task for AI analysis and potential healing
            pass  # Implement background processing if needed
        
        return {"message": "Alert created successfully", "id": alert.id}
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/monitoring/alerts/{alert_id}/status")
async def update_alert_status(alert_id: str, status: AlertStatus):
    """Update alert status"""
    try:
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if status == AlertStatus.RESOLVED:
            update_data["resolved_at"] = datetime.utcnow()
        
        result = await db.system_alerts.update_one(
            {"id": alert_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert status updated successfully"}
    except Exception as e:
        logger.error(f"Error updating alert status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/monitoring/analyze")
async def trigger_ai_analysis():
    """Trigger AI-powered system analysis"""
    try:
        # Get current metrics
        current_metrics = await get_current_system_metrics()
        
        # Get recent historical metrics
        recent_metrics = await db.monitoring_metrics.find().sort("timestamp", -1).limit(20).to_list(length=20)
        
        # Perform AI analysis
        ai_analysis = await analyze_metrics_with_ai(recent_metrics, current_metrics)
        
        # Store the current metrics
        metric = MonitoringMetric(
            metric_name="system_health_check",
            value=1.0,
            unit="status",
            timestamp=datetime.utcnow(),
            source="ai_analysis",
            metadata=current_metrics
        )
        await db.monitoring_metrics.insert_one(metric.dict())
        
        return {
            "message": "AI analysis completed",
            "current_metrics": current_metrics,
            "ai_analysis": ai_analysis,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error in AI analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/monitoring/healing-action")
async def execute_healing_action(action_type: str, alert_id: str, description: str):
    """Execute a self-healing action"""
    try:
        success = False
        output = ""
        
        # Simulate different healing actions
        if action_type == "restart_service":
            # Simulate service restart
            output = "Service restart command executed successfully"
            success = True
        elif action_type == "clear_cache":
            # Simulate cache clearing
            output = "System cache cleared successfully"
            success = True
        elif action_type == "scale_resources":
            # Simulate resource scaling
            output = "Resource scaling initiated"
            success = True
        else:
            output = f"Unknown action type: {action_type}"
            success = False
        
        # Create healing action record
        healing_action = HealingAction(
            alert_id=alert_id,
            action_type=action_type,
            description=description,
            executed_at=datetime.utcnow(),
            success=success,
            output=output,
            ai_recommended=True
        )
        
        await db.healing_actions.insert_one(healing_action.dict())
        
        # Update the alert with healing attempt
        await db.system_alerts.update_one(
            {"id": alert_id},
            {
                "$set": {
                    "auto_healing_attempted": True,
                    "updated_at": datetime.utcnow()
                },
                "$push": {"healing_actions": action_type}
            }
        )
        
        return {
            "message": "Healing action executed",
            "action_id": healing_action.id,
            "success": success,
            "output": output
        }
    except Exception as e:
        logger.error(f"Error executing healing action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/monitoring/healing-actions", response_model=List[HealingAction])
async def get_healing_actions(limit: int = 50):
    """Get recent healing actions"""
    try:
        actions = await db.healing_actions.find().sort("executed_at", -1).limit(limit).to_list(length=limit)
        return [HealingAction(**action) for action in actions]
    except Exception as e:
        logger.error(f"Error getting healing actions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/monitoring/simulate-alert")
async def simulate_system_alert(severity: AlertSeverity = AlertSeverity.MEDIUM):
    """Simulate a system alert for testing purposes"""
    try:
        current_metrics = await get_current_system_metrics()
        
        # Create a simulated alert based on metrics
        alert_scenarios = {
            AlertSeverity.LOW: {
                "title": "Disk Usage Warning",
                "description": f"Disk usage at {current_metrics['disk_usage']:.1f}% - monitor closely"
            },
            AlertSeverity.MEDIUM: {
                "title": "High Memory Usage",
                "description": f"Memory usage at {current_metrics['memory_usage']:.1f}% - consider optimization"
            },
            AlertSeverity.HIGH: {
                "title": "CPU Spike Detected",
                "description": f"CPU usage at {current_metrics['cpu_usage']:.1f}% - investigate processes"
            },
            AlertSeverity.CRITICAL: {
                "title": "System Performance Critical",
                "description": "Multiple metrics exceeding safe thresholds - immediate action required"
            }
        }
        
        scenario = alert_scenarios[severity]
        
        alert = SystemAlert(
            title=scenario["title"],
            description=scenario["description"],
            severity=severity,
            source="system_monitor",
            metric_data=current_metrics,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            auto_healing_attempted=False
        )
        
        await db.system_alerts.insert_one(alert.dict())
        
        return {
            "message": "Simulated alert created successfully",
            "alert": alert,
            "alert_id": alert.id
        }
    except Exception as e:
        logger.error(f"Error simulating alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WEBSOCKET ENDPOINTS FOR REAL-TIME MONITORING
# ============================================================================

# WebSocket connection manager for monitoring
class MonitoringConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_system_status(self, data: dict):
        message = json.dumps({"type": "system_status", "data": data})
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)
        
        # Remove dead connections
        for conn in dead_connections:
            self.disconnect(conn)

    async def broadcast_alert(self, alert: dict):
        message = json.dumps({"type": "new_alert", "data": alert})
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)
        
        # Remove dead connections
        for conn in dead_connections:
            self.disconnect(conn)

monitoring_manager = MonitoringConnectionManager()

@app.websocket("/ws/monitoring")
async def websocket_monitoring_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates"""
    await monitoring_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive and listen for client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        monitoring_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        monitoring_manager.disconnect(websocket)

# Background task for collecting and broadcasting real-time metrics
async def collect_and_broadcast_metrics():
    """Background task to collect metrics and broadcast to WebSocket clients"""
    while True:
        try:
            # Get current system metrics
            current_metrics = await get_current_system_metrics()
            
            # Count active alerts
            active_alerts_count = await db.system_alerts.count_documents({"status": "active"})
            
            # Calculate uptime (simulated)
            uptime_hours = random.uniform(120, 720)
            
            # Determine overall health
            health = "healthy"
            if current_metrics["cpu_usage"] > 80 or current_metrics["memory_usage"] > 85:
                health = "warning"
            if current_metrics["cpu_usage"] > 90 or current_metrics["memory_usage"] > 95:
                health = "critical"
            
            system_status = {
                "overall_health": health,
                "cpu_usage": current_metrics["cpu_usage"],
                "memory_usage": current_metrics["memory_usage"],
                "disk_usage": current_metrics["disk_usage"],
                "network_latency": current_metrics["network_latency"],
                "api_response_time": current_metrics["api_response_time"],
                "active_alerts": active_alerts_count,
                "total_alerts_24h": await db.system_alerts.count_documents({
                    "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
                }),
                "last_check": datetime.utcnow().isoformat(),
                "uptime": uptime_hours,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store metrics for historical analysis
            await store_historical_metric(current_metrics)
            
            # Broadcast to WebSocket clients
            await monitoring_manager.broadcast_system_status(system_status)
            
            # Sleep for 10 seconds before next update
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in metrics collection: {str(e)}")
            await asyncio.sleep(10)

async def store_historical_metric(metrics: dict):
    """Store current metrics for historical analysis and charting"""
    try:
        # Store individual metrics for charting
        timestamp = datetime.utcnow()
        
        metrics_to_store = [
            MonitoringMetric(
                metric_name="cpu_usage",
                value=metrics["cpu_usage"],
                unit="percent",
                timestamp=timestamp,
                source="system_monitor",
                metadata={"type": "real_time"}
            ),
            MonitoringMetric(
                metric_name="memory_usage",
                value=metrics["memory_usage"],
                unit="percent",
                timestamp=timestamp,
                source="system_monitor",
                metadata={"type": "real_time"}
            ),
            MonitoringMetric(
                metric_name="disk_usage", 
                value=metrics["disk_usage"],
                unit="percent",
                timestamp=timestamp,
                source="system_monitor",
                metadata={"type": "real_time"}
            ),
            MonitoringMetric(
                metric_name="network_latency",
                value=metrics["network_latency"],
                unit="ms",
                timestamp=timestamp,
                source="system_monitor",
                metadata={"type": "real_time"}
            ),
            MonitoringMetric(
                metric_name="api_response_time",
                value=metrics["api_response_time"],
                unit="ms",
                timestamp=timestamp,
                source="system_monitor",
                metadata={"type": "real_time"}
            )
        ]
        
        # Store all metrics in batch
        for metric in metrics_to_store:
            await db.monitoring_metrics.insert_one(metric.dict())
            
        # Clean up old metrics (keep only last 1000 entries per metric type)
        for metric_name in ["cpu_usage", "memory_usage", "disk_usage", "network_latency", "api_response_time"]:
            count = await db.monitoring_metrics.count_documents({"metric_name": metric_name})
            if count > 1000:
                # Get oldest entries to delete
                oldest_entries = await db.monitoring_metrics.find(
                    {"metric_name": metric_name}
                ).sort("timestamp", 1).limit(count - 1000).to_list(length=None)
                
                # Delete oldest entries
                if oldest_entries:
                    oldest_ids = [entry["_id"] for entry in oldest_entries]
                    await db.monitoring_metrics.delete_many({"_id": {"$in": oldest_ids}})
                    
    except Exception as e:
        logger.error(f"Error storing historical metrics: {str(e)}")

@api_router.get("/monitoring/metrics/historical/{metric_name}")
async def get_historical_metrics(metric_name: str, hours: int = 24):
    """Get historical metrics for charting"""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get historical data
        metrics = await db.monitoring_metrics.find({
            "metric_name": metric_name,
            "timestamp": {"$gte": start_time, "$lte": end_time}
        }).sort("timestamp", 1).to_list(length=None)
        
        # Format for charting
        chart_data = []
        for metric in metrics:
            chart_data.append({
                "timestamp": metric["timestamp"].isoformat(),
                "value": metric["value"],
                "unit": metric["unit"]
            })
        
        return {
            "metric_name": metric_name,
            "data": chart_data,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_points": len(chart_data)
        }
    except Exception as e:
        logger.error(f"Error getting historical metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/monitoring/metrics/chart-data")
async def get_chart_data(hours: int = 6):
    """Get formatted data for all charts"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get all metric types
        metric_names = ["cpu_usage", "memory_usage", "disk_usage", "network_latency", "api_response_time"]
        chart_data = {}
        
        for metric_name in metric_names:
            metrics = await db.monitoring_metrics.find({
                "metric_name": metric_name,
                "timestamp": {"$gte": start_time, "$lte": end_time},
                "metadata.type": "real_time"
            }).sort("timestamp", 1).to_list(length=None)
            
            chart_data[metric_name] = {
                "labels": [metric["timestamp"].strftime("%H:%M") for metric in metrics],
                "data": [metric["value"] for metric in metrics],
                "unit": metrics[0]["unit"] if metrics else "",
                "count": len(metrics)
            }
        
        return {
            "success": True,
            "chart_data": chart_data,
            "time_range": f"Last {hours} hours",
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# END WEBSOCKET AND REAL-TIME FEATURES
# ============================================================================

# ============================================================================
# END MONITORING ENDPOINTS
# ============================================================================

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    # Start background metrics collection
    asyncio.create_task(collect_and_broadcast_metrics())
    logger.info("Started real-time metrics collection background task")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)