import base64
import json
import os
import re
import smtplib
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
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

    try:
        _send_demo_request_email(demo_request)
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc), "demoRequest": demo_request}, ensure_ascii=False))
        return _response(500, {"message": "Nao foi possivel enviar a solicitacao."})

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


def _send_demo_request_email(demo_request: dict[str, str]) -> None:
    config = _get_smtp_config()
    message = _build_email_message(demo_request, config)

    try:
        with smtplib.SMTP(config["host"], int(config["port"]), timeout=10) as smtp:
            if config["use_tls"]:
                smtp.starttls()

            if config["username"] and config["password"]:
                smtp.login(config["username"], config["password"])

            smtp.send_message(message)
    except Exception as exc:
        raise RuntimeError("Falha ao enviar e-mail SMTP.") from exc


def _get_smtp_config() -> dict[str, Any]:
    recipients = _split_recipients(os.environ.get("SMTP_TO_EMAILS", ""))

    config = {
        "host": os.environ.get("SMTP_HOST", "").strip(),
        "port": os.environ.get("SMTP_PORT", "587").strip(),
        "username": os.environ.get("SMTP_USERNAME", "").strip(),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "from_email": os.environ.get("SMTP_FROM_EMAIL", "").strip(),
        "to_emails": recipients,
        "use_tls": os.environ.get("SMTP_USE_TLS", "true").strip().lower()
        in ("1", "true", "yes", "sim"),
    }

    missing_fields = [
        key
        for key in ("host", "port", "from_email")
        if not config[key]
    ]

    if not recipients:
        missing_fields.append("to_emails")

    if missing_fields:
        raise RuntimeError(f"Configuracao SMTP incompleta: {', '.join(missing_fields)}.")

    if not str(config["port"]).isdigit():
        raise RuntimeError("Configuracao SMTP invalida: port.")

    return config


def _split_recipients(value: str) -> list[str]:
    return [email.strip() for email in value.split(";") if email.strip()]


def _build_email_message(
    demo_request: dict[str, str],
    config: dict[str, Any],
) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = f"Nova solicitacao de demonstracao - {demo_request['name']}"
    message["From"] = config["from_email"]
    message["To"] = ", ".join(config["to_emails"])
    message["Reply-To"] = demo_request["email"]
    message.set_content(
        "\n".join(
            [
                "Nova solicitacao de demonstracao recebida pelo site TotalHub.",
                "",
                f"ID: {demo_request['id']}",
                f"Nome: {demo_request['name']}",
                f"Telefone: {demo_request['phone']}",
                f"E-mail: {demo_request['email']}",
                f"Origem: {demo_request['source']}",
                f"Enviado em: {demo_request['submittedAt']}",
                f"Recebido em: {demo_request['receivedAt']}",
                "",
                "Mensagem:",
                demo_request["message"],
            ]
        )
    )

    return message


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
