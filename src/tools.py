import psycopg2 # для работы с PostgreSQL
from psycopg2.extras import RealDictCursor  # RealDictCursor возвращает результаты как словари (dict), а не кортежи
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


# Модель для результата запроса к БД (структурированный ответ)
class FinancialMetricResult(BaseModel):
    """Результат запроса финансовой метрики из БД"""
    metric_name: str = Field(..., description="Название метрики (например, 'Debt/EBITDA')")
    actual_value: float = Field(..., description="Фактическое значение метрики")
    reporting_period: str = Field(..., description="Отчетный период (например, '2024-Q3')")
    borrower_id: str = Field(..., description="ID заемщика")


# Инструмент 1: Получение финансовой метрики из БД
def get_financial_metric(
        borrower_id: str,
        metric_name: str,
        reporting_period: str,
        db_connection_params: Dict[str, Any]
) -> Optional[FinancialMetricResult]:
    """
    Инструмент агента: извлекает значение финансовой метрики из БД PostgreSQL.

    Args:
        borrower_id: ID заемщика
        metric_name: Название метрики (например, 'Debt/EBITDA')
        reporting_period: Отчетный период (например, '2024-Q3')
        db_connection_params: Параметры подключения к БД (host, port, dbname, user, password)

    Returns:
        FinancialMetricResult если метрика найдена, иначе None
    """
    try:
        # Устанавливаем соединение с БД
        connection = psycopg2.connect(**db_connection_params)

        # Создаем курсор с RealDictCursor для получения результатов в виде словарей
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # SQL-запрос для получения метрики
            query = """
                SELECT metric_name, actual_value, reporting_period, borrower_id
                FROM financial_metrics
                WHERE borrower_id = %s 
                  AND metric_name = %s 
                  AND reporting_period = %s
                LIMIT 1
            """

            # Выполняем запрос с параметрами (защита от SQL-инъекций через %s)
            cursor.execute(query, (borrower_id, metric_name, reporting_period))

            # Получаем одну запись
            result = cursor.fetchone()

            # Если запись найдена, преобразуем в модель Pydantic
            if result:
                return FinancialMetricResult(**result)

            # Если метрика не найдена, возвращаем None
            return None

    except psycopg2.Error as e:
        # Логируем ошибку БД (в реальном проекте используем logging)
        print(f"Database error: {e}")
        return None

    finally:
        # Гарантированно закрываем соединение, даже если произошла ошибка
        if 'connection' in locals() and connection:
            connection.close()


# Инструмент 2: Проверка лимита заемщика
def check_borrower_limit(
        borrower_id: str,
        limit_type: str,
        db_connection_params: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Инструмент агента: проверяет лимит заемщика (например, максимальная сумма кредита).

    Args:
        borrower_id: ID заемщика
        limit_type: Тип лимита (например, 'credit_limit', 'exposure_limit')
        db_connection_params: Параметры подключения к БД

    Returns:
        Словарь с информацией о лимите, если найден, иначе None
    """
    try:
        connection = psycopg2.connect(**db_connection_params)

        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT borrower_id, limit_type, limit_value, current_usage, available_limit
                FROM borrower_limits
                WHERE borrower_id = %s AND limit_type = %s
                LIMIT 1
            """

            cursor.execute(query, (borrower_id, limit_type))
            result = cursor.fetchone()

            if result:
                # Возвращаем как словарь (можно преобразовать в Pydantic модель при необходимости)
                return dict(result)

            return None

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None

    finally:
        if 'connection' in locals() and connection:
            connection.close()