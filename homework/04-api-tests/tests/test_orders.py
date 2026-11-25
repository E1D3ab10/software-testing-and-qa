from decimal import Decimal

import allure
import pytest

from data.orders import changed_payload, order_payload
from helpers.assertions import assert_error, assert_json

pytestmark = [allure.epic("Pizza API"), allure.feature("Создание и чтение заказов")]


@pytest.mark.positive
@allure.title("POST /orders: создание, Location, чтение и наличие в списке")
def test_create_and_read_order(api):
    payload = order_payload()
    response = api.create(payload)
    order = assert_json(response, 201, "order")
    assert response.headers["Location"] == f"/orders/{order['id']}"
    assert order["status"] == "CREATED"
    assert order["address"] == payload["address"]
    assert order["items"] == payload["items"]
    assert Decimal(str(order["totalAmount"])) == Decimal("32.00")
    assert order["currency"] == "EUR"
    assert order["deliveryZone"] == "CENTER"
    assert order["cancellationReason"] is None
    assert assert_json(api.get(order["id"]), 200, "order") == order
    orders = assert_json(api.list(), 200, "orders")
    assert [item for item in orders if item["id"] == order["id"]] == [
        {key: order[key] for key in ("id", "status", "totalAmount", "currency", "deliveryZone")}
    ]


@pytest.mark.positive
@pytest.mark.parametrize("size,qty,amount", [("SMALL", 1, "8"), ("MEDIUM", 3, "30"), ("LARGE", 2, "24")])
@allure.title("Цена зависит от размера и количества: {size}, qty={qty}")
def test_price(api, size, qty, amount):
    payload = order_payload()
    payload["items"] = [{"name": "Pizza", "size": size, "qty": qty}]
    order = assert_json(api.create(payload), 201, "order")
    assert Decimal(str(order["totalAmount"])) == Decimal(amount)
    assert order["items"] == payload["items"]


@pytest.mark.positive
@pytest.mark.parametrize("postcode,zone", [("1012", "CENTER"), ("1100", "CENTER"), ("2000", "OUTSKIRTS")])
@allure.title("Зона доставки для индекса {postcode}: {zone}")
def test_delivery_zone(api, postcode, zone):
    order = assert_json(api.create(changed_payload(("address", "postcode"), postcode)), 201, "order")
    assert order["deliveryZone"] == zone


@pytest.mark.positive
@allure.title("Нормализация имени пиццы и размера")
def test_normalization(api):
    payload = order_payload()
    payload["items"] = [{"name": "  Margherita  ", "size": " medium ", "qty": 1}]
    order = assert_json(api.create(payload), 201, "order")
    assert order["items"] == [{"name": "Margherita", "size": "MEDIUM", "qty": 1}]


@pytest.mark.positive
@allure.title("Квартира необязательна")
def test_optional_apartment(api):
    payload = order_payload()
    del payload["address"]["apartment"]
    order = assert_json(api.create(payload), 201, "order")
    assert order["address"]["apartment"] is None


INVALID_FIELDS = [
    pytest.param(("items",), [], "items", id="empty-items"),
    pytest.param(("items",), None, "items", id="null-items"),
    pytest.param(("items", 0), None, "item.name", id="null-item"),
    pytest.param(("address",), None, "address.city", id="null-address"),
    pytest.param(("items", 0, "name"), "", "item.name", id="empty-name"),
    pytest.param(("items", 0, "name"), "  ", "item.name", id="blank-name"),
    pytest.param(("items", 0, "name"), None, "item.name", id="null-name"),
    pytest.param(("items", 0, "size"), "", "item.size", id="empty-size"),
    pytest.param(("items", 0, "size"), None, "item.size", id="null-size"),
    pytest.param(("items", 0, "size"), "XL", "Unknown size", id="unknown-size"),
    pytest.param(("items", 0, "qty"), 0, "item.qty", id="zero-quantity"),
    pytest.param(("items", 0, "qty"), -1, "item.qty", id="negative-quantity"),
]
for field in ("city", "street", "house", "postcode"):
    for value, label in [("", "empty"), ("  ", "blank"), (None, "null")]:
        INVALID_FIELDS.append(pytest.param(("address", field), value, f"address.{field}", id=f"{label}-{field}"))


@pytest.mark.negative
@pytest.mark.parametrize("path,value,message", INVALID_FIELDS)
@allure.title("Невалидный заказ отклоняется с 400: {path}")
def test_invalid_order(api, path, value, message):
    assert_error(api.create(changed_payload(path, value)), 400, "/orders", message)


@pytest.mark.negative
@pytest.mark.parametrize("field", ["address", "items"])
@allure.title("Отсутствует обязательное поле {field}")
def test_missing_field(api, field):
    payload = order_payload()
    del payload[field]
    assert_error(api.create(payload), 400, "/orders")
