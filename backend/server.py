from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
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

# AI Integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

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

# Mock data initialization
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