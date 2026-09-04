"""
core/config.py
Конфигурация для ядра OpenExecutive.
"""
from dataclasses import dataclass
import os

@dataclass
class Settings:
    """Настройки приложения."""
    ollama_base_url: str = "http://localhost:11434"
    main_model: str = "qwen2.5:14b"
    fast_model: str = "qwen2.5:7b"
    timeout: float = 120.0
    
def get_settings() -> Settings:
    """Получает настройки из переменных окружения."""
    return Settings(
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        main_model=os.getenv("MAIN_MODEL", "qwen2.5:14b"),
        fast_model=os.getenv("FAST_MODEL", "qwen2.5:7b"),
        timeout=float(os.getenv("REQUEST_TIMEOUT", "120.0"))
    )
