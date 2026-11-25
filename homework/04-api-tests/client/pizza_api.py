"""HTTP client: transport and Allure attachments, no expected status codes."""
import json

import allure
import requests

WORKFLOW = "/seminar/workflow/orders"


class PizzaApi:
    def __init__(self, settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers["Accept"] = "application/json"
        # Only IDs returned by this test's POST requests can enter cleanup.
        self.created_ids = set()

    def close(self):
        self.session.close()

    def request(self, method, path, **kwargs):
        with allure.step(f"{method} {path}"):
            allure.attach(
                json.dumps({"method": method, "path": path, **kwargs}, ensure_ascii=False, indent=2),
                "Request", allure.attachment_type.JSON,
            )
            response = self.session.request(
                method, self.settings.base_url + path,
                timeout=self.settings.timeout, allow_redirects=False, **kwargs,
            )
            allure.attach(
                json.dumps({"status": response.status_code, "headers": dict(response.headers),
                            "body": response.text}, ensure_ascii=False, indent=2),
                "Response", allure.attachment_type.JSON,
            )
            if method == "POST" and path in {"/orders", WORKFLOW} and response.ok:
                body = response.json()
                order_id = body.get("id") or body.get("orderId")
                if order_id:
                    self.created_ids.add(order_id)
            return response

    def create(self, payload):
        return self.request("POST", "/orders", json=payload)

    def get(self, order_id):
        return self.request("GET", f"/orders/{order_id}")

    def list(self):
        return self.request("GET", "/orders")

    def change_status(self, order_id, status):
        return self.request("PATCH", f"/orders/{order_id}/status", json={"status": status})

    def cancel(self, order_id, reason):
        return self.request("DELETE", f"/orders/{order_id}", params={"reason": reason})

    def remove(self, order_id, reason):
        return self.request("DELETE", f"/orders/{order_id}/remove", params={"reason": reason})

    def workflow_create(self, payload):
        return self.request("POST", WORKFLOW, json=payload)

    def workflow_command(self, order_id, command):
        return self.request("POST", f"{WORKFLOW}/{order_id}/{command}")

    def board(self, order_id):
        return self.request("GET", f"{WORKFLOW}/{order_id}/board")
