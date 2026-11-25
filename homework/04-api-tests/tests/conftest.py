import json
import platform
from pathlib import Path

import allure
import pytest
import requests

from client.pizza_api import PizzaApi
from config.settings import Settings
from data.orders import PATHS_TO_STATUS, REASON, order_payload
from helpers.assertions import assert_json


@pytest.fixture(scope="session")
def settings():
    return Settings.from_env()


@pytest.fixture(scope="session", autouse=True)
def check_api(settings):
    try:
        response = requests.get(settings.base_url + "/orders", timeout=settings.timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        pytest.exit(f"API unavailable at {settings.base_url}. Run python scripts/sut.py start. {exc}", returncode=2)


@pytest.fixture
def api(settings):
    client = PizzaApi(settings)
    yield client
    errors = []
    try:
        with allure.step("Cleanup: only orders created by this test"):
            for order_id in client.created_ids:
                response = client.get(order_id)
                if response.status_code == 404:
                    continue
                if response.status_code != 200:
                    errors.append(f"GET {order_id}: {response.status_code}")
                    continue
                order = response.json()
                if order["status"] in {"OUT_FOR_DELIVERY", "DELIVERED"}:
                    allure.attach(order_id, "Terminal order: removed with disposable Docker environment")
                    continue
                # PATCH cancellation has no stored reason; it cannot be removed via the public API.
                if order["status"] == "CANCELLED" and not order["cancellationReason"]:
                    allure.attach(order_id, "PATCH-cancelled order: removed with disposable Docker environment")
                    continue
                response = client.remove(order_id, order["cancellationReason"] or REASON)
                if response.status_code not in {204, 404}:
                    errors.append(f"DELETE {order_id}: {response.status_code} {response.text}")
    finally:
        client.close()
    assert not errors, "Cleanup failed: " + "; ".join(errors)


@pytest.fixture
def create_order(api):
    def create(status="CREATED", payload=None):
        body = assert_json(api.create(payload if payload is not None else order_payload()), 201, "order")
        order_id = body["id"]
        for target in PATHS_TO_STATUS[status]:
            body = assert_json(api.change_status(order_id, target), 200, "order")
            assert body["status"] == target
        return body
    return create


def pytest_sessionfinish(session, exitstatus):
    output = session.config.getoption("allure_report_dir")
    if output:
        directory = Path(output)
        directory.mkdir(parents=True, exist_ok=True)
        settings = Settings.from_env()
        lock = json.loads((Path(__file__).parents[1] / "sut.lock.json").read_text())
        (directory / "environment.properties").write_text(
            f"Base.URL={settings.base_url}\nPython={platform.python_version()}\n"
            f"SUT.Revision={lock['revision']}\nSUT.Source={lock['repository']}\n",
            encoding="utf-8",
        )
