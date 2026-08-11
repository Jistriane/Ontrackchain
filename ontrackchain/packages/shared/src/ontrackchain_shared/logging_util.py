"""Sprint S28+48 P4: Logging Estruturado JSON (Zero dependências novas).

Shared: stdlib logging + json.dumps + contextvars para request_id.
100% retrocompatível: se não chamar setup_structured_logging → logging default.

Uso em app/main.py FastAPI:
    from ontrackchain_shared.logging_util import (
        setup_structured_logging,
        RequestIdLogMiddleware,
    )
    setup_structured_logging("auth-service", level=os.getenv("LOG_LEVEL", "INFO"))
    app = FastAPI(...)
    app.add_middleware(RequestIdLogMiddleware)
    # depois use: logger.info("evento", extra={"key": "val"})
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from starlette.middleware.base import (
        BaseHTTPMiddleware,
        RequestResponseEndpoint,
    )
    from starlette.requests import Request
    from starlette.responses import Response
    _STARLETTE_OK = True
except Exception:  # pragma: no cover - starlette é importado via FastAPI
    _STARLETTE_OK = False

REQUEST_ID_HEADER = "X-Request-Id"
REQUEST_ID_CTX: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id",
    default=None,
)
_SERVICE_NAME_CTX: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "service_name",
    default=None,
)


class JsonFormatter(logging.Formatter):
    """Formata logs para JSON lines (structlog-like, stdlib only).

    Schema baseado em ECS simplificado + OpenTelemetry log fields.
    NÃO requer dependências extras — apenas json + logging stdlib.
    """

    level_to_severity: dict[str, int] = {
        "DEBUG": 7,
        "INFO": 6,
        "WARNING": 4,
        "WARN": 4,
        "ERROR": 3,
        "CRITICAL": 2,
        "FATAL": 1,
    }

    def __init__(
        self,
        include_exc_text: bool = True,
        service_field: str = "service",
        timestamp_field: str = "timestamp",
        level_field: str = "level",
        message_field: str = "message",
        logger_field: str = "logger",
        request_id_field: str = "request_id",
    ) -> None:
        super().__init__()
        self.include_exc_text = include_exc_text
        self.service_field = service_field
        self.timestamp_field = timestamp_field
        self.level_field = level_field
        self.message_field = message_field
        self.logger_field = logger_field
        self.request_id_field = request_id_field

    @staticmethod
    def _default_serializer(obj: Any) -> Any:
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        try:
            return repr(obj)
        except Exception:  # pragma: no cover
            return f"<non-serializable {type(obj).__name__}>"

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - formatter impl
        # message
        try:
            msg = record.getMessage()
        except Exception:  # pragma: no cover
            msg = str(record.msg)

        # base payload
        payload: dict[str, Any] = {
            self.timestamp_field: datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat().replace("+00:00", "Z"),
            self.level_field: record.levelname,
            "severity": self.level_to_severity.get(record.levelname, 6),
            self.logger_field: record.name,
            self.message_field: msg,
            "_meta": {
                "lineno": record.lineno,
                "funcName": record.funcName,
                "pathname": record.pathname,
                "thread": record.thread,
                "pid": record.process,
            },
        }

        # service field (Filter-based injection + ctx fallback)
        service = getattr(record, "service", None) or _SERVICE_NAME_CTX.get()
        if service:
            payload[self.service_field] = service

        # request_id from contextvar or record.extra
        rid = getattr(record, "request_id", None) or REQUEST_ID_CTX.get()
        if rid:
            payload[self.request_id_field] = rid

        # exception traceback
        if self.include_exc_text and record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
            payload["type"] = "exception"
            payload["exception.type"] = (
                record.exc_info[0].__name__
                if record.exc_info and record.exc_info[0] is not None
                else "Unknown"
            )

        # user provided extras — attribute injection via logger.info(..., extra=...)
        # standard attributes to ignore
        reserved = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process",
            "service", "request_id", "asctime", "message", "taskName",
        }
        extras_from_record = {
            k: v for k, v in record.__dict__.items()
            if k not in reserved and not k.startswith("_")
        }
        if extras_from_record:
            for k, v in extras_from_record.items():
                if k in payload:
                    # record extras override base (except timestamp/level/message service)
                    if k not in (self.timestamp_field, self.level_field, self.message_field):
                        payload[k] = v
                else:
                    payload[k] = v

        # dump JSON (one line = JSON Lines). Fallback ensures serialização sempre OK.
        try:
            return json.dumps(
                payload,
                default=self._default_serializer,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        except (TypeError, ValueError):
            try:
                payload_lite = {
                    self.timestamp_field: payload.get(self.timestamp_field),
                    self.level_field: payload.get(self.level_field),
                    self.logger_field: payload.get(self.logger_field),
                    self.message_field: "[serialization failed] original message dropped",
                    "serialization_error": True,
                    self.service_field: payload.get(self.service_field),
                    self.request_id_field: payload.get(self.request_id_field),
                }
                return json.dumps(payload_lite, ensure_ascii=False, separators=(",", ":"))
            except Exception as last:  # pragma: no cover
                return (
                    f'{{"{self.timestamp_field}":"{time.time()}",'
                    f'"level":"ERROR","message":"JsonFormatter double fault: {last}"}}'
                )


class ServiceInjectionFilter(logging.Filter):
    """Injeta field `service` em todos LogRecord para não precisar repetir."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name
        _SERVICE_NAME_CTX.set(service_name)

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        record.service = self.service_name  # type: ignore[attr-defined]
        rid = REQUEST_ID_CTX.get()
        if rid:
            record.request_id = rid  # type: ignore[attr-defined]
        return True


_STRUCTURED_LOGGING_SETUP_DONE: set[str] = set()


def setup_structured_logging(
    service_name: str,
    level: str | int = logging.INFO,
    stream: Any = sys.stdout,
    json_formatter: Optional[JsonFormatter] = None,
) -> logging.Logger:
    """Configura root logger para JSON estruturado (Sprint S28+48 P4).

    Idempotente: múltiplas chamadas mesmo service_name → ignora 2ª+.
    Não destrói handlers já existentes de dev — apenas adiciona 1 JSON handler,
    e opcionalmente remove default handler print() cru se for stderr stdout.

    Args:
        service_name: nome do microserviço (ex: auth-service, public-api).
        level: nível mínimo de log para JSON handler (INFO default).
        stream: default sys.stdout (container-friendly).
        json_formatter: opcional customizado (para testes ou formatos especiais).

    Returns:
        logging.Logger root logger pré-configurado.
    """
    root_logger = logging.getLogger()
    if service_name in _STRUCTURED_LOGGING_SETUP_DONE:
        return root_logger
    _STRUCTURED_LOGGING_SETUP_DONE.add(service_name)

    if isinstance(level, str):
        level_int = getattr(logging, level.upper(), logging.INFO)
    else:
        level_int = int(level)

    # Cria 1 StreamHandler com JsonFormatter + ServiceInjectionFilter
    # IMPORTANTE: NÃO remove handlers já existentes (evita quebrar uvicorn default)
    handler = logging.StreamHandler(stream)
    handler.setLevel(level_int)
    formatter = json_formatter or JsonFormatter()
    handler.setFormatter(formatter)
    handler.addFilter(ServiceInjectionFilter(service_name))
    handler.set_name(f"structured-{service_name}")

    # Sobe nível root se mais restrito
    if root_logger.level == logging.NOTSET or root_logger.level > level_int:
        root_logger.setLevel(level_int)

    # Evita duplicação handler idêntico (idempotência se filtro pelo nome)
    for existing in list(root_logger.handlers):
        if getattr(existing, "name", None) == handler.name:
            return root_logger
    root_logger.addHandler(handler)
    return root_logger


def get_logger(name: str, **extra_kwargs: Any) -> logging.LoggerAdapter[Any]:
    """Retorna LoggerAdapter com campos extras padrão (use como logging.getLogger).

    Exemplo:
        logger = get_logger(__name__, module="auth.pre_screening")
        logger.info("usuário logado", extra={"user_id": 123})
    """
    base = logging.getLogger(name)
    return logging.LoggerAdapter(base, extra_kwargs)


if _STARLETTE_OK:  # pragma: no branch - se starlette n disponível, skip
    class RequestIdLogMiddleware(BaseHTTPMiddleware):  # type: ignore[misc,valid-type]
        """Middleware FastAPI/Starlette que injeta X-Request-Id em logs + response.

        1. Lê header `X-Request-Id` do request (client ou upstream).
        2. Se ausente: gera uuid4 hex curto.
        3. Seta contextvar REQUEST_ID_CTX → auto-injetado nos logs (via Filter + Formatter).
        4. Devolve response header `X-Request-Id` (client/upstream consegue correlacionar).
        """

        async def dispatch(
            self,
            request: Request,
            call_next: RequestResponseEndpoint,
        ) -> Response:
            incoming = request.headers.get(REQUEST_ID_HEADER, "") or request.headers.get(
                "x-request-id",
                "",
            )
            rid = incoming.strip() or uuid.uuid4().hex
            token = REQUEST_ID_CTX.set(rid)
            try:
                response = await call_next(request)
            finally:
                REQUEST_ID_CTX.reset(token)
            if REQUEST_ID_HEADER not in response.headers:
                response.headers[REQUEST_ID_HEADER] = rid
            return response
else:  # pragma: no cover - fallback: export stub para não crash import
    class RequestIdLogMiddleware:  # type: ignore[no-redef]
        """Fallback: starlette não disponível (ex: scripts CLI). Não crasha importação.

        Starlette middleware não disponível. NÃO É ERRO: módulos sem FastAPI ainda usam
        setup_structured_logging/get_logger normalmente.
        """

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs
            pass  # no-op

        async def __call__(self, *args: Any, **kwargs: Any) -> Any:
            del args, kwargs
            return None
