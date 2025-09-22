from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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
from pathlib import Path
import base64
import io

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)