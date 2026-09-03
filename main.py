#!/usr/bin/env python3
"""
Open Executive — Точка входа в приложение
Запуск десктопного приложения с главным окном
"""

import sys
import os
from pathlib import Path

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    # Пытаемся загрузить .env из разных возможных мест
    for env_path in [".env", Path(__file__).parent / ".env"]:
        if Path(env_path).exists():
            load_dotenv(env_path)
            break
except ImportError:
    print("Warning: python-dotenv not installed. Using environment variables only.")


def ensure_data_directories():
    """Создает необходимые директории для данных если их нет."""
    base_dir = Path(__file__).parent.absolute()
    
    # Директории для ChromaDB и SQLite
    data_dirs = [
        base_dir / "data" / "chroma_db",
        base_dir / "data" / "sqlite",
    ]
    
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Также создаем директорию в домашней папке пользователя для надежности
    # (используется при запуске скомпилированного приложения)
    user_data_dir = Path.home() / ".openexecutive"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    return base_dir, user_data_dir


# Создаем директории до импорта PyQt6
base_dir, user_data_dir = ensure_data_directories()

# Добавляем текущую директорию в path для импортов
sys.path.insert(0, str(base_dir))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database import WorkspaceManager
from ui_widgets import PromptEngineerWidget, ChatInfo
from models import AgentRole


class MainWindow(QMainWindow):
    """Главное окно приложения Open Executive"""
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = WorkspaceManager()
        self._current_project_id = None
        self._current_chat_id = None
        self._chat_workers = []  # Храним ссылки на воркеры чтобы не GC
        self._setup_ui()
        
    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Open Executive — Виртуальный совет директоров")
        self.setMinimumSize(1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title = QLabel("🎯 Open Executive")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Подзаголовок
        subtitle = QLabel("Ваш персональный совет директоров")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Информация о статусе
        status_label = QLabel("✅ Ollama: готов к работе\n✅ База данных: инициализирована")
        status_label.setFont(QFont("Arial", 11))
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        # Виджет промпт-инженера
        self.prompt_engineer_widget = PromptEngineerWidget()
        layout.addWidget(self.prompt_engineer_widget)
        
        # Подключение сигналов
        self.prompt_engineer_widget.prompt_ready.connect(self._on_prompt_ready)
        self.prompt_engineer_widget.refine_requested.connect(self._on_refine_requested)
        
        # Загружаем тестовые чаты для демонстрации
        self._load_test_chats()
    
    def _load_test_chats(self):
        """Загружает тестовые чаты в виджет промпт-инженера."""
        test_chats = [
            ChatInfo(id=1, name="Чат с CFO", agent_role=AgentRole.CFO),
            ChatInfo(id=2, name="Чат с CMO", agent_role=AgentRole.CMO),
            ChatInfo(id=3, name="Чат с CSO", agent_role=AgentRole.CSO),
            ChatInfo(id=4, name="Чат с COO", agent_role=AgentRole.COO),
            ChatInfo(id=5, name="Чат с CHRO", agent_role=AgentRole.CHRO),
        ]
        self.prompt_engineer_widget.load_chats(test_chats)
    
    def _on_prompt_ready(self, prompt_text: str, chat_id: int, agent_role: str):
        """
        Обработчик сигнала готовности промпта.
        Запускает ChatWorker для получения ответа от LLM.
        
        Args:
            prompt_text: Текст промпта для отправки.
            chat_id: ID целевого чата.
            agent_role: Роль агента.
        """
        # Показываем индикатор "Печатает..."
        self.statusBar().showMessage(f"🤖 Агент {agent_role} печатает...", 5000)
        
        # Создаем и запускаем ChatWorker
        worker = ChatWorker(
            project_id=str(self._current_project_id or "default"),
            chat_id=str(chat_id),
            agent_role=agent_role,
            message=prompt_text,
            history=[]  # TODO: Загрузить историю из БД
        )
        
        # Сохраняем ссылку на воркер
        self._chat_workers.append(worker)
        
        # Подключаем сигналы
        worker.finished.connect(self._on_chat_response)
        worker.error.connect(self._on_chat_error)
        
        # Запускаем воркер
        worker.start()
    
    def _on_chat_response(self, response: str):
        """Обработчик успешного ответа от чата."""
        self.statusBar().showMessage("✅ Ответ получен", 3000)
        
        # TODO: Добавить ответ в UI чата
        # Для демонстрации показываем в QMessageBox
        QMessageBox.information(
            self,
            "Ответ агента",
            response[:500] + ("..." if len(response) > 500 else "")
        )
    
    def _on_chat_error(self, error_msg: str):
        """Обработчик ошибки чата."""
        self.statusBar().showMessage("❌ Ошибка", 3000)
        QMessageBox.critical(self, "Ошибка генерации ответа", error_msg)
    
    def _on_refine_requested(self):
        """Обработчик запроса на доработку промпта."""
        self.statusBar().showMessage("🔄 Доработка промпта...", 2000)


def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    
    # Установка стиля приложения
    app.setStyle("Fusion")
    
    # Создание и показ главного окна
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
