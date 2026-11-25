# Дефекты API Pizza Delivery

Проверил 25 ноября 2026 года на PostgreSQL 16 и коммите приложения
`a43ef6f79f6fcbb27b6710fd61cfa756ee4ee2d0`.
В описанных запросах получил HTTP 500 и JSON с полями `status: 500`,
`error: "Internal Server Error"`, `message: "Unexpected error"`.

Создайте заказ и скопируйте его `id`. Подставляйте UUID вместо `ORDER_ID`:

```bash
curl -i -X POST http://localhost:8080/orders \
  -H 'Content-Type: application/json' \
  -d '{"address":{"city":"Amsterdam","street":"Damrak","house":"1","postcode":"1012"},"items":[{"name":"Pizza","size":"SMALL","qty":1}]}'
```

## BUG-001. null в статусе

```bash
curl -i -X PATCH http://localhost:8080/orders/ORDER_ID/status \
  -H 'Content-Type: application/json' -d '{"status":null}'
```

Ожидаю **400 Bad Request**. Получаю **500**, заказ сохраняет прежние данные.
В конструкторе `ChangeOrderStatusCommand` вызов `Objects.requireNonNull(newStatus)`
выбрасывает `NullPointerException` до валидации use case.
В `WebExceptionHandler` для этого исключения действует общий обработчик.

Тест: `test_known_bugs.py::test_null_status`.

## BUG-002. Повреждённый JSON

```bash
curl -i -X POST http://localhost:8080/orders \
  -H 'Content-Type: application/json' -d '{broken'
curl -i -X POST http://localhost:8080/seminar/workflow/orders \
  -H 'Content-Type: application/json' -d '{broken'
```

Ожидаю **400 Bad Request**. Получаю **500** на обоих маршрутах.
В `WebExceptionHandler` для `HttpMessageNotReadableException` действует общий
обработчик с кодом 500.

Тест: `test_known_bugs.py::test_malformed_json`, два параметра.

## BUG-003. Преждевременные команды workflow

Выполните запросы для заказа в статусе CREATED:

```bash
curl -i -X POST http://localhost:8080/seminar/workflow/orders/ORDER_ID/start-cooking
curl -i -X POST http://localhost:8080/seminar/workflow/orders/ORDER_ID/assign-courier
curl -i -X POST http://localhost:8080/seminar/workflow/orders/ORDER_ID/deliver
```

Ожидаю **409 Conflict**, как при запрещённых переходах основного API.
Получаю **500** на трёх маршрутах; заказ сохраняет прежние данные.
В workflow-interactors вызов доменной политики выбрасывает `IllegalStateException`.
В `ChangeOrderStatusInteractor` разработчик преобразовал такое исключение
в `BusinessRuleViolationException`; в workflow этого преобразования нет.

Тест: `test_known_bugs.py::test_premature_workflow_command`, три параметра.

## Запуск воспроизведений

```bash
python -m pytest -m known_bug --runxfail -v
```

На указанном коммите вы получите **6 failed** и код выхода **1**.
В полном прогоне использую строгий xfail для этих случаев; прошедшие проверки
считаю отдельно. [Журнал запуска](known-bugs-run.txt).
