# Open Executive — Локальный виртуальный совет директоров

Десктопное AI-приложение для принятия стратегических решений с помощью мультиагентной системы из 9 ролей (CFO, CMO, COO, CEO и др.). Работает полностью локально на вашем компьютере.

## 🚀 Особенности

- **Мультиагентная архитектура**: 9 специализированных ролей (Orchestrator, CSO, CFO, CHRO, GC, COO, CMO, CPO, Board)
- **Полная приватность**: Все данные хранятся локально (SQLite + ChromaDB)
- **Локальные LLM**: Интеграция с Ollama (модели qwen2.5:14b и qwen2.5:7b)
- **Умный промпт-инженер**: Автоматическая генерация и доработка промптов под конкретную роль
- **Экспорт артефактов**: Выгрузка результатов в PDF и PowerPoint
- **Нативный UI**: PyQt6 с современной стилизацией (QSS)

## 📋 Требования

- Python 3.9+
- Ollama (установленный локально)
- Модели Ollama: `qwen2.5:14b` и `qwen2.5:7b`

## 🛠️ Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd open-executive
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Установка и настройка Ollama

#### Установка Ollama
- **Linux**: `curl -fsSL https://ollama.com/install.sh | sh`
- **macOS**: `brew install ollama` или скачайте с [ollama.com](https://ollama.com)
- **Windows**: Скачайте установщик с [ollama.com](https://ollama.com)

#### Запуск Ollama сервера
```bash
ollama serve
```

#### Загрузка необходимых моделей
```bash
ollama pull qwen2.5:14b
ollama pull qwen2.5:7b
```

Проверка работы:
```bash
ollama run qwen2.5:7b "Привет!"
```

## 🚀 Запуск приложения

### Основной запуск

```bash
python main.py
```

### Запуск с указанием порта Ollama (если нестандартный)

```bash
OLLAMA_HOST=http://localhost:11434 python main.py
```

### Запуск в режиме разработки (с подробным логированием)

```bash
LOG_LEVEL=DEBUG python main.py
```

## 📁 Структура проекта

```
open-executive/
├── main.py                 # Точка входа в приложение
├── database.py             # WorkspaceManager: SQLite + ChromaDB
├── prompt_engineer.py      # PromptEngineer: генерация промптов
├── ui_widgets.py           # PyQt6 виджеты (PromptEngineerWidget и др.)
├── exporters.py            # Экспорт в PDF и PowerPoint
├── models.py               # Модели данных
├── agents/                 # Логика агентов (ролей)
│   ├── __init__.py
│   └── base_agent.py       # Базовый класс агента
├── utils/                  # Утилиты
│   ├── __init__.py
│   └── llm_client.py       # Клиент для Ollama API
├── styles/                 # QSS стили для UI
│   └── default.qss
├── tests/                  # Тесты
│   ├── test_database.py
│   ├── test_prompt_engineer.py
│   └── test_exporters.py
├── requirements.txt        # Зависимости Python
└── README.md              # Этот файл
```

## 🎯 Как использовать

### 1. Создание проекта
При первом запуске создайте новый проект. Проект — это отдельная папка с общей базой знаний (ChromaDB collection) и эпизодической памятью (SQLite).

### 2. Создание чатов
Внутри проекта создавайте чаты, привязанные к конкретным ролям:
- **ORCHESTRATOR** — главный координатор
- **CSO** — стратегия и развитие
- **CFO** — финансы, юнит-экономика, риски
- **CHRO** — HR, команда, культура
- **GC** — юридические вопросы
- **COO** — операционная деятельность
- **CMO** — маркетинг и продажи
- **CPO** — продукт и UX
- **BOARD** — взгляд инвесторов

### 3. Работа с промпт-инженером
1. Введите сырую идею в поле промпт-инженера
2. Выберите целевую роль (например, "Отправить в: Чат с CFO")
3. Нажмите "Сгенерировать" — промпт будет адаптирован под роль
4. При необходимости нажмите "Доработать" для улучшения
5. Отредактируйте вручную если нужно
6. Нажмите "Отправить в чат"

### 4. Экспорт результатов
- **PDF**: Экспорт текстовых отчетов и рекомендаций
- **PowerPoint**: Генерация презентаций со слайдами (title + bullets)

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OLLAMA_HOST` | URL Ollama сервера | `http://localhost:11434` |
| `MAIN_MODEL` | Основная модель для агентов | `qwen2.5:14b` |
| `ENGINEER_MODEL` | Модель для промпт-инженера | `qwen2.5:7b` |
| `DATA_DIR` | Папка для хранения данных | `./data` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

### Пример .env файла

```bash
OLLAMA_HOST=http://localhost:11434
MAIN_MODEL=qwen2.5:14b
ENGINEER_MODEL=qwen2.5:7b
DATA_DIR=./data
LOG_LEVEL=INFO
```

## 🧪 Тестирование

Запуск тестов:

```bash
pytest tests/
```

Запуск с покрытием:

```bash
pytest --cov=. tests/
```

## 🏗️ Архитектура

### Компоненты

1. **WorkspaceManager** (`database.py`)
   - Управление проектами и чатами
   - SQLite для мета-данных и сообщений
   - ChromaDB для векторного поиска

2. **PromptEngineer** (`prompt_engineer.py`)
   - Генерация промптов на основе роли
   - Доработка существующих промптов
   - Использование быстрой модели (7b)

3. **Агенты** (`agents/`)
   - 9 специализированных ролей
   - Общие системные промпты
   - Интеграция с Ollama через QThread

4. **UI** (`ui_widgets.py`)
   - PyQt6 виджеты
   - Сигналы и слоты для асинхронности
   - Анимации сворачивания/разворачивания

5. **Экспортеры** (`exporters.py`)
   - PDF (заглушка для будущей реализации)
   - PowerPoint (полная реализация на python-pptx)

### Поток данных

```
User Input → PromptEngineer → Refined Prompt → Target Agent → Ollama API → Response
                                     ↓
                              ChromaDB (Vector Search)
                                     ↓
                              SQLite (Episodic Memory)
```

## 📝 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте ветку (`git checkout -b feature/AmazingFeature`)
3. Commit изменений (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## ❓ FAQ

**Q: Почему приложение тормозит?**  
A: Убедитесь, что у вас достаточно RAM (минимум 16GB для 14B модели) и что Ollama запущен.

**Q: Как сменить модель?**  
A: Измените переменные окружения `MAIN_MODEL` и `ENGINEER_MODEL` или выберите в настройках UI.

**Q: Где хранятся данные?**  
A: В папке `./data` по умолчанию. Можно изменить через `DATA_DIR`.

**Q: Можно ли использовать другие модели?**  
A: Да, любые модели совместимые с OpenAI API. Настройте через переменные окружения.

## 📞 Контакты

Для вопросов и предложений создавайте Issues в репозитории.

---

**Open Executive** — Ваш персональный совет директоров всегда с вами.