from src.tools import get_financial_metric, check_borrower_limit, FinancialMetricResult
import pytest
from unittest.mock import MagicMock, patch
from psycopg2 import Error as Psycopg2Error


# ============================================================
# ТЕСТ 1: Позитивный сценарий — успешное получение метрики из БД
# ============================================================
def test_get_financial_metric_success(mocker):
    """
    Проверяем, что инструмент корректно извлекает метрику из БД.
    Используем mocker (pytest-mock) для подмены psycopg2.connect.
    """
    # 1. Настраиваем тестовые данные (что должна вернуть БД)
    mock_db_result = {
        "metric_name": "Debt/EBITDA",
        "actual_value": 2.4,
        "reporting_period": "2024-Q3",
        "borrower_id": "BORROWER-001"
    }

    # 2. Создаем мок-объект для курсора
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = mock_db_result  # Курсор вернет наши тестовые данные
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)  # Для работы with statement
    mock_cursor.__exit__ = MagicMock(return_value=False)

    # 3. Создаем мок-объект для соединения с БД
    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor  # Соединение вернет наш мок-курсор

    # 4. Подменяем psycopg2.connect на нашу заглушку
    # Теперь при вызове psycopg2.connect() будет возвращаться mock_connection
    mocker.patch("src.tools.psycopg2.connect", return_value=mock_connection)

    # 5. Вызываем тестируемую функцию
    result = get_financial_metric(
        borrower_id="BORROWER-001",
        metric_name="Debt/EBITDA",
        reporting_period="2024-Q3",
        db_connection_params={"host": "localhost", "port": 5432, "dbname": "test", "user": "test", "password": "test"}
    )

    # 6. Проверяем результат
    assert result is not None
    assert isinstance(result, FinancialMetricResult)
    assert result.metric_name == "Debt/EBITDA"
    assert result.actual_value == 2.4
    assert result.borrower_id == "BORROWER-001"

    # 7. Проверяем, что psycopg2.connect был вызван с правильными параметрами
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()


# ============================================================
# ТЕСТ 2: Метрика не найдена в БД
# ============================================================
def test_get_financial_metric_not_found(mocker):
    """
    Проверяем, что инструмент возвращает None, если метрика не найдена.
    """
    # Настраиваем мок: курсор вернет None (запись не найдена)
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    mocker.patch("src.tools.psycopg2.connect", return_value=mock_connection)

    # Вызываем функцию
    result = get_financial_metric(
        borrower_id="BORROWER-999",
        metric_name="Debt/EBITDA",
        reporting_period="2024-Q3",
        db_connection_params={"host": "localhost", "port": 5432, "dbname": "test", "user": "test", "password": "test"}
    )

    # Проверяем, что результат None
    assert result is None


# ============================================================
# ТЕСТ 3: Ошибка БД (например, недоступность сервера)
# ============================================================
def test_get_financial_metric_database_error(mocker):
    """
    Проверяем, что инструмент корректно обрабатывает ошибки БД.
    """
    # Настраиваем мок: psycopg2.connect выбросит исключение
    mocker.patch(
        "src.tools.psycopg2.connect",
        side_effect=Psycopg2Error("Connection refused")
    )

    # Вызываем функцию
    result = get_financial_metric(
        borrower_id="BORROWER-001",
        metric_name="Debt/EBITDA",
        reporting_period="2024-Q3",
        db_connection_params={"host": "localhost", "port": 5432, "dbname": "test", "user": "test", "password": "test"}
    )

    # Проверяем, что результат None (ошибка обработана)
    assert result is None


# ============================================================
# ТЕСТ 4: Проверка лимита заемщика — успешный сценарий
# ============================================================
def test_check_borrower_limit_success(mocker):
    """
    Проверяем, что инструмент корректно извлекает информацию о лимите.
    """
    mock_db_result = {
        "limit_type": "credit_limit",
        "limit_value": 1000000.0,
        "current_usage": 400000.0,
        "available_limit": 600000.0
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = mock_db_result
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    mocker.patch("src.tools.psycopg2.connect", return_value=mock_connection)

    result = check_borrower_limit(
        borrower_id="BORROWER-001",
        limit_type="credit_limit",
        db_connection_params={"host": "localhost", "port": 5432, "dbname": "test", "user": "test", "password": "test"}
    )

    assert result is not None
    assert result["limit_type"] == "credit_limit"
    assert result["limit_value"] == 1000000.0
    assert result["available_limit"] == 600000.0


# ============================================================
# ТЕСТ 5: Проверка лимита — лимит не найден
# ============================================================
def test_check_borrower_limit_not_found(mocker):
    """
    Проверяем, что инструмент возвращает None, если лимит не найден.
    """
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    mocker.patch("src.tools.psycopg2.connect", return_value=mock_connection)

    result = check_borrower_limit(
        borrower_id="BORROWER-999",
        limit_type="credit_limit",
        db_connection_params={"host": "localhost", "port": 5432, "dbname": "test", "user": "test", "password": "test"}
    )

    assert result is None