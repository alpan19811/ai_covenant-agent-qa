# AI Covenant Agent QA Framework

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![pytest](https://img.shields.io/badge/pytest-8.3.3-green.svg)](https://docs.pytest.org/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-2.9.2-purple.svg)](https://docs.pydantic.dev/)
[![Testcontainers](https://img.shields.io/badge/testcontainers-4.8.1-orange.svg)](https://testcontainers.com/)

---

## 🎯 Overview / Обзор
**EN:** Production-grade QA automation framework for testing AI-powered covenant validation agents in the FinTech/Banking domain. It demonstrates a comprehensive 4-level testing strategy for LLM-based systems, including unit tests, real database integration (Testcontainers), metric-based LLM evaluation, and adversarial robustness testing.

**RU:** Production-grade фреймворк автоматизации тестирования AI-агентов для валидации кредитных ковенант в финтехе/банкинге. Демонстрирует комплексную 4-уровневую стратегию тестирования LLM-систем: модульные тесты, интеграция с реальной БД (Testcontainers), метрическая оценка качества LLM и тестирование на устойчивость к атакам.

---

## 📂 Project Structure / Структура проекта
*(Stable Markdown list / Стабильный список)*

* **`src/`** — Исходный код AI-агента (Pydantic-модели, SQL-инструменты, логика извлечения).
* **`tests/unit/`** — Модульные тесты (изолированная проверка валидации и моков БД/LLM).
* **`tests/integration/`** — Интеграционные тесты (взаимодействие с реальной PostgreSQL через Docker-контейнеры).
* **`tests/evaluation/`** — Оценка качества LLM (расчёт Precision, Recall, F1-score на основе Ground Truth).
* **`tests/adversarial/`** — Тестирование на устойчивость (защита от галлюцинаций, Prompt Injection, Out-of-Domain данных).
* **`data/`** — Эталонный датасет (`ground_truth.json`) для валидации ответов агента.
* **`reports/`** — Отчёты Allure (генерируются автоматически).

---

## 🧪 4-Level Testing Strategy / Стратегия тестирования

1. **Unit Testing (10 тестов):** Проверка строгих Pydantic-схем и логики SQL-инструментов с использованием `pytest-mock`.
2. **Integration Testing (6 тестов):** Тестирование с реальной PostgreSQL 16 через `testcontainers`. *Достижение: выявлен и исправлен реальный баг в SQL-логике (отсутствие поля в SELECT).*
3. **Evaluation Testing (3 теста):** Метрическая оценка качества ответов LLM. Сравнение с эталоном для выявления False Positives (галлюцинаций) и False Negatives (пропусков).
4. **Adversarial Testing (5 тестов):** Проверка устойчивости агента. Демонстрация того, что строгая Pydantic-валидация выступает как Security Guardrail, отсеивая вредоносные промпты и сломанные схемы.

---

## 🚀 Quick Start / Быстрый старт

### Prerequisites / Требования
* Python 3.12+
* Docker Desktop (обязательно для интеграционных тестов)

### Installation / Установка
```bash
git clone https://github.com/alpan19811/ai_covenant-agent-qa.git
cd ai_covenant-agent-qa
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt


# Run Tests / Запуск тестов
# Все тесты (All tests)
pytest tests/ -v --tb=short

# Только интеграционные тесты (Requires Docker)
pytest tests/integration/ -v -s

# Генерация Allure-отчёта (Generate Allure report)
pytest tests/ --alluredir=reports/allure-results
allure serve reports/allure-results


# Key Features / Ключевые особенности
Pydantic as Security Guardrail: Кастомные валидаторы (@field_validator) предотвращают пропуск галлюцинаций LLM (например, финансового ковенанта без порогового значения) в бизнес-логику.
Domain Expertise: Проект опирается на 14-летний опыт кредитного анализа и знание регуляторных требований (Положение ЦБ РФ № 590-П).
Zero-Config DB Testing: testcontainers автоматически поднимает и уничтожает изолированную PostgreSQL для каждого прогона тестов.


# Tech Stack / Технологический стек
Language: Python 3.12
Testing: pytest, pytest-mock, pytest-asyncio
Validation: Pydantic v2
Database: PostgreSQL 16, psycopg2-binary, Testcontainers
AI/LLM: Ollama, LangChain (conceptual)
Reporting: Allure