"""
models.py
Определение типов данных, ENUM ролей и структур для проекта Open Executive.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


class AgentRole(Enum):
    """
    Перечисление ролей агентов (Совет Директоров).
    Каждая роль имеет уникальный системный контекст.
    """
    ORCHESTRATOR = "ORCHESTRATOR"  # Главный координатор
    CSO = "CSO"                    # Chief Strategy Officer
    CFO = "CFO"                    # Chief Financial Officer
    CHRO = "CHRO"                  # Chief Human Resources Officer
    GC = "GC"                      # General Counsel (Юрист)
    COO = "COO"                    # Chief Operating Officer
    CMO = "CMO"                    # Chief Marketing Officer
    CPO = "CPO"                    # Chief Product Officer
    BOARD = "BOARD"                # Представитель инвесторов


@dataclass
class Project:
    """Модель проекта (Рабочего пространства)."""
    id: int
    name: str
    chroma_collection_name: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Chat:
    """Модель чата внутри проекта."""
    id: int
    project_id: int
    name: str
    agent_role: AgentRole
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Message:
    """Модель сообщения в чате."""
    id: int
    chat_id: int
    role: str  # 'user' или 'assistant' (или системная роль)
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EpisodicMemory:
    """Модель эпизодической памяти проекта (краткие саммари событий)."""
    id: int
    project_id: int
    summary: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PromptRequest:
    """Запрос к промпт-инженеру."""
    user_idea: str
    target_agent_role: AgentRole
    chat_context: List[dict] = field(default_factory=list)


@dataclass
class SlideData:
    """Структура данных для экспорта в PowerPoint."""
    title: str
    bullets: List[str]
