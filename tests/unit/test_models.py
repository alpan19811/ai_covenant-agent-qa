from src.models import ExtractedCovenant, CovenantType, CovenantValidationResult, AgentResponse
import pytest

# ============================================================
# ТЕСТ 1: Позитивный сценарий — создание валидного финансового ковенанта
# ============================================================
def test_valid_financial_covenant():
    """
    Проверяем, что финансовый ковенант с пороговым значением создается успешно.
    Это "happy path" — базовый позитивный сценарий.
    """
    covenant = ExtractedCovenant(
        covenant_id="Cov-1",
        covenant_type=CovenantType.FINANCIAL,
        description="Debt/EBITDA не должен превышать 3.0x",
        threshold_value=3.0,
        metric_name="Debt/EBITDA"
    )

    # Проверяем, что объект создан и поля заполнены корректно
    assert covenant.covenant_id == "Cov-1"
    assert covenant.covenant_type == CovenantType.FINANCIAL
    assert covenant.threshold_value == 3.0
    assert covenant.metric_name == "Debt/EBITDA"


# ============================================================
# ТЕСТ 2: Негативный сценарий — финансовый ковенант БЕЗ порогового значения
# ============================================================
def test_financial_covenant_without_threshold_raises_error():
    """
    Проверяем, что наш кастомный валидатор работает:
    финансовый ковенант БЕЗ threshold_value должен вызывать ValidationError.
    """
    # pytest.raises перехватывает ожидаемое исключение.
    # Если исключение НЕ возникнет — тест упадет (что нам и нужно).
    with pytest.raises(Exception) as exc_info:
        ExtractedCovenant(
            covenant_id="Cov-Bad",
            covenant_type=CovenantType.FINANCIAL,
            description="Тест без порога",
            threshold_value=None  # ← нарушение бизнес-логики
        )

    # Дополнительно проверяем, что в тексте ошибки есть наша кастомная фраза
    assert "threshold_value не может быть пустым" in str(exc_info.value)


# ============================================================
# ТЕСТ 3: Позитивный сценарий — нефинансовый ковенант БЕЗ порогового значения
# ============================================================
def test_non_financial_covenant_without_threshold_is_valid():
    """
    Проверяем, что для нефинансового ковенанта отсутствие threshold_value — это НОРМА.
    Валидатор не должен срабатывать.
    """
    covenant = ExtractedCovenant(
        covenant_id="Cov-2",
        covenant_type=CovenantType.NON_FINANCIAL,
        description="Предоставлять отчетность ежеквартально",
        threshold_value=None,  # ← для нефинансового это допустимо
        metric_name=None
    )

    assert covenant.covenant_id == "Cov-2"
    assert covenant.covenant_type == CovenantType.NON_FINANCIAL
    assert covenant.threshold_value is None


# ============================================================
# ТЕСТ 4: Граничный сценарий — проверка Enum-валидации
# ============================================================
def test_invalid_covenant_type_raises_error():
    """
    Проверяем, что Pydantic отклоняет недопустимое значение типа ковенанта.
    Если передать строку, которой нет в Enum, должна возникнуть ошибка.
    """
    with pytest.raises(Exception):
        ExtractedCovenant(
            covenant_id="Cov-3",
            covenant_type="invalid_type",  # ← недопустимое значение
            description="Тест",
            threshold_value=None
        )


# ============================================================
# ТЕСТ 5: Проверка вложенной модели AgentResponse
# ============================================================
def test_agent_response_with_nested_validation_results():
    """
    Проверяем, что итоговый ответ агента корректно собирается
    из вложенных моделей CovenantValidationResult.
    """
    validation_result = CovenantValidationResult(
        covenant_id="Cov-1",
        status="Pass",
        actual_value=2.4,
        llm_reasoning="Фактическое значение 2.4x ниже порога 3.0x"
    )

    response = AgentResponse(
        contract_id="LOAN-2024-00158",
        validation_results=[validation_result],
        overall_status="Approved",
        summary="Ковенант соблюден"
    )

    assert response.contract_id == "LOAN-2024-00158"
    assert len(response.validation_results) == 1
    assert response.validation_results[0].status == "Pass"
    assert response.validation_results[0].actual_value == 2.4