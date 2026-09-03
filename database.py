"""
database.py
Модуль управления базой данных SQLite для проекта Open Executive.
Реализует класс WorkspaceManager для работы с проектами, чатами и сообщениями.
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Any
from pathlib import Path

from models import Project, Chat, Message, EpisodicMemory, AgentRole


class WorkspaceManager:
    """
    Менеджер рабочего пространства (БД).
    Управляет проектами, чатами, сообщениями и эпизодической памятью в SQLite.
    
    Атрибуты:
        db_path (Path): Путь к файлу базы данных SQLite.
    """

    def __init__(self, db_path: str = "open_executive.db"):
        """
        Инициализация менеджера БД.
        
        Args:
            db_path: Путь к файлу SQLite базы данных.
        """
        self.db_path = Path(db_path)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Создает и возвращает подключение к БД с поддержкой ROW factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Инициализация схемы БД (создание таблиц если не существуют)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица проектов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    chroma_collection_name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица чатов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    agent_role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            # Таблица сообщений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
                )
            """)
            
            # Таблица эпизодической памяти
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()

    # --- Методы для Проектов ---

    def create_project(self, name: str) -> Project:
        """
        Создает новый проект.
        
        Args:
            name: Название проекта.
            
        Returns:
            Project: Объект созданного проекта.
        """
        chroma_name = f"collection_{name.lower().replace(' ', '_')}_{datetime.now().timestamp()}"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name, chroma_collection_name) VALUES (?, ?)",
                (name, chroma_name)
            )
            conn.commit()
            project_id = cursor.lastrowid
            
            return Project(
                id=project_id,
                name=name,
                chroma_collection_name=chroma_name
            )

    def get_project(self, project_id: int) -> Optional[Project]:
        """Получает проект по ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            
            if row:
                return Project(
                    id=row['id'],
                    name=row['name'],
                    chroma_collection_name=row['chroma_collection_name'],
                    created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
                )
        return None

    def list_projects(self) -> List[Project]:
        """Возвращает список всех проектов."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            return [
                Project(
                    id=row['id'],
                    name=row['name'],
                    chroma_collection_name=row['chroma_collection_name'],
                    created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
                )
                for row in rows
            ]

    # --- Методы для Чатов ---

    def create_chat(self, project_id: int, name: str, agent_role: AgentRole) -> Chat:
        """
        Создает новый чат в проекте с указанной ролью агента.
        
        Args:
            project_id: ID проекта.
            name: Название чата.
            agent_role: Роль агента (ENUM).
            
        Returns:
            Chat: Объект созданного чата.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chats (project_id, name, agent_role) VALUES (?, ?, ?)",
                (project_id, name, agent_role.value)
            )
            conn.commit()
            chat_id = cursor.lastrowid
            
            return Chat(
                id=chat_id,
                project_id=project_id,
                name=name,
                agent_role=agent_role
            )

    def get_chat(self, chat_id: int) -> Optional[Chat]:
        """Получает чат по ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
            row = cursor.fetchone()
            
            if row:
                return Chat(
                    id=row['id'],
                    project_id=row['project_id'],
                    name=row['name'],
                    agent_role=AgentRole(row['agent_role']),
                    created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
                )
        return None

    def list_chats(self, project_id: int) -> List[Chat]:
        """Возвращает список всех чатов в проекте."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chats WHERE project_id = ? ORDER BY created_at ASC", (project_id,))
            rows = cursor.fetchall()
            
            return [
                Chat(
                    id=row['id'],
                    project_id=row['project_id'],
                    name=row['name'],
                    agent_role=AgentRole(row['agent_role']),
                    created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
                )
                for row in rows
            ]

    # --- Методы для Сообщений ---

    def add_message(self, chat_id: int, role: str, content: str) -> Message:
        """
        Добавляет сообщение в чат.
        
        Args:
            chat_id: ID чата.
            role: Роль отправителя ('user', 'assistant', 'system').
            content: Текст сообщения.
            
        Returns:
            Message: Объект созданного сообщения.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content)
            )
            conn.commit()
            msg_id = cursor.lastrowid
            
            return Message(
                id=msg_id,
                chat_id=chat_id,
                role=role,
                content=content
            )

    def get_messages(self, chat_id: int, limit: Optional[int] = None) -> List[Message]:
        """
        Получает историю сообщений чата.
        
        Args:
            chat_id: ID чата.
            limit: Ограничение количества сообщений (None = все).
            
        Returns:
            List[Message]: Список сообщений.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM messages WHERE chat_id = ? ORDER BY timestamp ASC"
            if limit:
                query += f" LIMIT {limit}"
                
            cursor.execute(query, (chat_id,))
            rows = cursor.fetchall()
            
            return [
                Message(
                    id=row['id'],
                    chat_id=row['chat_id'],
                    role=row['role'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp']) if isinstance(row['timestamp'], str) else row['timestamp']
                )
                for row in rows
            ]

    # --- Методы для Эпизодической Памяти ---

    def add_episodic_memory(self, project_id: int, summary: str) -> EpisodicMemory:
        """
        Добавляет запись в эпизодическую память проекта.
        
        Args:
            project_id: ID проекта.
            summary: Краткое содержание эпизода.
            
        Returns:
            EpisodicMemory: Объект записи памяти.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO episodic_memory (project_id, summary) VALUES (?, ?)",
                (project_id, summary)
            )
            conn.commit()
            mem_id = cursor.lastrowid
            
            return EpisodicMemory(
                id=mem_id,
                project_id=project_id,
                summary=summary
            )

    def get_episodic_memories(self, project_id: int, limit: int = 10) -> List[EpisodicMemory]:
        """Получает последние записи эпизодической памяти проекта."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM episodic_memory WHERE project_id = ? ORDER BY timestamp DESC LIMIT ?",
                (project_id, limit)
            )
            rows = cursor.fetchall()
            
            return [
                EpisodicMemory(
                    id=row['id'],
                    project_id=row['project_id'],
                    summary=row['summary'],
                    timestamp=datetime.fromisoformat(row['timestamp']) if isinstance(row['timestamp'], str) else row['timestamp']
                )
                for row in rows
            ]
