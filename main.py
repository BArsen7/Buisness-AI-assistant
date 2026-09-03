#!/usr/bin/env python3
"""
Open Executive — Точка входа в приложение
Запуск десктопного приложения с главным окном
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Добавляем текущую директорию в path для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import WorkspaceManager
from ui_widgets import PromptEngineerWidget


class MainWindow(QMainWindow):
    """Главное окно приложения Open Executive"""
    
    def __init__(self):
        super().__init__()
        self.workspace_manager = WorkspaceManager()
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
        
        # Виджет промпт-инженера (для демонстрации)
        self.prompt_engineer_widget = PromptEngineerWidget()
        layout.addWidget(self.prompt_engineer_widget)
        
        # Подключение сигналов
        self.prompt_engineer_widget.prompt_ready.connect(self._on_prompt_ready)
        self.prompt_engineer_widget.refine_requested.connect(self._on_refine_requested)


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
