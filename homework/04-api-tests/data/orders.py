"""Fresh payloads and explicit business expectations, not imported from the SUT."""
from copy import deepcopy
from uuid import uuid4

BASE_ORDER = {
    "address": {"city": "Amsterdam", "street": "Damrak", "house": "1",
                "apartment": "12", "postcode": "1012"},
    "items": [{"name": "Margherita", "size": "MEDIUM", "qty": 2},
              {"name": "Pepperoni", "size": "LARGE", "qty": 1}],
}
STATUSES = ("CREATED", "PAID", "COOKING", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED")
ALLOWED_TRANSITIONS = (
    ("CREATED", "PAID"), ("PAID", "COOKING"),
    ("COOKING", "OUT_FOR_DELIVERY"), ("OUT_FOR_DELIVERY", "DELIVERED"),
    ("CREATED", "CANCELLED"), ("PAID", "CANCELLED"), ("COOKING", "CANCELLED"),
)
PATHS_TO_STATUS = {
    "CREATED": [], "PAID": ["PAID"], "COOKING": ["PAID", "COOKING"],
    "OUT_FOR_DELIVERY": ["PAID", "COOKING", "OUT_FOR_DELIVERY"],
    "DELIVERED": ["PAID", "COOKING", "OUT_FOR_DELIVERY", "DELIVERED"],
    "CANCELLED": ["CANCELLED"],
}
REASON = "Ошибочный тестовый заказ"
WORKFLOW_STEPS = (
    ("payment-received", "ReceivePayment", "PaymentReceived", "PAID", "StartCooking"),
    ("start-cooking", "StartCooking", "CookingStarted", "COOKING", "AssignCourier"),
    ("assign-courier", "AssignCourier", "CourierAssigned", "OUT_FOR_DELIVERY", "DeliverOrder"),
    ("deliver", "DeliverOrder", "OrderDelivered", "DELIVERED", "None"),
)


def order_payload():
    payload = deepcopy(BASE_ORDER)
    payload["items"][0]["name"] = f"Margherita-{uuid4().hex[:10]}"
    return payload


def changed_payload(path, value):
    payload = order_payload()
    current = payload
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value
    return payload
