import pytest
from testcontainers.postgres import PostgresContainer
import psycopg2
from psycopg2.extras import RealDictCursor

from src.tools import get_financial_metric, check_borrower_limit


# ============================================================
# ФИКСТУРА: Создание и уничтожение контейнера с PostgreSQL
# ============================================================
@pytest.fixture(scope="module")
def postgres_container():
    """
    Фикстура pytest, которая создаёт Docker-контейнер с PostgreSQL.

    scope="module" означает, что контейнер создаётся ОДИН РАЗ для всех тестов в этом модуле.
    Это экономит время (не нужно запускать контейнер для каждого теста).
    """
    # Создаём контейнер с PostgreSQL
    # image="postgres:16" — используем PostgreSQL версии 16
    with PostgresContainer("postgres:16") as postgres:
        # Получаем параметры подключения к контейнеру
        # testcontainers автоматически выбирает случайный свободный порт
        connection_params = {
            "host": postgres.get_container_host_ip(),
            "port": int(postgres.get_exposed_port(5432)),
            "dbname": postgres.dbname,
            "user": postgres.username,
            "password": postgres.password
        }

        # Инициализируем схему БД (создаём таблицы)
        init_test_schema(connection_params)

        # Заполняем тестовыми данными
        insert_test_data(connection_params)

        # Возвращаем параметры подключения в тесты
        yield connection_params

        # После завершения всех тестов контейнер автоматически уничтожается
        # (благодаря контекстному менеджеру with)


# ============================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: Инициализация схемы БД
# ============================================================
def init_test_schema(connection_params):
    """
    Создаёт таблицы в тестовой БД.
    Выполняется один раз перед началом тестов.
    """
    connection = psycopg2.connect(**connection_params)

    try:
        with connection.cursor() as cursor:
            # Создаём таблицу финансовых метрик
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_metrics (
                    id SERIAL PRIMARY KEY,
                    borrower_id VARCHAR(50) NOT NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    actual_value DECIMAL(15, 2) NOT NULL,
                    reporting_period VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(borrower_id, metric_name, reporting_period)
                )
            """)

            # Создаём таблицу лимитов заемщика
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS borrower_limits (
                    id SERIAL PRIMARY KEY,
                    borrower_id VARCHAR(50) NOT NULL,
                    limit_type VARCHAR(100) NOT NULL,
                    limit_value DECIMAL(15, 2) NOT NULL,
                    current_usage DECIMAL(15, 2) NOT NULL DEFAULT 0,
                    available_limit DECIMAL(15, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(borrower_id, limit_type)
                )
            """)

            # Создаём индексы для ускорения запросов
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_financial_metrics_lookup 
                ON financial_metrics(borrower_id, metric_name, reporting_period)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_borrower_limits_lookup 
                ON borrower_limits(borrower_id, limit_type)
            """)

        connection.commit()

    finally:
        connection.close()


# ============================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: Заполнение тестовыми данными
# ============================================================
def insert_test_data(connection_params):
    """
    Заполняет таблицы тестовыми данными.
    Выполняется один раз перед началом тестов.
    """
    connection = psycopg2.connect(**connection_params)

    try:
        with connection.cursor() as cursor:
            # Вставляем финансовые метрики
            cursor.execute("""
                INSERT INTO financial_metrics (borrower_id, metric_name, actual_value, reporting_period)
                VALUES 
                    ('BORROWER-001', 'Debt/EBITDA', 2.4, '2024-Q3'),
                    ('BORROWER-001', 'Current Ratio', 1.8, '2024-Q3'),
                    ('BORROWER-002', 'Debt/EBITDA', 4.5, '2024-Q3'),
                    ('BORROWER-003', 'Net Debt / EBITDA', 3.1, '2024-Q3')
            """)

            # Вставляем лимиты заемщиков
            cursor.execute("""
                INSERT INTO borrower_limits (borrower_id, limit_type, limit_value, current_usage, available_limit)
                VALUES 
                    ('BORROWER-001', 'credit_limit', 1000000.0, 400000.0, 600000.0),
                    ('BORROWER-001', 'exposure_limit', 2000000.0, 800000.0, 1200000.0),
                    ('BORROWER-002', 'credit_limit', 500000.0, 450000.0, 50000.0),
                    ('BORROWER-003', 'credit_limit', 750000.0, 100000.0, 650000.0)
            """)

        connection.commit()

    finally:
        connection.close()


# ============================================================
# ТЕСТ 1: Успешное извлечение финансовой метрики из реальной БД
# ============================================================
def test_get_financial_metric_success_integration(postgres_container):
    """
    Проверяем, что инструмент корректно извлекает метрику из РЕАЛЬНОЙ БД (в контейнере).
    """
    result = get_financial_metric(
        borrower_id="BORROWER-001",
        metric_name="Debt/EBITDA",
        reporting_period="2024-Q3",
        db_connection_params=postgres_container
    )

    assert result is not None
    assert result.borrower_id == "BORROWER-001"
    assert result.metric_name == "Debt/EBITDA"
    assert result.actual_value == 2.4
    assert result.reporting_period == "2024-Q3"


# ============================================================
# ТЕСТ 2: Метрика не найдена в реальной БД
# ============================================================
def test_get_financial_metric_not_found_integration(postgres_container):
    """
    Проверяем, что инструмент возвращает None для несуществующей метрики.
    """
    result = get_financial_metric(
        borrower_id="BORROWER-999",  # Не существует в тестовых данных
        metric_name="Debt/EBITDA",
        reporting_period="2024-Q3",
        db_connection_params=postgres_container
    )

    assert result is None


# ============================================================
# ТЕСТ 3: Проверка другого заемщика и метрики
# ============================================================
def test_get_financial_metric_different_borrower_integration(postgres_container):
    """
    Проверяем извлечение метрики для другого заемщика.
    """
    result = get_financial_metric(
        borrower_id="BORROWER-002",
        metric_name="Debt/EBITDA",
        reporting_period="2024-Q3",
        db_connection_params=postgres_container
    )

    assert result is not None
    assert result.actual_value == 4.5


# ============================================================
# ТЕСТ 4: Проверка лимита заемщика — успешный сценарий
# ============================================================
def test_check_borrower_limit_success_integration(postgres_container):
    """
    Проверяем, что инструмент корректно извлекает информацию о лимите из реальной БД.
    """
    result = check_borrower_limit(
        borrower_id="BORROWER-001",
        limit_type="credit_limit",
        db_connection_params=postgres_container
    )

    assert result is not None
    assert result["borrower_id"] == "BORROWER-001"
    assert result["limit_type"] == "credit_limit"
    assert result["limit_value"] == 1000000.0
    assert result["current_usage"] == 400000.0
    assert result["available_limit"] == 600000.0


# ============================================================
# ТЕСТ 5: Лимит не найден
# ============================================================
def test_check_borrower_limit_not_found_integration(postgres_container):
    """
    Проверяем, что инструмент возвращает None для несуществующего лимита.
    """
    result = check_borrower_limit(
        borrower_id="BORROWER-999",
        limit_type="credit_limit",
        db_connection_params=postgres_container
    )

    assert result is None


# ============================================================
# ТЕСТ 6: Проверка другого типа лимита
# ============================================================
def test_check_borrower_limit_different_type_integration(postgres_container):
    """
    Проверяем извлечение другого типа лимита (exposure_limit).
    """
    result = check_borrower_limit(
        borrower_id="BORROWER-001",
        limit_type="exposure_limit",
        db_connection_params=postgres_container
    )

    assert result is not None
    assert result["limit_type"] == "exposure_limit"
    assert result["limit_value"] == 2000000.0