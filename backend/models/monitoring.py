from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"

class MonitoringMetric(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    source: str  # e.g., "cpu", "memory", "network", "api"
    metadata: Optional[Dict[str, Any]] = {}

class SystemAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    source: str
    metric_data: Optional[Dict[str, Any]] = {}
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    auto_healing_attempted: bool = False
    healing_actions: List[str] = []
    ai_analysis: Optional[str] = None

class SystemStatus(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    overall_health: str  # "healthy", "warning", "critical"
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    api_response_time: float
    active_alerts: int
    total_alerts_24h: int
    last_check: datetime
    uptime: float  # in hours

class HealingAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str
    action_type: str  # "restart_service", "clear_cache", "scale_resources", etc.
    description: str
    executed_at: datetime
    success: bool
    output: Optional[str] = None
    ai_recommended: bool = False

class MonitoringConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric_thresholds: Dict[str, Dict[str, float]]  # metric_name -> {warning, critical}
    check_intervals: Dict[str, int]  # metric_name -> interval in seconds
    auto_healing_enabled: bool = True
    alert_escalation_time: int = 300  # seconds before escalation
    ai_analysis_enabled: bool = True
    notification_channels: List[str] = ["dashboard", "email"]

class AnomalyDetection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str
    detected_at: datetime
    anomaly_type: str  # "spike", "drop", "trend_change", "pattern_break"
    confidence_score: float  # 0.0 to 1.0
    baseline_value: float
    anomalous_value: float
    ai_analysis: str
    recommended_actions: List[str] = []