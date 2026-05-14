import base64
import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
REQUIRED_FIELDS = ("name", "phone", "email", "message")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    method = _get_http_method(event)

    if method == "OPTIONS":
        return _response(204, None)

    if method != "POST":
        return _response(405, {"message": "Metodo nao permitido."})

    try:
        payload = _parse_body(event)
    except ValueError as exc:
        return _response(400, {"message": str(exc)})

    errors = _validate_payload(payload)
    if errors:
        return _response(400, {"message": "Dados invalidos.", "errors": errors})

    demo_request = _build_demo_request(payload)
    _persist_demo_request(demo_request)

    return _response(
        200,
        {
            "message": "Solicitacao recebida com sucesso.",
            "requestId": demo_request["id"],
        },
    )


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")

    if body is None:
        return {}

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    try:
        parsed = json.loads(body)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("JSON invalido.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("O corpo da requisicao deve ser um objeto JSON.")

    return parsed


def _validate_payload(payload: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}

    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors[field] = "Campo obrigatorio."

    email = payload.get("email")
    if isinstance(email, str) and email.strip() and not EMAIL_PATTERN.match(email.strip()):
        errors["email"] = "E-mail invalido."

    return errors


def _build_demo_request(payload: dict[str, Any]) -> dict[str, str]:
    now = datetime.now(timezone.utc).isoformat()

    return {
        "id": str(uuid.uuid4()),
        "name": payload["name"].strip(),
        "phone": payload["phone"].strip(),
        "email": payload["email"].strip().lower(),
        "message": payload["message"].strip(),
        "source": str(payload.get("source") or "totalhub-site").strip(),
        "submittedAt": str(payload.get("submittedAt") or now).strip(),
        "receivedAt": now,
    }


def _persist_demo_request(demo_request: dict[str, str]) -> None:
    table_name = os.environ.get("DEMO_REQUESTS_TABLE")

    if not table_name:
        print(json.dumps({"demoRequest": demo_request}, ensure_ascii=False))
        return

    import boto3

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    table.put_item(Item=demo_request)


def _get_http_method(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext") or {}
    http_context = request_context.get("http") or {}

    return (
        http_context.get("method")
        or event.get("httpMethod")
        or event.get("requestContext", {}).get("httpMethod")
        or ""
    ).upper()


def _response(status_code: int, body: dict[str, Any] | None) -> dict[str, Any]:
    headers = {
        "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN", "*"),
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
        "Content-Type": "application/json",
    }

    response: dict[str, Any] = {
        "statusCode": status_code,
        "headers": headers,
    }

    if body is not None:
        response["body"] = json.dumps(body, ensure_ascii=False)
    else:
        response["body"] = ""

    return response
