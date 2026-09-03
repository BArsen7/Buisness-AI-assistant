"""
prompt_engineer.py
Модуль промпт-инженерии для проекта Open Executive.
Использует быструю модель (qwen2.5:7b) для генерации и уточнения промптов
с учетом специфики ролей агентов.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Импорты для работы с LLM (Ollama через OpenAI-compatible API)
try:
    from openai import OpenAI
except ImportError:
    # Заглушка если openai не установлен
    OpenAI = None

from models import AgentRole, PromptRequest


@dataclass
class RolePromptTemplate:
    """Шаблон системного промпта для каждой роли."""
    role_name: str
    description: str
    focus_areas: List[str]
    output_requirements: List[str]


# Конфигурация промптов для каждой роли агента
ROLE_TEMPLATES: Dict[AgentRole, RolePromptTemplate] = {
    AgentRole.ORCHESTRATOR: RolePromptTemplate(
        role_name="Главный Координатор (Orchestrator)",
        description="Вы — центральный координатор Совета Директоров. Ваша задача — синтезировать мнения всех экспертов, выявлять противоречия и формировать целостную картину.",
        focus_areas=["Синтез мнений", "Управление конфликтами", "Стратегическое видение", "Баланс интересов"],
        output_requirements=["Четкая структура ответа", "Выделение ключевых решений", "План дальнейших действий"]
    ),
    AgentRole.CSO: RolePromptTemplate(
        role_name="Chief Strategy Officer (CSO)",
        description="Вы — директор по стратегии. Ваш фокус на долгосрочном планировании, конкурентном анализе и рыночных возможностях.",
        focus_areas=["Рыночный анализ", "Конкурентная среда", "Долгосрочные цели", "Стратегические инициативы"],
        output_requirements=["SWOT-анализ", "Конкретные стратегические шаги", "Оценка рисков и возможностей"]
    ),
    AgentRole.CFO: RolePromptTemplate(
        role_name="Chief Financial Officer (CFO)",
        description="Вы — финансовый директор. Ваш фокус на цифрах, юнит-экономике, рентабельности и финансовых рисках.",
        focus_areas=["Финансовое моделирование", "Юнит-экономика", "Cash flow", "ROI/IRR/NPV", "Бюджетирование"],
        output_requirements=["Конкретные цифры и метрики", "Расчет окупаемости", "Анализ финансовых рисков", "Рекомендации по оптимизации затрат"]
    ),
    AgentRole.CHRO: RolePromptTemplate(
        role_name="Chief Human Resources Officer (CHRO)",
        description="Вы — директор по персоналу. Ваш фокус на организационной структуре, талантах, культуре компании и мотивации.",
        focus_areas=["Организационный дизайн", "Подбор талантов", "Корпоративная культура", "Обучение и развитие"],
        output_requirements=["Рекомендации по структуре команды", "План развития персонала", "Оценка культурных рисков"]
    ),
    AgentRole.GC: RolePromptTemplate(
        role_name="General Counsel (GC)",
        description="Вы — главный юрист. Ваш фокус на правовом соответствии, рисках, контрактах и регуляторных требованиях.",
        focus_areas=["Правовые риски", "Комплаенс", "Контрактное право", "Интеллектуальная собственность"],
        output_requirements=["Выявление юридических рисков", "Рекомендации по защите", "Ссылки на регуляторные требования"]
    ),
    AgentRole.COO: RolePromptTemplate(
        role_name="Chief Operating Officer (COO)",
        description="Вы — операционный директор. Ваш фокус на процессах, эффективности, масштабировании и исполнении.",
        focus_areas=["Оптимизация процессов", "KPI и метрики", "Масштабирование", "Управление ресурсами"],
        output_requirements=["Пошаговый план реализации", "Метрики эффективности", "Выявление узких мест"]
    ),
    AgentRole.CMO: RolePromptTemplate(
        role_name="Chief Marketing Officer (CMO)",
        description="Вы — маркетинговый директор. Ваш фокус на позиционировании, клиентском опыте, каналах продвижения и бренде.",
        focus_areas=["Позиционирование продукта", "Customer Journey", "Маркетинговые каналы", "Бренд-стратегия"],
        output_requirements=["Маркетинговый план", "Анализ целевой аудитории", "Рекомендации по каналам продвижения"]
    ),
    AgentRole.CPO: RolePromptTemplate(
        role_name="Chief Product Officer (CPO)",
        description="Вы — продуктовый директор. Ваш фокус на продуктовой стратегии, roadmap, пользовательских потребностях и метриках продукта.",
        focus_areas=["Продуктовая стратегия", "Product-Market Fit", "User Experience", "Метрики продукта (LTV, CAC, Retention)"],
        output_requirements=["Продуктовый roadmap", "Приоритизация фич", "Анализ пользовательских потребностей"]
    ),
    AgentRole.BOARD: RolePromptTemplate(
        role_name="Представитель Инвесторов (Board)",
        description="Вы — представитель совета инвесторов. Ваш фокус на возврате инвестиций, оценке компании, exit-стратегии и защите интересов акционеров.",
        focus_areas=["Оценка компании", "Exit-стратегия", "Защита интересов акционеров", "Финансовая отчетность"],
        output_requirements=["Оценка инвестиционной привлекательности", "Вопросы к основателям", "Требования к отчетности"]
    )
}


class PromptEngineer:
    """
    Промпт-инженер для генерации и уточнения промптов.
    Использует быструю модель qwen2.5:7b через Ollama API.
    
    Атрибуты:
        client (OpenAI): Клиент для работы с Ollama API.
        model_name (str): Название модели для промпт-инженера.
    """

    def __init__(self, ollama_base_url: str = "http://localhost:11434/v1"):
        """
        Инициализация промпт-инженера.
        
        Args:
            ollama_base_url: URL базового эндпоинта Ollama API.
        """
        if OpenAI is None:
            raise ImportError("Требуется установить пакет 'openai': pip install openai")
            
        self.client = OpenAI(
            base_url=ollama_base_url,
            api_key="ollama"  # Ollama не требует реального API key
        )
        self.model_name = "qwen2.5:7b"

    def _build_system_prompt(self, target_role: AgentRole) -> str:
        """
        Формирует системный промпт для промпт-инженера с учетом целевой роли.
        
        Args:
            target_role: Целевая роль агента, для которой готовится промпт.
            
        Returns:
            str: Системный промпт.
        """
        template = ROLE_TEMPLATES[target_role]
        
        focus_str = ", ".join(template.focus_areas)
        requirements_str = "\n".join([f"- {req}" for req in template.output_requirements])
        
        return f"""Ты — профессиональный промпт-инженер. Твоя задача — создать идеальный промпт для ИИ-агента, который играет роль: {template.role_name}.

Описание роли: {template.description}

Ключевые области фокуса этой роли: {focus_str}

Требования к выходным данным от этой роли:
{requirements_str}

Твоя цель: преобразовать сырую идею пользователя в детализированный, структурированный промпт, который заставит агента этой роли дать максимально полезный, специфичный для его компетенции ответ.

Промпт должен:
1. Четко обозначить контекст задачи
2. Требовать ответа в рамках компетенции данной роли
3. Включать требования к формату ответа (цифры, таблицы, списки и т.д.)
4. Быть конкретным и избегать двусмысленностей"""

    def generate_prompt(self, user_idea: str, chat_context: List[Dict[str, Any]], target_agent_role: AgentRole) -> str:
        """
        Генерирует промпт на основе сырой идеи пользователя.
        
        Args:
            user_idea: Сырая идея/вопрос пользователя.
            chat_context: История чата (список сообщений в формате {"role": "...", "content": "..."}).
            target_agent_role: Роль целевого агента, для которого готовится промпт.
            
        Returns:
            str: Сгенерированный промпт.
        """
        system_prompt = self._build_system_prompt(target_agent_role)
        
        # Формируем контекст чата
        context_str = ""
        if chat_context:
            context_messages = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in chat_context[-5:]  # Берем последние 5 сообщений для контекста
            ])
            context_str = f"\n\nКонтекст текущего диалога:\n{context_messages}"
        
        user_prompt = f"""Сырая идея пользователя: "{user_idea}"
{context_str}

Создай детализированный промпт для агента роли '{target_agent_role.value}', который поможет получить максимально качественный и релевантный ответ."""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback: возвращаем базовый промпт если API недоступен
            return f"[Ошибка генерации промпта: {e}]\n\nБазовый промпт для {target_agent_role.value}: {user_idea}"

    def refine_prompt(self, current_prompt: str, chat_context: List[Dict[str, Any]]) -> str:
        """
        Уточняет и улучшает существующий промпт.
        
        Args:
            current_prompt: Текущий вариант промпта.
            chat_context: История чата для контекста.
            
        Returns:
            str: Улучшенный промпт.
        """
        system_prompt = """Ты — профессиональный редактор промптов. Твоя задача — улучшить существующий промпт, сделав его более четким, конкретным и эффективным.

Критерии улучшения:
1. Устранить двусмысленности
2. Добавить конкретику и детали
3. Улучшить структуру
4. Добавить требования к формату ответа
5. Убедиться что промпт провоцирует глубокий, аналитический ответ"""

        context_str = ""
        if chat_context:
            context_messages = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in chat_context[-3:]
            ])
            context_str = f"\nКонтекст диалога:\n{context_messages}"

        user_prompt = f"""Текущий промпт:
{current_prompt}
{context_str}

Улучши этот промпт согласно критериям выше. Верни только улучшенную версию промпта без дополнительных комментариев."""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[Ошибка уточнения промпта: {e}]\n\nОригинальный промпт: {current_prompt}"

    def extract_role_from_context(self, chat_context: List[Dict[str, Any]]) -> Optional[AgentRole]:
        """
        Пытается определить целевую роль агента из контекста чата.
        
        Args:
            chat_context: История чата.
            
        Returns:
            Optional[AgentRole]: Определенная роль или None.
        """
        # Простая эвристика: ищем упоминания ролей в последних сообщениях
        if not chat_context:
            return None
            
        recent_text = " ".join([
            msg.get('content', '') 
            for msg in chat_context[-3:]
        ]).upper()
        
        for role in AgentRole:
            if role.value in recent_text or role.name in recent_text:
                return role
        
        return None
