"""Expected API behavior. Strict, narrow xfail records confirmed application defects.

Run `pytest -m known_bug --runxfail` to see these as ordinary failed tests.
"""
import allure
import pytest

from client.pizza_api import WORKFLOW
from helpers.assertions import KnownApiDefect, assert_client_error, assert_json

pytestmark = [pytest.mark.negative, pytest.mark.known_bug,
              allure.epic("Pizza API"), allure.feature("Известные дефекты приложения")]


@pytest.mark.xfail(strict=True, raises=KnownApiDefect, reason="BUG-001: null status gives 500 instead of 400")
@allure.description("BUG-001: null-статус приводит к 500. Подробности и curl: docs/BUGS.md.")
@allure.title("BUG-001: null-статус должен возвращать 400")
def test_null_status(api, create_order):
    original = create_order()
    response = api.change_status(original["id"], None)
    assert assert_json(api.get(original["id"]), 200, "order") == original
    assert_client_error(response, 400, f"/orders/{original['id']}/status", "BUG-001")


@pytest.mark.parametrize("path", ["/orders", WORKFLOW])
@pytest.mark.xfail(strict=True, raises=KnownApiDefect, reason="BUG-002: malformed JSON gives 500 instead of 400")
@allure.title("BUG-002: повреждённый JSON должен возвращать 400 ({path})")
def test_malformed_json(api, path):
    response = api.request("POST", path, data="{broken", headers={"Content-Type": "application/json"})
    assert_client_error(response, 400, path, "BUG-002")


@pytest.mark.parametrize("route", ["start-cooking", "assign-courier", "deliver"])
@pytest.mark.xfail(strict=True, raises=KnownApiDefect, reason="BUG-003: invalid workflow transition gives 500 instead of 409")
@allure.title("BUG-003: {route} из CREATED должен возвращать 409")
def test_premature_workflow_command(api, create_order, route):
    original = create_order()
    response = api.workflow_command(original["id"], route)
    assert assert_json(api.get(original["id"]), 200, "order") == original
    assert_client_error(response, 409, f"{WORKFLOW}/{original['id']}/{route}", "BUG-003")
