"""
ui_widgets.py
PyQt6 виджеты для проекта Open Executive.
Включает PromptEngineerWidget и вспомогательные компоненты.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QComboBox, QLabel, QSplitter,
    QFrame, QScrollArea, QGroupBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont, QIcon

from models import AgentRole, Chat
from ui.worker import ChatWorker, PromptWorker
from exporters import export_to_pdf, export_to_pptx, export_markdown_to_structured_slides


@dataclass
class ChatInfo:
    """Информация о чате для отображения в ComboBox."""
    id: int
    name: str
    agent_role: AgentRole
    
    def display_name(self) -> str:
        """Возвращает отображаемое имя для ComboBox."""
        role_icons = {
            AgentRole.ORCHESTRATOR: "🎯",
            AgentRole.CSO: "📊",
            AgentRole.CFO: "💰",
            AgentRole.CHRO: "👥",
            AgentRole.GC: "⚖️",
            AgentRole.COO: "⚙️",
            AgentRole.CMO: "📢",
            AgentRole.CPO: "📱",
            AgentRole.BOARD: "🏦"
        }
        icon = role_icons.get(self.agent_role, "💼")
        return f"{icon} {self.name} ({self.agent_role.value})"


class PromptEngineerWidget(QWidget):
    """
    Виджет промпт-инженера для генерации и уточнения промптов.
    
    Сигналы:
        prompt_ready(str, int, str): Эмитится когда промпт готов к отправке (prompt, chat_id, agent_role).
        refine_requested(): Эмитится при запросе на доработку промпта.
        visibility_changed(bool): Эмитится при изменении видимости виджета.
    """
    
    # Сигналы
    prompt_ready = pyqtSignal(str, int, str)  # (prompt_text, target_chat_id, agent_role)
    refine_requested = pyqtSignal()
    visibility_changed = pyqtSignal(bool)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_chat_id: Optional[int] = None
        self._current_agent_role: Optional[str] = None
        self._is_visible = False
        self._prompt_worker: Optional[PromptWorker] = None
        
        self._setup_ui()
        self._apply_styles()
        
    def _setup_ui(self) -> None:
        """Инициализация пользовательского интерфейса."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        header_label = QLabel("🛠️ Промпт-Инженер")
        header_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Выбор целевого чата
        chat_group = QGroupBox("Целевой чат")
        chat_layout = QVBoxLayout(chat_group)
        
        self.chat_combo = QComboBox()
        self.chat_combo.setMinimumHeight(35)
        self.chat_combo.currentIndexChanged.connect(self._on_chat_changed)
        chat_layout.addWidget(self.chat_combo)
        
        main_layout.addWidget(chat_group)
        
        # Выбор целевой роли (QComboBox)
        role_group = QGroupBox("Целевая роль агента")
        role_layout = QVBoxLayout(role_group)
        
        self.role_combo = QComboBox()
        self.role_combo.setMinimumHeight(35)
        self._populate_role_combo()
        role_layout.addWidget(self.role_combo)
        
        main_layout.addWidget(role_group)
        
        # Сырая идея
        idea_group = QGroupBox("Ваша идея (сырой ввод)")
        idea_layout = QVBoxLayout(idea_group)
        
        self.idea_input = QTextEdit()
        self.idea_input.setPlaceholderText(
            "Введите вашу идею или вопрос...\n\n"
            "Пример: «Нужно проанализировать финансовые риски выхода на рынок Азии»"
        )
        self.idea_input.setMinimumHeight(100)
        idea_layout.addWidget(self.idea_input)
        
        main_layout.addWidget(idea_group)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("✨ Сгенерировать промпт")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        buttons_layout.addWidget(self.generate_btn)
        
        self.refine_btn = QPushButton("🔄 Доработать")
        self.refine_btn.setMinimumHeight(40)
        self.refine_btn.clicked.connect(self._on_refine_clicked)
        buttons_layout.addWidget(self.refine_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Результат (сгенерированный промпт)
        result_group = QGroupBox("Сгенерированный промпт")
        result_layout = QVBoxLayout(result_group)
        
        self.prompt_output = QTextEdit()
        self.prompt_output.setPlaceholderText("Здесь появится сгенерированный промпт...")
        self.prompt_output.setMinimumHeight(150)
        self.prompt_output.setReadOnly(False)  # Разрешаем ручное редактирование
        result_layout.addWidget(self.prompt_output)
        
        main_layout.addWidget(result_group)
        
        # Индикатор загрузки
        self.loading_label = QLabel("⏳ Обработка...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setVisible(False)
        main_layout.addWidget(self.loading_label)
        
        # Кнопка отправки в чат
        self.send_btn = QPushButton("📤 Отправить в чат")
        self.send_btn.setMinimumHeight(45)
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.send_btn.setEnabled(False)  # Disabled пока нет промпта
        main_layout.addWidget(self.send_btn)
        
        # Spacer
        main_layout.addStretch()
        
    def _apply_styles(self) -> None:
        """Применяет стилизацию через QSS."""
        self.setStyleSheet("""
            PromptEngineerWidget {
                background-color: #f5f5f5;
                border-left: 2px solid #4a90d9;
            }
            
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
                padding-top: 10px;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #4a90d9;
            }
            
            QTextEdit {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
            }
            
            QTextEdit:focus {
                border: 2px solid #4a90d9;
            }
            
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #3a7bc8;
            }
            
            QPushButton:pressed {
                background-color: #2a6bb8;
            }
            
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            
            QComboBox {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 6px;
                min-height: 35px;
                background-color: white;
            }
            
            QComboBox::drop-down {
                width: 30px;
            }
        """)
        
    def _populate_role_combo(self) -> None:
        """Заполняет ComboBox ролями агентов с расшифровкой на русском."""
        role_descriptions = {
            "ORCHESTRATOR": ("🎯", "Координатор — главный управляющий агент"),
            "CSO": ("📊", "CSO — директор по стратегии"),
            "CFO": ("💰", "CFO — финансовый директор"),
            "CHRO": ("👥", "CHRO — директор по персоналу"),
            "GC": ("⚖️", "GC — генеральный counsel (юрист)"),
            "COO": ("⚙️", "COO — операционный директор"),
            "CMO": ("📢", "CMO — директор по маркетингу"),
            "CPO": ("📱", "CPO — директор по продукту"),
            "BOARD": ("🏦", "BOARD — представитель инвесторов")
        }
        
        for role in AgentRole:
            icon, description = role_descriptions.get(role.value, ("💼", f"{role.value} — роль"))
            display_name = f"{icon} {description}"
            self.role_combo.addItem(display_name, role.value)
        
        # Устанавливаем значение по умолчанию (Координатор)
        orchestrator_index = self.role_combo.findData("ORCHESTRATOR")
        if orchestrator_index >= 0:
            self.role_combo.setCurrentIndex(orchestrator_index)
        else:
            self.role_combo.setCurrentIndex(0)
    
    def _on_chat_changed(self, index: int) -> None:
        """Обработчик изменения выбранного чата."""
        if index >= 0:
            chat_data = self.chat_combo.itemData(index)
            if chat_data is not None:
                self._current_chat_id = chat_data
    
    def _set_loading(self, loading: bool) -> None:
        """Устанавливает состояние загрузки."""
        self.loading_label.setVisible(loading)
        self.generate_btn.setEnabled(not loading)
        self.refine_btn.setEnabled(not loading)
        self.send_btn.setEnabled(not loading and bool(self.prompt_output.toPlainText().strip()))
    
    def _on_generate_clicked(self) -> None:
        """Обработчик кнопки генерации промпта."""
        idea = self.idea_input.toPlainText().strip()
        if not idea:
            self.idea_input.setFocus()
            return
        
        # Получаем целевую роль из ComboBox
        role_index = self.role_combo.currentIndex()
        if role_index < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите целевую роль агента")
            return
        
        target_role = self.role_combo.itemData(role_index)
        self._current_agent_role = target_role
        
        # Запускаем PromptWorker в отдельном потоке
        self._set_loading(True)
        
        self._prompt_worker = PromptWorker(
            idea=idea,
            target_role=target_role,
            context=""
        )
        
        self._prompt_worker.finished.connect(self._on_prompt_generated)
        self._prompt_worker.error.connect(self._on_prompt_error)
        self._prompt_worker.start()
    
    def _on_prompt_generated(self, refined_text: str) -> None:
        """Обработчик успешной генерации промпта."""
        self._set_loading(False)
        self.prompt_output.setPlainText(refined_text)
        self.send_btn.setEnabled(True)
    
    def _on_prompt_error(self, error_msg: str) -> None:
        """Обработчик ошибки генерации промпта."""
        self._set_loading(False)
        QMessageBox.critical(self, "Ошибка генерации промпта", error_msg)
        # Все равно показываем текст (даже если это сообщение об ошибке)
        self.prompt_output.setPlainText(error_msg)
    
    def _on_refine_clicked(self) -> None:
        """Обработчик кнопки доработки промпта."""
        current_prompt = self.prompt_output.toPlainText().strip()
        if not current_prompt:
            return
        
        # Получаем целевую роль
        role_index = self.role_combo.currentIndex()
        if role_index < 0:
            target_role = "EXPERT"
        else:
            target_role = self.role_combo.itemData(role_index)
        
        self._set_loading(True)
        
        # Запускаем PromptWorker для уточнения
        self._prompt_worker = PromptWorker(
            idea=current_prompt,  # Передаем текущий промпт как идею для уточнения
            target_role=target_role,
            context=""
        )
        
        self._prompt_worker.finished.connect(self._on_prompt_generated)
        self._prompt_worker.error.connect(self._on_prompt_error)
        self._prompt_worker.start()
        
        self.refine_requested.emit()
    
    def _on_send_clicked(self) -> None:
        """Обработчик кнопки отправки в чат."""
        prompt_text = self.prompt_output.toPlainText().strip()
        if prompt_text and self._current_chat_id is not None:
            role = self._current_agent_role or "EXPERT"
            self.prompt_ready.emit(prompt_text, self._current_chat_id, role)
            
    def load_chats(self, chats: List[ChatInfo]) -> None:
        """
        Загружает список чатов в ComboBox.
        
        Args:
            chats: Список объектов ChatInfo для отображения.
        """
        self.chat_combo.clear()
        
        for chat in chats:
            display_name = chat.display_name()
            self.chat_combo.addItem(display_name, chat.id)
            
        if chats:
            self._current_chat_id = chats[0].id
            
    def set_generated_prompt(self, prompt: str) -> None:
        """
        Устанавливает сгенерированный промпт в поле вывода.
        
        Args:
            prompt: Текст промпта для отображения.
        """
        self.prompt_output.setPlainText(prompt)
        self.send_btn.setEnabled(bool(prompt.strip()))
        
    def clear_inputs(self) -> None:
        """Очищает все поля ввода."""
        self.idea_input.clear()
        self.prompt_output.clear()
        self.send_btn.setEnabled(False)
        
    def toggle_visibility(self, visible: bool) -> None:
        """
        Переключает видимость виджета с анимацией.
        
        Args:
            visible: True для показа, False для скрытия.
        """
        self._is_visible = visible
        self.setVisible(visible)
        self.visibility_changed.emit(visible)


class CollapsiblePanel(QWidget):
    """
    Сворачиваемая панель для анимированного показа/скрытия виджетов.
    Может быть использована для панели промпт-инженера.
    """
    
    expanded = pyqtSignal()
    collapsed = pyqtSignal()
    
    def __init__(self, content_widget: QWidget, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.content_widget = content_widget
        self.is_expanded = False
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Инициализация UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Создаем animation widget
        self.animation_widget = QWidget()
        anim_layout = QVBoxLayout(self.animation_widget)
        anim_layout.setContentsMargins(0, 0, 0, 0)
        anim_layout.addWidget(self.content_widget)
        
        layout.addWidget(self.animation_widget)
        
        # Анимация размера
        self.animation = QPropertyAnimation(self.animation_widget, b"maximumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Начальное состояние - свернуто
        self.animation_widget.setMaximumWidth(0)
        
    def toggle(self) -> None:
        """Переключает состояние панели."""
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()
            
    def expand(self) -> None:
        """Разворачивает панель."""
        self.is_expanded = True
        self.animation.setEndValue(400)  # Ширина панели
        self.animation.start()
        self.animation_widget.setVisible(True)
        self.expanded.emit()
        
    def collapse(self) -> None:
        """Сворачивает панель."""
        self.is_expanded = False
        self.animation.setEndValue(0)
        self.animation.start()
        
        # Скрываем после завершения анимации
        self.animation.finished.connect(
            lambda: self.animation_widget.setVisible(False),
            Qt.ConnectionType.SingleShotConnection
        )
        self.collapsed.emit()


class ChatMessageBubble(QFrame):
    """
    Виджет сообщения чата в стиле bubble.
    """
    
    def __init__(
        self, 
        content: str, 
        is_user: bool = True,
        timestamp: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.is_user = is_user
        
        self._setup_ui(content, timestamp)
        self._apply_styles()
        
    def _setup_ui(self, content: str, timestamp: str) -> None:
        """Инициализация UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Текст сообщения
        self.label = QLabel(content)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        layout.addWidget(self.label)
        
        # Время (опционально)
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet("color: #888; font-size: 11px;")
            if self.is_user:
                time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(time_label)
            
    def _apply_styles(self) -> None:
        """Применяет стилизацию."""
        if self.is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: #4a90d9;
                    color: white;
                    border-radius: 12px;
                }
                QLabel {
                    color: white;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #e5e5ea;
                    color: black;
                    border-radius: 12px;
                }
                QLabel {
                    color: black;
                }
            """)


# Пример использования и тестирования
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter
    
    app = QApplication(sys.argv)
    
    # Главное окно
    window = QMainWindow()
    window.setWindowTitle("Open Executive - Prompt Engineer Widget Test")
    window.setGeometry(100, 100, 1200, 800)
    
    # Центральный виджет со Splitter
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    splitter = QSplitter(Qt.Orientation.Horizontal)
    main_layout = QHBoxLayout(central_widget)
    main_layout.addWidget(splitter)
    
    # Левая часть - заглушка для чата
    chat_placeholder = QWidget()
    chat_placeholder.setStyleSheet("background-color: white;")
    chat_layout = QVBoxLayout(chat_placeholder)
    chat_label = QLabel("Основная область чата")
    chat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    chat_layout.addWidget(chat_label)
    
    # Правая часть - Prompt Engineer Widget
    prompt_widget = PromptEngineerWidget()
    
    # Тестовые данные
    test_chats = [
        ChatInfo(id=1, name="Чат с CFO", agent_role=AgentRole.CFO),
        ChatInfo(id=2, name="Чат с CMO", agent_role=AgentRole.CMO),
        ChatInfo(id=3, name="Чат с CSO", agent_role=AgentRole.CSO),
    ]
    prompt_widget.load_chats(test_chats)
    
    # Обработка сигналов
    def on_prompt_ready(prompt: str, chat_id: int):
        print(f"Prompt ready for chat {chat_id}:")
        print(prompt[:100] + "...")
        
    def on_refine():
        print("Refinement requested")
        
    prompt_widget.prompt_ready.connect(on_prompt_ready)
    prompt_widget.refine_requested.connect(on_refine)
    
    splitter.addWidget(chat_placeholder)
    splitter.addWidget(prompt_widget)
    splitter.setSizes([800, 400])
    
    window.show()
    sys.exit(app.exec())
