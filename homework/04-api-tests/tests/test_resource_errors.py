from uuid import uuid4

import allure
import pytest

from data.orders import REASON
from helpers.assertions import assert_error

pytestmark = [pytest.mark.negative, allure.epic("Pizza API"), allure.feature("Ошибки ресурса")]


@pytest.mark.parametrize("operation", ["get", "status", "cancel", "remove"])
@pytest.mark.parametrize("invalid_uuid", [False, True], ids=["unknown-uuid", "malformed-uuid"])
@allure.title("{operation}: неизвестный заказ — 404, неверный UUID — 400")
def test_resource_error(api, operation, invalid_uuid):
    order_id = "not-a-uuid" if invalid_uuid else str(uuid4())
    path = f"/orders/{order_id}"
    if operation == "get":
        response = api.get(order_id)
    elif operation == "status":
        response = api.change_status(order_id, "PAID")
        path += "/status"
    elif operation == "cancel":
        response = api.cancel(order_id, REASON)
    else:
        response = api.remove(order_id, REASON)
        path += "/remove"
    assert_error(response, 400 if invalid_uuid else 404, path)
