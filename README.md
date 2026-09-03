# Open Executive — Локальный виртуальный совет директоров

Десктопное AI-приложение для принятия стратегических решений с помощью мультиагентной системы из 9 ролей (CFO, CMO, COO, CEO и др.). Работает полностью локально на вашем компьютере без отправки данных в облако.

## 🚀 Особенности

- **Мультиагентная архитектура**: 9 специализированных ролей (Orchestrator, CSO, CFO, CHRO, GC, COO, CMO, CPO, Board)
- **Полная приватность**: Все данные хранятся локально (SQLite + ChromaDB)
- **Локальные LLM**: Интеграция с Ollama (модели qwen2.5:14b и qwen2.5:7b)
- **Умный промпт-инженер**: Автоматическая генерация и доработка промптов под конкретную роль
- **Экспорт артефактов**: Выгрузка результатов в PDF и PowerPoint (PPTX)
- **Нативный UI**: PyQt6 с современной стилизацией (QSS)
- **Асинхронность**: Все LLM-запросы выполняются в отдельных потоках (QThread), интерфейс не зависает
- **Готовность к сборке**: PyInstaller скрипт для создания одного исполняемого файла (.exe для Windows, бинарник для Linux)

---

## 📋 Требования

### Обязательные
- **Python 3.9+** (рекомендуется 3.10 или 3.11)
- **Ollama** (установленный локально)
- **Модели Ollama**: `qwen2.5:14b` и `qwen2.5:7b`
- **ОЗУ**: минимум 16 GB (для комфортной работы с 14B моделью)
- **Свободное место**: ~10 GB (для моделей и данных)

### Опциональные (для разработки)
- Git (для клонирования репозитория)
- Virtualenv или venv (для изоляции зависимостей)

---

## 🛠️ Установка

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/BArsen7/Buisness-AI-assistant.git
cd Buisness-AI-assistant
```

### Шаг 2: Создание виртуального окружения

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Шаг 3: Установка зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 4: Установка и настройка Ollama

#### Установка Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
# или скачайте с https://ollama.com
```

**Windows:**
1. Скачайте установщик с [ollama.com](https://ollama.com)
2. Запустите установщик и следуйте инструкциям

#### Запуск Ollama сервера

В отдельном терминале запустите:
```bash
ollama serve
```

> **Примечание:** По умолчанию Ollama запускается на `http://localhost:11434`

#### Загрузка необходимых моделей

```bash
ollama pull qwen2.5:14b
ollama pull qwen2.5:7b
```

Проверка работы:
```bash
ollama run qwen2.5:7b "Привет! Как дела?"
```

---

## ⚙️ Конфигурация

### Переменные окружения

Создайте файл `.env` в корне проекта (или используйте переменные окружения вашей ОС):

```bash
# URL Ollama сервера
OLLAMA_BASE_URL=http://localhost:11434

# Основная модель для агентов (требует больше ресурсов)
MAIN_MODEL=qwen2.5:14b

# Быстрая модель для промпт-инженера (меньше ресурсов)
FAST_MODEL=qwen2.5:7b

# Директория для хранения данных (ChromaDB, SQLite)
DATA_DIR=./data

# Уровень логирования: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OLLAMA_BASE_URL` | URL Ollama сервера | `http://localhost:11434` |
| `MAIN_MODEL` | Основная модель для агентов | `qwen2.5:14b` |
| `FAST_MODEL` | Модель для промпт-инженера | `qwen2.5:7b` |
| `DATA_DIR` | Папка для хранения данных | `./data` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

> **Важно:** При запуске скомпилированного приложения данные сохраняются в `~/.openexecutive/` (домашняя директория пользователя) для надежности.

---

## 🚀 Запуск приложения

### Основной запуск

Убедитесь, что Ollama запущен (`ollama serve` в отдельном терминале), затем:

```bash
python main.py
```

### Запуск с указанием порта Ollama (если нестандартный)

```bash
OLLAMA_BASE_URL=http://localhost:11435 python main.py
```

### Запуск в режиме разработки (с подробным логированием)

```bash
LOG_LEVEL=DEBUG python main.py
```

---

## 📦 Сборка в один исполняемый файл

Приложение можно скомпилировать в один файл (.exe для Windows, бинарник для Linux) с помощью PyInstaller.

### Для Windows

```bash
# Активируйте виртуальное окружение
venv\Scripts\activate

# Запустите сборку с флагом --windowed (скрывает консоль)
python build.py --windowed
```

После сборки исполняемый файл появится в папке `dist/OpenExecutive.exe`.

### Для Linux

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Запустите сборку (консоль остается видимой)
python build.py
```

После сборки исполняемый файл появится в папке `dist/OpenExecutive`.

### Что включает сборка

Скрипт `build.py` автоматически:
- Добавляет все необходимые скрытые импорты (PyQt6, chromadb, httpx и др.)
- Включает файл `.env` если он существует
- Создает пустую структуру папок `data/` для ChromaDB и SQLite
- Использует флаги `--onefile --clean --noconfirm`

> **Примечание:** Размер собранного файла составит ~150-250 MB в зависимости от платформы.

---

## 🎯 Как использовать

### 1. Первый запуск

При первом запуске приложение:
- Создаст директории `data/chroma_db` и `data/sqlite` для хранения данных
- Инициализирует базу данных и векторное хранилище
- Покажет главное окно с виджетом Промпт-Инженера

### 2. Работа с Промпт-Инженером

1. **Выберите целевой чат** из выпадающего списка (например, "Чат с CFO")
2. **Выберите целевую роль** агента (CEO, CFO, CMO и т.д.)
3. **Введите сырую идею** в поле ввода (например: "Нужно проанализировать финансовые риски выхода на рынок Азии")
4. **Нажмите "✨ Сгенерировать промпт"** — промпт будет адаптирован под выбранную роль
5. **При необходимости нажмите "🔄 Доработать"** для улучшения промпта
6. **Отредактируйте вручную** если нужно (поле редактируемое)
7. **Нажмите "📤 Отправить в чат"** — запрос будет отправлен агенту

### 3. Получение ответа

- После отправки промпта в статус-баре появится сообщение "🤖 Агент [РОЛЬ] печатает..."
- Через несколько секунд (зависит от модели и запроса) ответ будет получен
- Ответ показывается в информационном окне (QMessageBox)
- История чата сохраняется в базе данных

### 4. Экспорт результатов

Для экспорта результатов диалога:

**Экспорт в PDF:**
```python
from exporters import export_to_pdf

markdown_text = "# Отчет\n\nТекст ответа..."
export_to_pdf(markdown_text, "output/report.pdf")
```

**Экспорт в PowerPoint:**
```python
from exporters import export_to_pptx, export_markdown_to_structured_slides

markdown_text = "# Стратегия\n\n## Цели\n- Цель 1\n- Цель 2"
slides = export_markdown_to_structured_slides(markdown_text)
export_to_pptx(slides, "output/presentation.pptx")
```

> **Примечание:** В текущей версии экспорт в PDF сохраняет текст как Markdown-файл. Для полноценной конвертации в PDF рекомендуется установить дополнительные зависимости (weasyprint, pandoc).

---

## 📁 Структура проекта

```
Buisness-AI-assistant/
├── main.py                 # Точка входа в приложение
├── build.py                # Скрипт сборки PyInstaller
├── requirements.txt        # Зависимости Python
├── .env                    # Переменные окружения (создать вручную)
│
├── core/                   # Ядро OpenExecutive (интегрировано)
│   ├── runner.py           # Мост между UI и LLM (generate_response, generate_prompt_refinement)
│   ├── agents/             # Базовые классы агентов
│   ├── memory/             # Модули памяти
│   ├── prompts/            # Системные промпты
│   └── orchestrator/       # Координация агентов (router.py)
│
├── ui/                     # UI модули
│   └── worker.py           # Асинхронные QThread воркеры (ChatWorker, PromptWorker)
│
├── ui_widgets.py           # PyQt6 виджеты (PromptEngineerWidget, CollapsiblePanel и др.)
├── database.py             # WorkspaceManager: SQLite + ChromaDB
├── exporters.py            # Экспорт в PDF и PowerPoint
├── models.py               # Модели данных (AgentRole, Chat и др.)
│
├── data/                   # Данные приложения (создается автоматически)
│   ├── chroma_db/          # Векторное хранилище ChromaDB
│   └── sqlite/             # Эпизодическая память SQLite
│
└── dist/                   # Скомпилированные файлы (после сборки)
    └── OpenExecutive[.exe] # Исполняемый файл
```

---

## 🏗️ Архитектура

### Компоненты

1. **core/runner.py** — Мост между UI и LLM
   - `generate_response()` — прямой HTTP-запрос к Ollama API
   - `generate_prompt_refinement()` — генерация промптов через быструю модель
   - `init_chroma_collection()` — инициализация векторного хранилища

2. **ui/worker.py** — Асинхронные воркеры
   - `ChatWorker` — выполняет `generate_response` в отдельном потоке
   - `PromptWorker` — выполняет `generate_prompt_refinement` в отдельном потоке
   - Оба воркера эмитят сигналы `finished` и `error`

3. **ui_widgets.py** — PyQt6 виджеты
   - `PromptEngineerWidget` — основной виджет промпт-инженера
   - `CollapsiblePanel` — сворачиваемая панель с анимацией
   - `ChatMessageBubble` — пузыри сообщений чата

4. **database.py** — Управление данными
   - SQLite для мета-данных и истории чатов
   - ChromaDB для векторного поиска и контекста

5. **exporters.py** — Экспорт артефактов
   - `export_to_pdf()` — экспорт в PDF (placeholder)
   - `export_to_pptx()` — генерация PowerPoint презентаций
   - `export_markdown_to_structured_slides()` — конвертация MD в слайды

### Поток данных

```
User Input → PromptEngineerWidget → PromptWorker → generate_prompt_refinement() → Ollama API
                                                                                ↓
                                                                          Refined Prompt
                                                                                ↓
User Clicks Send → ChatWorker → generate_response() → Ollama API → Response → QMessageBox
                                     ↓
                              ChromaDB (Vector Search)
                                     ↓
                              SQLite (Episodic Memory)
```

---

## 🧪 Тестирование

Запуск тестов (если доступны):

```bash
pytest tests/
```

Запуск с покрытием:

```bash
pytest --cov=. tests/
```

Тестирование воркеров:

```bash
# Тест ChatWorker
python -m ui.worker

# Тест экспортеров
python exporters.py
```

---

## ❓ FAQ

**Q: Почему приложение тормозит?**  
A: Убедитесь, что у вас достаточно ОЗУ (минимум 16GB для 14B модели) и что Ollama запущен. Проверьте загрузку CPU/GPU во время генерации.

**Q: Как сменить модель?**  
A: Измените переменные окружения `MAIN_MODEL` и `FAST_MODEL` в файле `.env` или через экспортирование перед запуском.

**Q: Где хранятся данные?**  
A: По умолчанию в папке `./data` относительно приложения. При запуске скомпилированного файла данные сохраняются в `~/.openexecutive/` (домашняя директория пользователя).

**Q: Можно ли использовать другие модели?**  
A: Да, любые модели совместимые с OpenAI API через Ollama. Настройте через переменные окружения `OLLAMA_BASE_URL`, `MAIN_MODEL`, `FAST_MODEL`.

**Q: Как добавить новую роль агента?**  
A: Добавьте новую роль в `models.py` (класс `AgentRole`) и соответствующий системный промпт в `core/runner.py` (функция `_build_system_prompt_for_role`).

**Q: Приложение выдает ошибку "Connection refused" при запуске.**  
A: Убедитесь, что Ollama запущен командой `ollama serve` в отдельном терминале. Проверьте, что порт 11434 не занят другими приложениями.

---

## 🔧 Разработка

### Добавление новых функций

1. Создайте новый виджет в `ui_widgets.py` или отдельном файле в `ui/`
2. При необходимости создайте новый воркер в `ui/worker.py`
3. Добавьте функцию в `core/runner.py` для взаимодействия с LLM
4. Подключите виджет в `main.py`

### Стилизация UI

Стили определяются через QSS (Qt Style Sheets) непосредственно в виджетах. Пример:

```python
self.setStyleSheet("""
    QPushButton {
        background-color: #4a90d9;
        color: white;
        border-radius: 5px;
        padding: 8px 16px;
    }
    QPushButton:hover {
        background-color: #3a7bc8;
    }
""")
```

### Логирование

Используйте стандартный модуль `logging`:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Сообщение")
logger.debug("Отладочная информация")
logger.error("Ошибка")
```

---

## 📝 Лицензия

MIT License

---

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте ветку (`git checkout -b feature/AmazingFeature`)
3. Commit изменений (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

---

## 📞 Контакты

Для вопросов и предложений создавайте Issues в репозитории.

---

**Open Executive** — Ваш персональный совет директоров всегда с вами. 🎯