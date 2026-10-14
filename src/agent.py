from src.models import ExtractedCovenant
from typing import List, Any


class CovenantAgent:
    """
    AI-агент для извлечения кредитных ковенант из текста договора.
    """

    def __init__(self, llm_service: Any):
        self.llm_service = llm_service

    def extract(self, contract_text: str) -> List[ExtractedCovenant]:
        """
        Извлекает ковенанты из текста договора с защитой от сбоев LLM.
        """
        # 1. Вызываем LLM
        raw_llm_output = self.llm_service.generate(contract_text)

        # 2. ЗАЩИТА: Если LLM упала или вернула None/пустой список
        if not raw_llm_output:
            return []

        # 3. ЗАЩИТА: Проверка типа (LLM могла вернуть строку вместо списка)
        if not isinstance(raw_llm_output, list):
            print(f"[Agent Warning] LLM вернула некорректный формат: {type(raw_llm_output)}. Ожидался list.")
            return []

        # 4. Валидируем каждый элемент через Pydantic
        validated_covenants = []
        for item in raw_llm_output:
            # Пропускаем элементы, которые не являются словарями
            if not isinstance(item, dict):
                continue

            try:
                # Pydantic выступает нашим "санитаром": если данные бредовые, он выбросит Exception
                covenant = ExtractedCovenant(**item)
                validated_covenants.append(covenant)
            except Exception as e:
                # Логируем, но не падаем. Агент просто игнорирует невалидный ковенант.
                print(f"[Agent Warning] Validation error for covenant {item.get('covenant_id', 'unknown')}: {e}")

        return validated_covenants