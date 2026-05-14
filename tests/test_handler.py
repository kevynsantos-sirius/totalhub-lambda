import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.handler import lambda_handler


def setup_function():
    os.environ.pop("DEMO_REQUESTS_TABLE", None)
    os.environ["ALLOWED_ORIGIN"] = "http://localhost:5173"


def test_accepts_valid_demo_request():
    response = lambda_handler(_event(body=_valid_payload()), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["message"] == "Solicitacao recebida com sucesso."
    assert body["requestId"]
    assert response["headers"]["Access-Control-Allow-Origin"] == "http://localhost:5173"


def test_rejects_missing_required_fields():
    payload = _valid_payload()
    payload["email"] = ""

    response = lambda_handler(_event(body=payload), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["errors"]["email"] == "Campo obrigatorio."


def test_rejects_invalid_email():
    payload = _valid_payload()
    payload["email"] = "cliente-sem-arroba"

    response = lambda_handler(_event(body=payload), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["errors"]["email"] == "E-mail invalido."


def test_handles_options_preflight():
    response = lambda_handler(
        {"requestContext": {"http": {"method": "OPTIONS"}}},
        None,
    )

    assert response["statusCode"] == 204
    assert response["body"] == ""


def test_rejects_invalid_json():
    response = lambda_handler(_event(raw_body="{"), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["message"] == "JSON invalido."


def _event(body=None, raw_body=None):
    if raw_body is None:
        raw_body = json.dumps(body)

    return {
        "version": "2.0",
        "requestContext": {"http": {"method": "POST"}},
        "body": raw_body,
        "isBase64Encoded": False,
    }


def _valid_payload():
    return {
        "name": "Cliente TotalHub",
        "phone": "(11) 99999-0000",
        "email": "cliente@empresa.com",
        "message": "Quero conhecer a plataforma.",
        "source": "totalhub-site",
        "submittedAt": "2026-05-14T15:00:00.000Z",
    }
