import json
from functools import lru_cache
from http import HTTPStatus
from pathlib import Path

import allure
from jsonschema import Draft202012Validator, FormatChecker


@lru_cache
def validator(name):
    schema = json.loads((Path(__file__).parents[1] / "schemas/contracts.json").read_text())
    schema["$ref"] = f"#/$defs/{name}"
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def assert_json(response, status, schema):
    with allure.step(f"Status {status}, JSON contract: {schema}"):
        assert response.status_code == status, response.text
        assert response.headers.get("Content-Type", "").split(";")[0] == "application/json"
        body = response.json()
        validator(schema).validate(body)
        return body


def assert_error(response, status, path, message=None):
    body = assert_json(response, status, "error")
    assert body["status"] == status
    assert body["error"] == HTTPStatus(status).phrase
    assert body["path"] == path
    if message:
        assert message in body["message"]
    return body


def assert_no_content(response):
    assert response.status_code == 204, response.text
    assert response.content == b"", "A 204 response must have no body"


class KnownApiDefect(AssertionError):
    """Only the specifically reproduced 500 response is eligible for xfail."""


def assert_client_error(response, status, path, defect):
    if response.status_code == 500:
        body = assert_error(response, 500, path)
        assert body["message"] == "Unexpected error"
        raise KnownApiDefect(f"{defect}: expected HTTP {status}, received HTTP 500")
    assert_error(response, status, path)
