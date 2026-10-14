# 1. Импорт необходимых компонентов из библиотеки Pydantic и стандартной библиотеки Python
from pydantic import BaseModel, Field, field_validator, ValidationError, ValidationInfo
from typing import List, Optional
from enum import Enum


# 2. Определение перечисления (Enum) для типов ковенант.
# Использование Enum вместо обычных строк предотвращает опечатки и ограничивает модель только допустимыми значениями, что критично для валидации.
class CovenantType(str, Enum):
    FINANCIAL = "financial"  # Финансовый ковенант (например, Debt/EBITDA < 3.0)
    NON_FINANCIAL = "non_financial"  # Нефинансовый (например, предоставление отчетности в срок)
    INFORMATIONAL = "informational"  # Информационный


# 3. Модель для описания ОДНОГО извлеченного ковенанта.
# Наследуемся от BaseModel, чтобы получить возможности валидации и сериализации Pydantic.
class ExtractedCovenant(BaseModel):
    covenant_id: str = Field(..., description="Уникальный идентификатор ковенанта из договора (например, 'Cov-1')") # Field используется для добавления метаданных.
    covenant_type: CovenantType = Field(..., description="Тип ковенанта: financial, non_financial или informational") # Description помогает самой LLM понять, что от нее ожидают (при использовании structured output)
    description: str = Field(..., description="Полное текстовое описание условия ковенанта из договора") #  Examples дают модели подсказку о формате.

    # Optional означает, что поле может быть None (например, для нефинансовых ковенант пороговое значение не нужно)
    threshold_value: Optional[float] = Field(None,
                                             description="Числовое пороговое значение (например, 3.0 для Debt/EBITDA < 3.0)")

    metric_name: Optional[str] = Field(None, description="Название финансовой метрики (например, 'Debt/EBITDA')")

    # 4. Кастомный валидатор уровня поля (Field Validator). Он срабатывает ДО создания объекта. Проверяет логическую целостность данных.
    @field_validator('threshold_value')
    @classmethod
    def check_threshold_logic(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        # Если тип ковенанта финансовый, пороговое значение ОБЯЗАТЕЛЬНО должно быть указано
        # info.data содержит все ранее валидированные поля
        if info.data.get('covenant_type') == CovenantType.FINANCIAL and v is None:
            raise ValueError("Для финансового ковенанта (financial) поле threshold_value не может быть пустым")
        return v


# 5. Модель результата проверки (валидации) одного ковенанта агентом.
class CovenantValidationResult(BaseModel):
    covenant_id: str = Field(..., description="ID ковенанта, который проверяется")

    # Ограничиваем статус только тремя возможными строковыми значениями через Literal (или Enum, здесь для простоты str с описанием)
    status: str = Field(...,
                        description="Результат проверки: 'Pass' (соблюден), 'Fail' (нарушен), 'Warning' (риск нарушения)")

    actual_value: Optional[float] = Field(None,
                                          description="Фактическое значение метрики, полученное из БД или расчетов")

    # Поле для Chain-of-Thought (цепочки рассуждений).
    # В AI-тестировании важно проверять не только итоговый ответ, но и логику, к нему приведшую.
    llm_reasoning: str = Field(..., description="Обоснование решения, сгенерированное LLM")


# 6. Итоговая модель ответа всего AI-агента.
class AgentResponse(BaseModel):
    contract_id: str = Field(..., description="Идентификатор проверенного кредитного договора")

    # Список результатов валидации. По умолчанию пустой список, если ковенанты не найдены.
    validation_results: List[CovenantValidationResult] = Field(default_factory=list)

    overall_status: str = Field(..., description="Общий статус по договору: 'Approved', 'Rejected', 'Manual Review'")

    summary: str = Field(..., description="Краткая сводка для кредитного аналитика на естественном языке")

