# tests/evaluation/test_precision_recall.py

import pytest
import json
from pathlib import Path
from src.agent import CovenantAgent
from src.models import ExtractedCovenant


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАСЧЕТА МЕТРИК
# ============================================================

def calculate_metrics(expected_covenants: list, actual_covenants: list) -> dict:
    """
    Рассчитывает Precision, Recall и F1-score на основе covenant_id.
    """
    expected_ids = {c["covenant_id"] for c in expected_covenants}
    actual_ids = {c.covenant_id for c in actual_covenants}

    # True Positives: ID, которые есть и там, и там
    tp = len(expected_ids.intersection(actual_ids))

    # False Positives: ID, которые нашел агент, но их нет в Ground Truth (галлюцинации)
    fp = len(actual_ids - expected_ids)

    # False Negatives: ID, которые есть в Ground Truth, но агент их пропустил
    fn = len(expected_ids - actual_ids)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn
    }


# ============================================================
# ФИКСТУРЫ
# ============================================================

@pytest.fixture
def ground_truth_data():
    """Загружает эталонные данные из JSON."""
    gt_path = Path(__file__).parent.parent.parent / "data" / "ground_truth.json"
    with open(gt_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_llm_service(mocker):
    """Создает мок для LLM сервиса."""
    mock_service = mocker.MagicMock()
    return mock_service


# ============================================================
# ТЕСТ 1: Идеальный сценарий (Агент работает безупречно)
# ============================================================

def test_agent_perfect_extraction(ground_truth_data, mock_llm_service):
    """
    Сценарий: LLM возвращает идеально точные данные, совпадающие с Ground Truth.
    Ожидание: Precision = 1.0, Recall = 1.0
    """
    # Настраиваем мок: LLM возвращает точную копию expected_covenants
    mock_llm_service.generate.return_value = ground_truth_data["expected_covenants"]

    agent = CovenantAgent(llm_service=mock_llm_service)

    # Запускаем агента
    actual_covenants = agent.extract("Текст договора LOAN-2024-00158...")

    # Считаем метрики
    metrics = calculate_metrics(
        ground_truth_data["expected_covenants"],
        actual_covenants
    )

    # Проверяем, что метрики идеальны
    assert metrics["precision"] == 1.0, f"Precision should be 1.0, got {metrics['precision']}"
    assert metrics["recall"] == 1.0, f"Recall should be 1.0, got {metrics['recall']}"
    assert metrics["f1"] == 1.0
    assert len(actual_covenants) == 2


# ============================================================
# ТЕСТ 2: Сценарий с галлюцинациями (False Positives)
# ============================================================

def test_agent_with_hallucinations(ground_truth_data, mock_llm_service):
    """
    Сценарий: LLM находит правильные ковенанты, но ВЫДУМЫВАЕТ один лишний (галлюцинация).
    Ожидание: Recall = 1.0 (все нужные найдены), но Precision < 1.0 (есть мусор).
    """
    # Копируем эталон и добавляем выдуманный ковенант
    hallucinated_output = ground_truth_data["expected_covenants"].copy()
    hallucinated_output.append({
        "covenant_id": "Cov-Fake-99",  # Такого нет в Ground Truth!
        "covenant_type": "financial",
        "description": "Выдуманный ковенант про ликвидность",
        "threshold_value": 1.5,
        "metric_name": "Current Ratio"
    })

    mock_llm_service.generate.return_value = hallucinated_output
    agent = CovenantAgent(llm_service=mock_llm_service)

    actual_covenants = agent.extract("Текст договора...")
    metrics = calculate_metrics(ground_truth_data["expected_covenants"], actual_covenants)

    # Recall должен быть 1.0 (мы нашли все 2 реальных ковенанта: TP=2, FN=0)
    assert metrics["recall"] == 1.0
    # Precision должен быть 2/3 = 0.666... (TP=2, FP=1)
    assert metrics["precision"] == pytest.approx(0.666, rel=1e-2)
    assert metrics["fp"] == 1


# ============================================================
# ТЕСТ 3: Сценарий с пропусками (False Negatives)
# ============================================================

def test_agent_with_missed_covenants(ground_truth_data, mock_llm_service):
    """
    Сценарий: LLM находит только один ковенант из двух (пропускает Cov-2).
    Ожидание: Precision = 1.0 (мусора нет), но Recall < 1.0 (что-то пропустили).
    """
    # Возвращаем только первый ковенант
    missed_output = [ground_truth_data["expected_covenants"][0]]

    mock_llm_service.generate.return_value = missed_output
    agent = CovenantAgent(llm_service=mock_llm_service)

    actual_covenants = agent.extract("Текст договора...")
    metrics = calculate_metrics(ground_truth_data["expected_covenants"], actual_covenants)

    # Precision = 1.0 (TP=1, FP=0)
    assert metrics["precision"] == 1.0
    # Recall = 0.5 (TP=1, FN=1 - пропустили Cov-2)
    assert metrics["recall"] == 0.5
    assert metrics["fn"] == 1