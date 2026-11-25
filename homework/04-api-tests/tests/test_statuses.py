import allure
import pytest

from data.orders import ALLOWED_TRANSITIONS, STATUSES
from helpers.assertions import assert_error, assert_json

pytestmark = [allure.epic("Pizza API"), allure.feature("Статусы заказов")]


@pytest.mark.positive
@pytest.mark.parametrize("source,target", ALLOWED_TRANSITIONS)
@allure.title("Разрешён переход {source} → {target}")
def test_allowed_transition(api, create_order, source, target):
    original = create_order(source)
    updated = assert_json(api.change_status(original["id"], target), 200, "order")
    assert updated == {**original, "status": target}
    assert assert_json(api.get(original["id"]), 200, "order") == updated


FORBIDDEN = [(source, target) for source in STATUSES for target in STATUSES
             if (source, target) not in ALLOWED_TRANSITIONS]


@pytest.mark.negative
@pytest.mark.parametrize("source,target", FORBIDDEN)
@allure.title("Запрещён переход {source} → {target}: 409, заказ неизменен")
def test_forbidden_transition(api, create_order, source, target):
    original = create_order(source)
    path = f"/orders/{original['id']}/status"
    assert_error(api.change_status(original["id"], target), 409, path, "Illegal status transition")
    assert assert_json(api.get(original["id"]), 200, "order") == original


@pytest.mark.negative
@pytest.mark.parametrize("status", ["", "  ", "UNKNOWN"])
@allure.title("Некорректный статус {status}: 400, заказ неизменен")
def test_invalid_status(api, create_order, status):
    original = create_order()
    assert_error(api.change_status(original["id"], status), 400, f"/orders/{original['id']}/status")
    assert assert_json(api.get(original["id"]), 200, "order") == original


@pytest.mark.positive
@allure.title("Статус принимает регистр и окружающие пробелы")
def test_status_normalization(api, create_order):
    original = create_order()
    updated = assert_json(api.change_status(original["id"], " paid "), 200, "order")
    assert updated["status"] == "PAID"
