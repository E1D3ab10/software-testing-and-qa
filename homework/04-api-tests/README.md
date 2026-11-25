# Домашнее задание 4. API-автотесты Pizza Delivery

API-тесты для [NZRV-88/TestProject](https://github.com/NZRV-88/TestProject):
Python, pytest, requests, JSON Schema и Allure. Версия приложения указана в [sut.lock.json](sut.lock.json).

Результат: **116 passed, 6 xfailed**. Шесть xfail воспроизводят [три дефекта API](docs/BUGS.md).
[Скриншот Allure](docs/allure-overview.png) · [HTML-отчет](docs/allure-report.html) · [Вывод pytest](docs/pytest-output.txt).

## Запуск

Нужны Python 3.12+, Git и Docker с Compose v2. Для Allure: Node.js 22+ и Java 17+.
Порты 8080 и 5173 должны быть свободны.

```bash
git clone https://github.com/E1D3ab10/software-testing-and-qa.git
cd software-testing-and-qa/homework/04-api-tests
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/sut.py start
python -m pytest -v
```

В Windows: `py -3 -m venv .venv`, затем `.\.venv\Scripts\Activate.ps1`.
Через `start` вы клонируете приложение, собираете контейнеры и дожидаетесь готовности API.
API: [localhost:8080/orders](http://localhost:8080/orders), UI: [localhost:5173](http://localhost:5173).

Для другого адреса: `BASE_URL=http://localhost:8080 python -m pytest -v`.
Для удаления тестового стенда и его БД: `python scripts/sut.py reset`.

## Allure

```bash
npm ci
npm run report
npm run report:open
```

Результаты находятся в `allure-results/`, отчет в `allure-report/`.
Готовый [HTML-отчет](docs/allure-report.html) можно скачать и открыть без сервера.

## Покрытие и структура

Проверяю создание, чтение, статусы, отмену и удаление заказов, процесс доставки.
В наборе есть позитивные и негативные сценарии, проверки кодов 200/201/204/400/404/409
и JSON Schema ответов. Тесты создают собственные заказы.

Код разделен на HTTP-клиент (`client/`), настройки (`config/`), данные (`data/`),
схемы (`schemas/`), проверки (`helpers/`) и сценарии (`tests/`).

В [GitHub Actions](../../.github/workflows/hw4-api-tests.yml) настроил запуск тестов
и сохранение Allure-отчета в артефакте `api-test-report`.
