import pytest
from src.agent import CovenantAgent


@pytest.fixture
def mock_llm_service(mocker):
    mock_service = mocker.MagicMock()
    return mock_service


def test_agent_handles_empty_contract_text(mock_llm_service):
    """
    Сценарий: На вход подается текст без ковенантов. LLM возвращает пустой список.
    Ожидание: Агент не падает, возвращает пустой список.
    """
    mock_llm_service.generate.return_value = []
    agent = CovenantAgent(llm_service=mock_llm_service)

    result = agent.extract("Просто случайный текст без финансовых терминов.")

    assert result == []
    assert len(result) == 0


def test_agent_handles_none_llm_response(mock_llm_service):
    """
    Сценарий: LLM упала (таймаут, OOM) и вернула None.
    Ожидание: Агент gracefully возвращает пустой список, а не падает с TypeError.
    """
    mock_llm_service.generate.return_value = None
    agent = CovenantAgent(llm_service=mock_llm_service)

    result = agent.extract("Текст договора...")
    assert result == []


def test_agent_ignores_out_of_domain_input(mock_llm_service):
    """
    Сценарий (Out-of-Domain): На вход подан рецепт.
    Ожидание: LLM не должна выдумывать финансовые ковенанты из рецепта.
    Мы мокаем "правильную" LLM, которая вернула пустоту.
    """
    mock_llm_service.generate.return_value = []
    agent = CovenantAgent(llm_service=mock_llm_service)

    recipe = "Возьмите свеклу, капусту, картофель. Нарежьте кубиками..."
    result = agent.extract(recipe)

    assert result == []