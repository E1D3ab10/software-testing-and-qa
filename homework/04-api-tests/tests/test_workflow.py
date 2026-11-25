from uuid import uuid4

import allure
import pytest

from client.pizza_api import WORKFLOW
from data.orders import WORKFLOW_STEPS, order_payload
from helpers.assertions import assert_error, assert_json

pytestmark = [allure.epic("Pizza API"), allure.feature("Процесс доставки")]
FLAGS = ("paymentReceived", "cookingStarted", "courierAssigned", "delivered")


@pytest.mark.positive
@allure.title("Workflow: создание → оплата → кухня → курьер → доставка")
def test_workflow(api):
    step = assert_json(api.workflow_create(order_payload()), 200, "workflow")
    order_id = step["orderId"]
    assert step["executedCommand"] == "CreateOrder"
    assert step["emittedEvent"] == "OrderCreated"
    assert step["currentStatus"] == "CREATED"
    assert step["suggestedNextCommand"] == "ReceivePayment"
    board = assert_json(api.board(order_id), 200, "board")
    assert board == step["board"]
    assert board["id"] == order_id
    assert not any(board[flag] for flag in FLAGS)
    for index, (route, command, event, status, next_command) in enumerate(WORKFLOW_STEPS):
        with allure.step(f"{command} → {event}"):
            step = assert_json(api.workflow_command(order_id, route), 200, "workflow")
            assert step["orderId"] == order_id
            assert step["executedCommand"] == command
            assert step["emittedEvent"] == event
            assert step["currentStatus"] == status
            assert step["suggestedNextCommand"] == next_command
            board = assert_json(api.board(order_id), 200, "board")
            assert board == step["board"]
            assert board["currentStatus"] == status
            assert board["nextSuggestedCommand"] == next_command
            assert [board[flag] for flag in FLAGS] == [position <= index for position in range(4)]
            order = assert_json(api.get(order_id), 200, "order")
            assert order["status"] == status
            assert order["totalAmount"] == board["totalAmount"] == 32


@pytest.mark.negative
@pytest.mark.parametrize("route", ["board", *(step[0] for step in WORKFLOW_STEPS)])
@allure.title("Workflow {route}: неизвестный заказ — 404")
def test_workflow_not_found(api, route):
    order_id = str(uuid4())
    response = api.board(order_id) if route == "board" else api.workflow_command(order_id, route)
    assert_error(response, 404, f"{WORKFLOW}/{order_id}/{route}")


@pytest.mark.negative
@allure.title("Workflow: пустой список пицц — 400")
def test_workflow_invalid_create(api):
    payload = order_payload()
    payload["items"] = []
    assert_error(api.workflow_create(payload), 400, WORKFLOW, "items")
