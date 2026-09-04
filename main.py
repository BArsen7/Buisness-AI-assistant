#!/usr/bin/env python3
"""
Open Executive — Точка входа в приложение
Запуск десктопного приложения с главным окном
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Настройка логирования в терминал
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    # Пытаемся загрузить .env из разных возможных мест
    for env_path in [".env", Path(__file__).parent / ".env"]:
        if Path(env_path).exists():
            load_dotenv(env_path)
            logger.info(f"Загружен .env файл: {env_path}")
            break
except ImportError:
    logger.warning("Warning: python-dotenv not installed. Using environment variables only.")


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
        logger.debug(f"Директория создана/проверена: {dir_path}")
    
    # Также создаем директорию в домашней папке пользователя для надежности
    # (используется при запуске скомпилированного приложения)
    user_data_dir = Path.home() / ".openexecutive"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Директория пользователя: {user_data_dir}")
    
    return base_dir, user_data_dir


# Создаем директории до импорта PyQt6
base_dir, user_data_dir = ensure_data_directories()

# Добавляем текущую директорию в path для импортов
sys.path.insert(0, str(base_dir))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QMessageBox, QSplitter, QFrame, QScrollArea, 
    QListWidget, QListWidgetItem, QPushButton, QTextEdit,
    QComboBox, QGroupBox, QFileDialog, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon

from database import WorkspaceManager
from models import AgentRole, Project, Chat as ChatModel
from ui.worker import ChatWorker, PromptWorker


# Стили для приложения
APP_STYLESHEET = """
QMainWindow {
    background-color: #ffffff;
}

/* Стили для списка проектов и чатов */
QListWidget {
    border: 1px solid #d0d0d0;
    border-radius: 5px;
    background-color: white;
    font-size: 13px;
    padding: 5px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 3px;
    margin: 2px 0;
}

QListWidget::item:hover {
    background-color: #e3f2fd;
}

QListWidget::item:selected {
    background-color: #4a90d9;
    color: black;
    font-weight: bold;
}

/* Кнопки */
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

/* Поля ввода */
QTextEdit, QLineEdit, QComboBox {
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 8px;
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
    background-color: white;
}

QTextEdit:focus, QLineEdit:focus {
    border: 2px solid #4a90d9;
}

QComboBox {
    min-height: 35px;
}

QComboBox::item {
    padding: 8px;
    border-radius: 3px;
    margin: 2px 0;
    background-color: white;
    color: black;
}

QComboBox::item:hover {
    background-color: #e3f2fd;
    color: black;
    font-weight: bold;
}

QComboBox::item:selected {
    background-color: #4a90d9;
    color: black;
    font-weight: bold;
}

QComboBox::drop-down {
    width: 30px;
}

/* Группы */
QGroupBox {
    font-weight: bold;
    margin-top: 10px;
    padding-top: 10px;
    border: 1px solid #d0d0d0;
    border-radius: 5px;
    background-color: white;
    font-size: 13px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #4a90d9;
}

/* Разделители */
QSplitter::handle {
    background-color: #d0d0d0;
    width: 1px;
}

/* Scrollbar */
QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

/* Status bar */
QStatusBar {
    background-color: #f5f5f5;
    border-top: 1px solid #d0d0d0;
    font-size: 12px;
}
"""


class ProjectListWidget(QWidget):
    """Виджет списка проектов слева."""
    
    project_selected = pyqtSignal(int)  # project_id
    create_project_requested = pyqtSignal()
    chat_selected = pyqtSignal(int)  # chat_id
    
    def __init__(self, workspace_manager: WorkspaceManager, parent=None):
        super().__init__(parent)
        self.workspace_manager = workspace_manager
        self._current_project_id = None
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок
        title = QLabel("📁 Проекты")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Кнопка создания проекта
        self.create_btn = QPushButton("+ Новый проект")
        self.create_btn.clicked.connect(self.create_project_requested.emit)
        layout.addWidget(self.create_btn)
        
        # Список проектов
        self.project_list = QListWidget()
        self.project_list.setMaximumWidth(250)
        self.project_list.itemClicked.connect(self._on_project_clicked)
        layout.addWidget(self.project_list)
        
        # Заголовок чатов
        self.chats_label = QLabel("💬 Чаты проекта")
        self.chats_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.chats_label.setVisible(False)
        layout.addWidget(self.chats_label)
        
        # Список чатов
        self.chat_list = QListWidget()
        self.chat_list.setMaximumWidth(250)
        self.chat_list.itemClicked.connect(self._on_chat_clicked)
        self.chat_list.setVisible(False)
        layout.addWidget(self.chat_list)
        
        layout.addStretch()
        
    def refresh_projects(self):
        """Обновляет список проектов."""
        logger.info("Обновление списка проектов")
        self.project_list.clear()
        
        # Добавляем кнопку "Создать новый проект" как первый элемент
        create_item = QListWidgetItem("➕ Создать новый проект")
        create_item.setForeground(Qt.GlobalColor.darkGray)
        self.project_list.addItem(create_item)
        
        projects = self.workspace_manager.list_projects()
        for project in projects:
            item = QListWidgetItem(f"📁 {project.name}")
            item.setData(Qt.ItemDataRole.UserRole, project.id)
            self.project_list.addItem(item)
            
    def _on_project_clicked(self, item: QListWidgetItem):
        """Обработчик клика по проекту."""
        if item.text() == "➕ Создать новый проект":
            self.create_project_requested.emit()
            return
            
        project_id = item.data(Qt.ItemDataRole.UserRole)
        if project_id:
            logger.info(f"Выбран проект ID={project_id}")
            self._current_project_id = project_id
            self.project_selected.emit(project_id)
            self._load_chats_for_project(project_id)
            
    def _load_chats_for_project(self, project_id: int):
        """Загружает чаты для выбранного проекта."""
        self.chat_list.clear()
        chats = self.workspace_manager.list_chats(project_id)
        
        if chats:
            self.chats_label.setVisible(True)
            self.chat_list.setVisible(True)
            
            for chat in chats:
                role_icons = {
                    "ORCHESTRATOR": "🎯", "CSO": "📊", "CFO": "💰",
                    "CHRO": "👥", "GC": "⚖️", "COO": "⚙️",
                    "CMO": "📢", "CPO": "📱", "BOARD": "🏦"
                }
                icon = role_icons.get(chat.agent_role.value, "💼")
                item = QListWidgetItem(f"{icon} {chat.name}")
                item.setData(Qt.ItemDataRole.UserRole, chat.id)
                self.chat_list.addItem(item)
        else:
            self.chats_label.setVisible(False)
            self.chat_list.setVisible(False)
            
    def _on_chat_clicked(self, item: QListWidgetItem):
        """Обработчик клика по чату."""
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        if chat_id:
            logger.info(f"Выбран чат ID={chat_id}")
            self.chat_selected.emit(chat_id)
            
    def get_current_project_id(self):
        """Возвращает ID текущего проекта."""
        return self._current_project_id


class ChatViewWidget(QWidget):
    """Центральный виджет чата."""
    
    message_sent = pyqtSignal(str, int, str)  # message, chat_id, agent_role
    
    def __init__(self, workspace_manager: WorkspaceManager, parent=None):
        super().__init__(parent)
        self.workspace_manager = workspace_manager
        self._current_chat_id = None
        self._current_agent_role = None
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Заголовок чата
        self.chat_title = QLabel("🆕 Новый чат")
        self.chat_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(self.chat_title)
        
        # Область сообщений
        self.messages_area = QTextEdit()
        self.messages_area.setReadOnly(True)
        self.messages_area.setPlaceholderText(
            "Здесь будут отображаться сообщения...\n\n"
            "Выберите проект и чат слева или создайте новый."
        )
        layout.addWidget(self.messages_area)
        
        # Поле ввода сообщения
        input_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Введите сообщение...")
        self.message_input.setMaximumHeight(100)
        input_layout.addWidget(self.message_input)
        
        # Кнопка отправки
        self.send_btn = QPushButton("📤 Отправить")
        self.send_btn.setMaximumWidth(120)
        self.send_btn.clicked.connect(self._on_send_clicked)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Кнопки экспорта
        export_layout = QHBoxLayout()
        self.export_pdf_btn = QPushButton("📄 Экспорт в PDF")
        self.export_pdf_btn.clicked.connect(self._on_export_pdf)
        export_layout.addWidget(self.export_pdf_btn)
        
        self.export_pptx_btn = QPushButton("📊 Экспорт в PPTX")
        self.export_pptx_btn.clicked.connect(self._on_export_pptx)
        export_layout.addWidget(self.export_pptx_btn)
        
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
    def _on_send_clicked(self):
        """Отправка сообщения."""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
            
        if self._current_chat_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите чат или создайте новый")
            return
            
        logger.info(f"Отправка сообщения в чат ID={self._current_chat_id}")
        self.message_sent.emit(message, self._current_chat_id, self._current_agent_role or "ORCHESTRATOR")
        self.message_input.clear()
        
    def add_message(self, role: str, content: str):
        """Добавляет сообщение в чат."""
        role_display = "👤 Вы" if role == "user" else "🤖 Агент"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.messages_area.append(f"<b>{role_display}</b> <span style='color: gray;'>[{timestamp}]</span>")
        self.messages_area.append(f"<p>{content.replace(chr(10), '<br>')}</p>")
        self.messages_area.append("<hr>")
        self.messages_area.scrollToBottom()
        
    def set_chat_info(self, chat_name: str, agent_role: str):
        """Устанавливает информацию о текущем чате."""
        self.chat_title.setText(f"💬 {chat_name}")
        self._current_agent_role = agent_role
        
    def clear_chat(self):
        """Очищает чат."""
        self.messages_area.clear()
        self.chat_title.setText("🆕 Новый чат")
        self._current_chat_id = None
        self._current_agent_role = None
        
    def load_chat_history(self, chat_id: int):
        """Загружает историю сообщений чата."""
        self.messages_area.clear()
        messages = self.workspace_manager.get_messages(chat_id)
        
        for msg in messages:
            role = "user" if msg.role == "user" else "assistant"
            self.add_message(role, msg.content)
            
    def _on_export_pdf(self):
        """Экспорт в PDF."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить в PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            logger.info(f"Экспорт в PDF: {file_path}")
            # TODO: Реализовать экспорт
        
    def _on_export_pptx(self):
        """Экспорт в PPTX."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить в PPTX", "", "PowerPoint Files (*.pptx);;All Files (*)"
        )
        if file_path:
            logger.info(f"Экспорт в PPTX: {file_path}")
            # TODO: Реализовать экспорт
            
    def set_current_chat_id(self, chat_id: int):
        """Устанавливает текущий ID чата."""
        self._current_chat_id = chat_id


class MainWindow(QMainWindow):
    """Главное окно приложения Open Executive."""
    
    def __init__(self):
        super().__init__()
        logger.info("Инициализация главного окна")
        self.workspace_manager = WorkspaceManager()
        self._chat_workers = []
        self._prompt_worker = None
        self._setup_ui()
        self._refresh_project_list()
        
    def _setup_ui(self):
        """Настройка пользовательского интерфейса."""
        self.setWindowTitle("Open Executive — Виртуальный совет директоров")
        self.setMinimumSize(1400, 900)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Кнопки управления панелями (сверху)
        panel_buttons_widget = QWidget()
        panel_buttons_layout = QHBoxLayout(panel_buttons_widget)
        panel_buttons_layout.setContentsMargins(5, 5, 5, 5)
        panel_buttons_layout.setSpacing(5)
        
        # Кнопка сворачивания/разворачивания левой панели
        self.toggle_projects_btn = QPushButton("◀")
        self.toggle_projects_btn.setFixedSize(30, 30)
        self.toggle_projects_btn.setToolTip("Свернуть/развернуть панель проектов")
        self.toggle_projects_btn.clicked.connect(self._toggle_projects_panel)
        panel_buttons_layout.addWidget(self.toggle_projects_btn)
        
        # Spacer для центрации кнопок
        panel_buttons_layout.addStretch()
        
        # Кнопка сворачивания/разворачивания правой панели
        self.toggle_prompt_btn = QPushButton("▶")
        self.toggle_prompt_btn.setFixedSize(30, 30)
        self.toggle_prompt_btn.setToolTip("Свернуть/развернуть панель промпт-инженера")
        self.toggle_prompt_btn.clicked.connect(self._toggle_prompt_panel)
        panel_buttons_layout.addWidget(self.toggle_prompt_btn)
        
        main_layout.addWidget(panel_buttons_widget)
        
        # Splitter для разделения панелей
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - проекты
        self.project_panel = ProjectListWidget(self.workspace_manager)
        self.project_panel.setMinimumWidth(250)
        self.project_panel.setMaximumWidth(400)
        splitter.addWidget(self.project_panel)
        
        # Центральная панель - чат
        self.chat_view = ChatViewWidget(self.workspace_manager)
        self.chat_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.addWidget(self.chat_view)
        
        # Правая панель - промпт инженер
        self.prompt_panel = self._create_prompt_engineer_panel()
        self.prompt_panel.setMinimumWidth(400)
        self.prompt_panel.setMaximumWidth(600)
        self.prompt_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        splitter.addWidget(self.prompt_panel)
        
        # Сохраняем ссылки на панели для переключения
        self._projects_panel_visible = True
        self._prompt_panel_visible = True
        
        splitter.setStretchFactor(0, 0)  # Левая панель не растягивается
        splitter.setStretchFactor(1, 3)  # Центральная растягивается максимально
        splitter.setStretchFactor(2, 1)  # Правая панель растягивается по высоте чата
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("✅ Готов к работе", 5000)
        
        # Подключение сигналов
        self._connect_signals()
        
        logger.info("UI инициализирован успешно")
        
    def _create_prompt_engineer_panel(self) -> QWidget:
        """Создает панель промпт-инженера."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Заголовок
        header = QLabel("🛠️ Промпт-Инженер")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Выбор роли агента - используем QListWidget вместо QComboBox
        role_group = QGroupBox("Роль агента")
        role_layout = QVBoxLayout(role_group)
        
        self.role_list = QListWidget()
        self.role_list.setMaximumHeight(200)
        self.role_list.itemClicked.connect(self._on_role_selected)
        self._populate_role_list()
        role_layout.addWidget(self.role_list)
        layout.addWidget(role_group)
        
        # Храним текущую выбранную роль
        self._current_agent_role = "ORCHESTRATOR"
        
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
        layout.addWidget(idea_group)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("✨ Сгенерировать промпт")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.clicked.connect(self._on_generate_prompt)
        buttons_layout.addWidget(self.generate_btn)
        
        self.refine_btn = QPushButton("🔄 Доработать")
        self.refine_btn.setMinimumHeight(40)
        self.refine_btn.clicked.connect(self._on_refine_prompt)
        buttons_layout.addWidget(self.refine_btn)
        
        layout.addLayout(buttons_layout)
        
        # Результат
        result_group = QGroupBox("Сгенерированный промпт")
        result_layout = QVBoxLayout(result_group)
        
        self.prompt_output = QTextEdit()
        self.prompt_output.setPlaceholderText("Здесь появится сгенерированный промпт...")
        self.prompt_output.setMinimumHeight(150)
        result_layout.addWidget(self.prompt_output)
        layout.addWidget(result_group)
        
        # Индикатор загрузки
        self.loading_label = QLabel("⏳ Обработка...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label)
        
        # Кнопка отправки
        self.send_prompt_btn = QPushButton("📤 Отправить в чат")
        self.send_prompt_btn.setMinimumHeight(45)
        self.send_prompt_btn.clicked.connect(self._on_send_prompt_to_chat)
        self.send_prompt_btn.setEnabled(False)
        layout.addWidget(self.send_prompt_btn)
        
        layout.addStretch()
        
        return panel
        
    def _populate_role_list(self):
        """Заполняет QListWidget ролями агентов с расшифровкой на русском."""
        self.role_list.clear()
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
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, role.value)
            self.role_list.addItem(item)
            
        # Выбираем первый элемент по умолчанию
        if self.role_list.count() > 0:
            self.role_list.setCurrentRow(0)
        
    def _on_role_selected(self, item: QListWidgetItem):
        """Обработчик выбора роли."""
        role = item.data(Qt.ItemDataRole.UserRole)
        if role:
            self._current_agent_role = role
            logger.info(f"Выбрана роль: {role}")
        
    def _connect_signals(self):
        """Подключает сигналы между виджетами."""
        # Проект создан
        self.project_panel.create_project_requested.connect(self._on_create_project)
        
        # Проект выбран
        self.project_panel.project_selected.connect(self._on_project_selected)
        
        # Чат выбран
        self.project_panel.chat_selected.connect(self._on_chat_selected)
        
        # Сообщение отправлено из чата
        self.chat_view.message_sent.connect(self._on_message_sent)
        
    def _toggle_projects_panel(self):
        """Сворачивает/разворачивает левую панель проектов."""
        if self._projects_panel_visible:
            self.project_panel.setVisible(False)
            self.toggle_projects_btn.setText("▼")
            self._projects_panel_visible = False
            logger.debug("Панель проектов скрыта")
        else:
            self.project_panel.setVisible(True)
            self.toggle_projects_btn.setText("▲")
            self._projects_panel_visible = True
            logger.debug("Панель проектов отображена")
            
    def _toggle_prompt_panel(self):
        """Сворачивает/разворачивает правую панель промпт-инженера."""
        if self._prompt_panel_visible:
            self.prompt_panel.setVisible(False)
            self.toggle_prompt_btn.setText("▼")
            self._prompt_panel_visible = False
            logger.debug("Панель промпт-инженера скрыта")
        else:
            self.prompt_panel.setVisible(True)
            self.toggle_prompt_btn.setText("▲")
            self._prompt_panel_visible = True
            logger.debug("Панель промпт-инженера отображена")
        
    def _refresh_project_list(self):
        """Обновляет список проектов."""
        self.project_panel.refresh_projects()
        
    def _on_create_project(self):
        """Создание нового проекта."""
        logger.info("Запрос на создание нового проекта")
        
        # Простой диалог для ввода имени проекта
        from PyQt6.QtWidgets import QInputDialog
        
        project_name, ok = QInputDialog.getText(
            self, "Новый проект", "Введите название проекта:"
        )
        
        if ok and project_name.strip():
            try:
                project = self.workspace_manager.create_project(project_name.strip())
                logger.info(f"Создан проект: {project.name} (ID={project.id})")
                self._refresh_project_list()
                self.statusBar().showMessage(f"✅ Проект '{project.name}' создан", 3000)
            except Exception as e:
                logger.error(f"Ошибка создания проекта: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать проект: {e}")
                
    def _on_project_selected(self, project_id: int):
        """Проект выбран."""
        logger.info(f"Проект выбран: ID={project_id}")
        self.statusBar().showMessage(f"📁 Проект ID={project_id}", 2000)
        
    def _on_chat_selected(self, chat_id: int):
        """Чат выбран."""
        logger.info(f"Чат выбран: ID={chat_id}")
        chat = self.workspace_manager.get_chat(chat_id)
        
        if chat:
            self.chat_view.set_current_chat_id(chat_id)
            self.chat_view.set_chat_info(chat.name, chat.agent_role.value)
            self.chat_view.load_chat_history(chat_id)
            self.statusBar().showMessage(f"💬 Чат '{chat.name}' загружен", 2000)
            
    def _on_message_sent(self, message: str, chat_id: int, agent_role: str):
        """Сообщение отправлено пользователем."""
        logger.info(f"Сообщение отправлено в чат {chat_id}: {message[:50]}...")
        
        # Добавляем сообщение пользователя в БД и UI
        self.workspace_manager.add_message(chat_id, "user", message)
        self.chat_view.add_message("user", message)
        
        # Показываем индикатор "Печатает..."
        self.statusBar().showMessage(f"🤖 Агент {agent_role} печатает...", 0)
        
        # Создаем и запускаем ChatWorker
        worker = ChatWorker(
            project_id=str(self.project_panel.get_current_project_id() or "default"),
            chat_id=str(chat_id),
            agent_role=agent_role,
            message=message,
            history=[]
        )
        
        self._chat_workers.append(worker)
        worker.finished.connect(self._on_chat_response)
        worker.error.connect(self._on_chat_error)
        worker.start()
        
        logger.info("ChatWorker запущен")
        
    def _on_chat_response(self, response: str):
        """Ответ от агента получен."""
        logger.info(f"Ответ получен: {response[:100]}...")
        self.statusBar().showMessage("✅ Ответ получен", 3000)
        
        # Сохраняем в БД
        if self.chat_view._current_chat_id:
            self.workspace_manager.add_message(
                self.chat_view._current_chat_id, "assistant", response
            )
            
        # Добавляем в UI
        self.chat_view.add_message("assistant", response)
        
    def _on_chat_error(self, error_msg: str):
        """Ошибка при получении ответа."""
        logger.error(f"Ошибка ChatWorker: {error_msg}")
        self.statusBar().showMessage("❌ Ошибка", 3000)
        QMessageBox.critical(self, "Ошибка генерации ответа", error_msg)
        
    def _set_loading(self, loading: bool):
        """Устанавливает состояние загрузки."""
        self.loading_label.setVisible(loading)
        self.generate_btn.setEnabled(not loading)
        self.refine_btn.setEnabled(not loading)
        self.send_prompt_btn.setEnabled(not loading and bool(self.prompt_output.toPlainText().strip()))
        
    def _on_generate_prompt(self):
        """Генерация промпта."""
        idea = self.idea_input.toPlainText().strip()
        if not idea:
            logger.warning("Пустая идея для генерации промпта")
            self.idea_input.setFocus()
            return
            
        role = self._current_agent_role
        logger.info(f"Генерация промпта для роли: {role}")
        
        self._set_loading(True)
        
        self._prompt_worker = PromptWorker(
            idea=idea,
            target_role=role,
            context=""
        )
        
        self._prompt_worker.finished.connect(self._on_prompt_generated)
        self._prompt_worker.error.connect(self._on_prompt_error)
        self._prompt_worker.start()
        
    def _on_prompt_generated(self, refined_text: str):
        """Промпт сгенерирован."""
        logger.info("Промпт успешно сгенерирован")
        self._set_loading(False)
        self.prompt_output.setPlainText(refined_text)
        self.send_prompt_btn.setEnabled(True)
        
    def _on_prompt_error(self, error_msg: str):
        """Ошибка генерации промпта."""
        logger.error(f"Ошибка генерации промпта: {error_msg}")
        self._set_loading(False)
        QMessageBox.critical(self, "Ошибка генерации промпта", error_msg)
        self.prompt_output.setPlainText(error_msg)
        
    def _on_refine_prompt(self):
        """Доработка промпта."""
        current_prompt = self.prompt_output.toPlainText().strip()
        if not current_prompt:
            logger.warning("Нет промпта для доработки")
            return
            
        role = self._current_agent_role
        logger.info(f"Доработка промпта для роли: {role}")
        
        self._set_loading(True)
        
        self._prompt_worker = PromptWorker(
            idea=current_prompt,
            target_role=role,
            context=""
        )
        
        self._prompt_worker.finished.connect(self._on_prompt_generated)
        self._prompt_worker.error.connect(self._on_prompt_error)
        self._prompt_worker.start()
        
    def _on_send_prompt_to_chat(self):
        """Отправка промпта в чат."""
        prompt_text = self.prompt_output.toPlainText().strip()
        
        if not prompt_text:
            logger.warning("Пустой промпт для отправки")
            return
            
        # Если чат не выбран, создаем новый
        if self.chat_view._current_chat_id is None:
            project_id = self.project_panel.get_current_project_id()
            
            if project_id is None:
                QMessageBox.warning(
                    self, "Ошибка", 
                    "Выберите или создайте проект перед отправкой в чат"
                )
                return
                
            # Создаем новый чат
            agent_role = AgentRole(self._current_agent_role)
            
            chat_name = f"Чат с {agent_role.value}"
            try:
                chat = self.workspace_manager.create_chat(project_id, chat_name, agent_role)
                logger.info(f"Создан новый чат: {chat.name} (ID={chat.id})")
                self._refresh_project_list()
                self.chat_view.set_current_chat_id(chat.id)
                self.chat_view.set_chat_info(chat.name, agent_role.value)
            except Exception as e:
                logger.error(f"Ошибка создания чата: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать чат: {e}")
                return
                
        # Эмитим сигнал отправки сообщения
        self._on_message_sent(prompt_text, self.chat_view._current_chat_id, self._current_agent_role)


def main():
    """Точка входа в приложение."""
    logger.info("=" * 50)
    logger.info("Запуск приложения Open Executive")
    logger.info("=" * 50)
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    logger.info("Главное окно отображено")
    
    exit_code = app.exec()
    logger.info(f"Приложение завершено с кодом: {exit_code}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
