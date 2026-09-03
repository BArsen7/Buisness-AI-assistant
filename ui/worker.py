"""
ui/worker.py
Асинхронные воркеры для PyQt6.
Запускают тяжелые операции (LLM запросы) в отдельных потоках QThread,
чтобы не блокировать основной UI поток.
"""

import sys
import os
from typing import List, Dict, Any, Optional

from PyQt6.QtCore import QThread, pyqtSignal

# Добавляем родительскую директорию в path для импортов core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ChatWorker(QThread):
    """
    Воркер для генерации ответа чата.
    
    Сигналы:
        finished(str): Эмитится при успешном завершении с текстом ответа.
        error(str): Эмитится при возникновении ошибки с описанием проблемы.
    """
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(
        self,
        project_id: str,
        chat_id: str,
        agent_role: str,
        message: str,
        history: List[Dict[str, Any]] = None,
        parent: Optional[QThread] = None
    ):
        """
        Инициализация воркера.
        
        Args:
            project_id: ID проекта.
            chat_id: ID чата.
            agent_role: Роль агента (CEO, CFO, CMO и т.д.).
            message: Текущее сообщение пользователя.
            history: История чата (список сообщений).
            parent: Родительский объект QThread.
        """
        super().__init__(parent)
        self.project_id = project_id
        self.chat_id = chat_id
        self.agent_role = agent_role
        self.message = message
        self.history = history if history is not None else []
    
    def run(self) -> None:
        """
        Основной метод выполнения в отдельном потоке.
        Вызывает core.runner.generate_response и эмитит результаты.
        """
        try:
            from core.runner import generate_response
            
            response = generate_response(
                project_id=self.project_id,
                chat_id=self.chat_id,
                agent_role=self.agent_role,
                message=self.message,
                history=self.history
            )
            
            # Проверяем, не является ли ответ ошибкой
            if response.startswith("[Ошибка"):
                self.error.emit(response)
            else:
                self.finished.emit(response)
                
        except ImportError as e:
            self.error.emit(f"Ошибка импорта модуля core.runner: {str(e)}")
        except Exception as e:
            self.error.emit(f"Неожиданная ошибка в ChatWorker: {str(e)}")


class PromptWorker(QThread):
    """
    Воркер для генерации/уточнения промпта.
    
    Сигналы:
        finished(str): Эмитится при успешном завершении с уточненным текстом промпта.
        error(str): Эмитится при возникновении ошибки с описанием проблемы.
    """
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(
        self,
        idea: str,
        target_role: str,
        context: str = "",
        parent: Optional[QThread] = None
    ):
        """
        Инициализация воркера.
        
        Args:
            idea: Сырая идея/вопрос пользователя.
            target_role: Целевая роль агента.
            context: Дополнительный контекст (история чата и т.д.).
            parent: Родительский объект QThread.
        """
        super().__init__(parent)
        self.idea = idea
        self.target_role = target_role
        self.context = context
    
    def run(self) -> None:
        """
        Основной метод выполнения в отдельном потоке.
        Вызывает core.runner.generate_prompt_refinement и эмитит результаты.
        """
        try:
            from core.runner import generate_prompt_refinement
            
            refined_text = generate_prompt_refinement(
                idea=self.idea,
                target_role=self.target_role,
                context=self.context
            )
            
            # Проверяем, не является ли ответ ошибкой
            if refined_text.startswith("[Ошибка"):
                self.error.emit(refined_text)
            else:
                self.finished.emit(refined_text)
                
        except ImportError as e:
            self.error.emit(f"Ошибка импорта модуля core.runner: {str(e)}")
        except Exception as e:
            self.error.emit(f"Неожиданная ошибка в PromptWorker: {str(e)}")


# Пример использования (для тестирования)
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Тест ChatWorker
    print("Тестирование ChatWorker...")
    worker = ChatWorker(
        project_id="test_project",
        chat_id="test_chat",
        agent_role="CFO",
        message="Проанализируй финансовые риски",
        history=[]
    )
    
    def on_finished(response):
        print(f"ChatWorker finished: {response[:100]}...")
        app.quit()
    
    def on_error(msg):
        print(f"ChatWorker error: {msg}")
        app.quit()
    
    worker.finished.connect(on_finished)
    worker.error.connect(on_error)
    worker.start()
    
    sys.exit(app.exec())
