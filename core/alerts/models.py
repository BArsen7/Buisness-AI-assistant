"""
core/alerts/models.py
Модели для системы алертов (заглушки для совместимости).
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"

@dataclass
class AlertEvent:
    """Событие алерта."""
    name: str
    severity: AlertSeverity
    message: str
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TriageDecision:
    """Решение триажа."""
    route_to: str
    priority: int
    notes: str = ""
