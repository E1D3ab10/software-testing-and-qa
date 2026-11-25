import allure
import pytest

from data.orders import REASON
from helpers.assertions import assert_error, assert_json, assert_no_content

pytestmark = [allure.epic("Pizza API"), allure.feature("Отмена и удаление")]


@pytest.mark.positive
@pytest.mark.parametrize("status", ["CREATED", "PAID", "COOKING"])
@allure.title("Отмена из {status}: 204, сохранены заказ и причина")
def test_cancel(api, create_order, status):
    original = create_order(status)
    assert_no_content(api.cancel(original["id"], REASON))
    cancelled = assert_json(api.get(original["id"]), 200, "order")
    assert cancelled == {**original, "status": "CANCELLED", "cancellationReason": REASON}
    orders = assert_json(api.list(), 200, "orders")
    assert next(item for item in orders if item["id"] == original["id"])["status"] == "CANCELLED"


@pytest.mark.positive
@pytest.mark.parametrize("reason", ["x", "x" * 1000], ids=["one-character", "1000-characters"])
@pytest.mark.parametrize("operation", ["cancel", "remove"])
@allure.title("Границы длины причины: {operation}")
def test_reason_boundaries(api, create_order, reason, operation):
    order = create_order()
    assert_no_content(getattr(api, operation)(order["id"], reason))
    if operation == "cancel":
        saved = assert_json(api.get(order["id"]), 200, "order")
        assert saved["cancellationReason"] == reason
    else:
        assert_error(api.get(order["id"]), 404, f"/orders/{order['id']}")


@pytest.mark.positive
@allure.title("Повторная отмена идемпотентна; пробелы в причине удаляются")
def test_cancel_retry(api, create_order):
    order = create_order()
    assert_no_content(api.cancel(order["id"], f"  {REASON}  "))
    cancelled = assert_json(api.get(order["id"]), 200, "order")
    assert cancelled["cancellationReason"] == REASON
    assert_no_content(api.cancel(order["id"], REASON))
    assert assert_json(api.get(order["id"]), 200, "order") == cancelled


@pytest.mark.negative
@pytest.mark.parametrize("operation", ["cancel", "remove"])
@allure.title("Другая причина для отменённого заказа: {operation} возвращает 409")
def test_different_reason(api, create_order, operation):
    order = create_order()
    assert_no_content(api.cancel(order["id"], REASON))
    original = assert_json(api.get(order["id"]), 200, "order")
    path = f"/orders/{order['id']}" + ("/remove" if operation == "remove" else "")
    assert_error(getattr(api, operation)(order["id"], "Другая причина"), 409, path)
    assert assert_json(api.get(order["id"]), 200, "order") == original


@pytest.mark.negative
@pytest.mark.parametrize("status", ["OUT_FOR_DELIVERY", "DELIVERED"])
@pytest.mark.parametrize("operation", ["cancel", "remove"])
@allure.title("{operation} запрещён из {status}: 409")
def test_terminal_order(api, create_order, status, operation):
    order = create_order(status)
    path = f"/orders/{order['id']}" + ("/remove" if operation == "remove" else "")
    assert_error(getattr(api, operation)(order["id"], REASON), 409, path)
    assert assert_json(api.get(order["id"]), 200, "order") == order


@pytest.mark.negative
@pytest.mark.parametrize("reason", [None, "", "   ", "x" * 1001], ids=["missing", "empty", "blank", "too-long"])
@pytest.mark.parametrize("operation", ["cancel", "remove"])
@allure.title("Невалидная причина {operation}: 400, заказ неизменен")
def test_invalid_reason(api, create_order, reason, operation):
    order = create_order()
    path = f"/orders/{order['id']}" + ("/remove" if operation == "remove" else "")
    assert_error(getattr(api, operation)(order["id"], reason), 400, path)
    assert assert_json(api.get(order["id"]), 200, "order") == order


@pytest.mark.positive
@pytest.mark.parametrize("status", ["CREATED", "PAID", "COOKING", "CANCELLED"])
@allure.title("Полное удаление из {status}: 204, затем 404 и отсутствие в списке")
def test_remove(api, create_order, status):
    order = create_order("CREATED" if status == "CANCELLED" else status)
    if status == "CANCELLED":
        assert_no_content(api.cancel(order["id"], REASON))
    assert_no_content(api.remove(order["id"], REASON))
    assert_error(api.get(order["id"]), 404, f"/orders/{order['id']}")
    assert_error(api.remove(order["id"], REASON), 404, f"/orders/{order['id']}/remove")
    assert order["id"] not in {item["id"] for item in assert_json(api.list(), 200, "orders")}
