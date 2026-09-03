from core.agents.base import BaseAgent
from core.config import get_settings


class FinanceAgent(BaseAgent):
    name = "cfo"
    domain = "finance"
    use_deep_reasoning = True

    @property
    def model(self) -> str:  # type: ignore[override]
        return get_settings().deep_reasoning_model

    def get_system_prompt(self) -> str:
        from core.prompts.domain_prompts import CFO_PROMPT

        return CFO_PROMPT
