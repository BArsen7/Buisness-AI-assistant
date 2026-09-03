"""
core/runner.py
Мост между UI и ядром OpenExecutive.
Предоставляет простой синхронный интерфейс для вызова из PyQt6 виджетов.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    raise ImportError("Требуется установить пакет 'httpx': pip install httpx")

try:
    import chromadb
except ImportError:
    raise ImportError("Требуется установить пакет 'chromadb': pip install chromadb")

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


@dataclass
class ChatMessage:
    """Простая модель сообщения чата."""
    role: str  # 'user', 'assistant', 'system'
    content: str


def get_ollama_base_url() -> str:
    """Получает базовый URL Ollama из окружения."""
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_main_model() -> str:
    """Получает основную модель для генерации ответов."""
    return os.getenv("MAIN_MODEL", "qwen2.5:14b")


def get_fast_model() -> str:
    """Получает быструю модель для промпт-инженера."""
    return os.getenv("FAST_MODEL", "qwen2.5:7b")


def init_chroma_collection(project_id: str, persist_directory: str = None) -> chromadb.Collection:
    """
    Инициализирует или получает ChromaDB collection для проекта.
    
    Args:
        project_id: Уникальный идентификатор проекта.
        persist_directory: Директория для сохранения данных ChromaDB.
        
    Returns:
        chromadb.Collection: Коллекция для данного проекта.
    """
    if persist_directory is None:
        # По умолчанию сохраняем в папке data/chroma_db относительно скрипта
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        persist_directory = os.path.join(base_dir, "data", "chroma_db")
    
    # Создаем директорию если не существует
    os.makedirs(persist_directory, exist_ok=True)
    
    # Инициализируем постоянный клиент
    client = chromadb.PersistentClient(path=persist_directory)
    
    # Получаем или создаем коллекцию
    collection_name = f"project_{project_id}"
    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        collection = client.create_collection(name=collection_name)
    
    return collection


def generate_response(
    project_id: str,
    chat_id: str,
    agent_role: str,
    message: str,
    history: List[Dict[str, Any]] = None,
    model: str = None
) -> str:
    """
    Генерирует ответ от агента с указанной ролью.
    
    Args:
        project_id: ID проекта (для ChromaDB).
        chat_id: ID чата (для логирования/контекста).
        agent_role: Роль агента (CEO, CFO, CMO и т.д.).
        message: Текущее сообщение пользователя.
        history: История чата (список сообщений в формате {"role": "...", "content": "..."}).
        model: Название модели (по умолчанию из .env).
        
    Returns:
        str: Текстовый ответ от LLM.
        
    Raises:
        Exception: При ошибке запроса к Ollama.
    """
    if history is None:
        history = []
    
    if model is None:
        model = get_main_model()
    
    # Инициализируем ChromaDB collection (для будущего использования)
    try:
        collection = init_chroma_collection(project_id)
    except Exception as e:
        # Если ChromaDB недоступен, продолжаем без него
        print(f"Warning: ChromaDB initialization failed: {e}")
    
    # Формируем системный промпт на основе роли агента
    system_prompt = _build_system_prompt_for_role(agent_role)
    
    # Формируем сообщения для API
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Добавляем историю чата (последние 10 сообщений для контекста)
    for msg in history[-10:]:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            messages.append(msg)
    
    # Добавляем текущее сообщение
    messages.append({"role": "user", "content": message})
    
    # Делаем запрос к Ollama API
    base_url = get_ollama_base_url()
    api_endpoint = f"{base_url}/v1/chat/completions"
    
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                api_endpoint,
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Извлекаем ответ
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return "[Ошибка: пустой ответ от LLM]"
                
    except httpx.HTTPError as e:
        return f"[Ошибка HTTP запроса к Ollama: {str(e)}]"
    except Exception as e:
        return f"[Ошибка генерации ответа: {str(e)}]"


def generate_prompt_refinement(
    idea: str,
    target_role: str,
    context: str = "",
    model: str = None
) -> str:
    """
    Генерирует или уточняет промпт для заданной роли.
    Использует быструю модель для оперативной работы.
    
    Args:
        idea: Сырая идея/вопрос пользователя.
        target_role: Целевая роль агента.
        context: Дополнительный контекст (история чата и т.д.).
        model: Название модели (по умолчанию быстрая модель из .env).
        
    Returns:
        str: Сгенерированный или уточненный промпт.
    """
    if model is None:
        model = get_fast_model()
    
    # Системный промпт для промпт-инженера
    system_prompt = _build_prompt_engineer_system_prompt(target_role)
    
    # Формируем пользовательский промпт
    user_prompt = f"""Сырая идея пользователя: "{idea}"
"""
    
    if context:
        user_prompt += f"\nКонтекст диалога:\n{context}\n"
    
    user_prompt += """
Создай детализированный, структурированный промпт для ИИ-агента, который играет роль {role}.
Промпт должен:
1. Четко обозначить контекст задачи
2. Требовать ответа в рамках компетенции данной роли
3. Включать требования к формату ответа (цифры, таблицы, списки)
4. Быть конкретным и избегать двусмысленностей

Верни только готовый промпт без дополнительных комментариев.""".format(role=target_role)
    
    # Делаем запрос к Ollama API
    base_url = get_ollama_base_url()
    api_endpoint = f"{base_url}/v1/chat/completions"
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                api_endpoint,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1500,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return "[Ошибка: пустой ответ от LLM]"
                
    except httpx.HTTPError as e:
        return f"[Ошибка HTTP запроса к Ollama: {str(e)}]\n\nБазовый промпт: {idea}"
    except Exception as e:
        return f"[Ошибка генерации промпта: {str(e)}]\n\nБазовый промпт: {idea}"


def _build_system_prompt_for_role(role: str) -> str:
    """
    Формирует системный промпт для заданной роли агента.
    
    Args:
        role: Роль агента (строка).
        
    Returns:
        str: Системный промпт.
    """
    role_upper = role.upper()
    
    prompts = {
        "ORCHESTRATOR": """Ты — Главный Координатор (Orchestrator) Совета Директоров. 
Твоя задача — синтезировать мнения всех экспертов, выявлять противоречия и формировать целостную картину.
Фокус: Синтез мнений, Управление конфликтами, Стратегическое видение, Баланс интересов.
Требования к ответу: Четкая структура, выделение ключевых решений, план дальнейших действий.""",
        
        "CSO": """Ты — Chief Strategy Officer (CSO), директор по стратегии.
Твой фокус на долгосрочном планировании, конкурентном анализе и рыночных возможностях.
Фокус: Рыночный анализ, Конкурентная среда, Долгосрочные цели, Стратегические инициативы.
Требования к ответу: SWOT-анализ, конкретные стратегические шаги, оценка рисков и возможностей.""",
        
        "CFO": """Ты — Chief Financial Officer (CFO), финансовый директор.
Твой фокус на цифрах, юнит-экономике, рентабельности и финансовых рисках.
Фокус: Финансовое моделирование, Юнит-экономика, Cash flow, ROI/IRR/NPV, Бюджетирование.
Требования к ответу: Конкретные цифры и метрики, расчет окупаемости, анализ финансовых рисков, рекомендации по оптимизации затрат.""",
        
        "CHRO": """Ты — Chief Human Resources Officer (CHRO), директор по персоналу.
Твой фокус на организационной структуре, талантах, культуре компании и мотивации.
Фокус: Организационный дизайн, Подбор талантов, Корпоративная культура, Обучение и развитие.
Требования к ответу: Рекомендации по структуре команды, план развития персонала, оценка культурных рисков.""",
        
        "GC": """Ты — General Counsel (GC), главный юрист.
Твой фокус на правовом соответствии, рисках, контрактах и регуляторных требованиях.
Фокус: Правовые риски, Комплаенс, Контрактное право, Интеллектуальная собственность.
Требования к ответу: Выявление юридических рисков, рекомендации по защите, ссылки на регуляторные требования.""",
        
        "COO": """Ты — Chief Operating Officer (COO), операционный директор.
Твой фокус на процессах, эффективности, масштабировании и исполнении.
Фокус: Оптимизация процессов, KPI и метрики, Масштабирование, Управление ресурсами.
Требования к ответу: Пошаговый план реализации, метрики эффективности, выявление узких мест.""",
        
        "CMO": """Ты — Chief Marketing Officer (CMO), маркетинговый директор.
Твой фокус на позиционировании, клиентском опыте, каналах продвижения и бренде.
Фокус: Позиционирование продукта, Customer Journey, Маркетинговые каналы, Бренд-стратегия.
Требования к ответу: Маркетинговый план, анализ целевой аудитории, рекомендации по каналам продвижения.""",
        
        "CPO": """Ты — Chief Product Officer (CPO), продуктовый директор.
Твой фокус на продуктовой стратегии, roadmap, пользовательских потребностях и метриках продукта.
Фокус: Продуктовая стратегия, Product-Market Fit, User Experience, Метрики продукта (LTV, CAC, Retention).
Требования к ответу: Продуктовый roadmap, приоритизация фич, анализ пользовательских потребностей.""",
        
        "BOARD": """Ты — Представитель Инвесторов (Board Member).
Твой фокус на возврате инвестиций, оценке компании, exit-стратегии и защите интересов акционеров.
Фокус: Оценка компании, Exit-стратегия, Защита интересов акционеров, Финансовая отчетность.
Требования к ответу: Оценка инвестиционной привлекательности, вопросы к основателям, требования к отчетности."""
    }
    
    return prompts.get(role_upper, f"""Ты — эксперт-консультант в роли {role}.
Предоставь детальный, профессиональный ответ на запрос пользователя.
Включи конкретные рекомендации, анализ рисков и план действий.""")


def _build_prompt_engineer_system_prompt(target_role: str) -> str:
    """
    Формирует системный промпт для промпт-инженера.
    
    Args:
        target_role: Целевая роль агента, для которой готовится промпт.
        
    Returns:
        str: Системный промпт для промпт-инженера.
    """
    return f"""Ты — профессиональный промпт-инженер. Твоя задача — создать идеальный промпт для ИИ-агента, который играет роль: {target_role}.

Твоя цель: преобразовать сырую идею пользователя в детализированный, структурированный промпт, который заставит агента этой роли дать максимально полезный, специфичный для его компетенции ответ.

Промпт должен:
1. Четко обозначить контекст задачи
2. Требовать ответа в рамках компетенции данной роли
3. Включать требования к формату ответа (цифры, таблицы, списки и т.д.)
4. Быть конкретным и избегать двусмысленностей
5. Провоцировать глубокий, аналитический ответ

Верни только готовый промпт без дополнительных комментариев."""
