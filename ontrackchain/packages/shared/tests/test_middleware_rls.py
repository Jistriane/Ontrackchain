"""Shared v1.1 — Testes Sprint28+22 (P0.2 backlog independente PGP)

Módulo sob teste: ontrackchain_shared.middleware_rls (260 linhas, FastAPI RLS middleware)
Cobertura: 80%+ funções públicas sem precisar de conexão PG real
  ✅ DEFAULT_BYPASS_RLS_PATHS contém healthz / metrics / docs
  ✅ DEFAULT_BYPASS_RLS_PREFIXES contém /public/ /auth/ etc.
  ✅ path_needs_rls_context() bypass paths / bypass prefixes / rotas reais retorna True
  ✅ _is_valid_uuid() UUID válido / None / empty / string inválida
  ✅ extract_org_id_from_headers() Dict-style headers + UUID case-insensitive header name
  ✅ extract_org_id_from_jwt_payload() dict / str org_id / lista / claim keys 4 variantes
  ✅ apply_rls_context_on_connection RuntimeError se conn=None
  ✅ apply_rls_context_on_async_connection RuntimeError se async_conn=None
  ✅ make_rls_context_middleware retorna callable async
  ✅ register_rls_context_middleware não quebra em app FastAPI vazio (não conecta PG)
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI

from ontrackchain_shared.middleware_rls import (
    DEFAULT_BYPASS_RLS_PATHS,
    DEFAULT_BYPASS_RLS_PREFIXES,
    UUID_RE,
    _is_valid_uuid,
    apply_rls_context_on_async_connection,
    apply_rls_context_on_connection,
    extract_org_id_from_headers,
    extract_org_id_from_jwt_payload,
    make_rls_context_middleware,
    path_needs_rls_context,
    register_rls_context_middleware,
)

SAMPLE_UUID = "550e8400-e29b-41d4-a716-446655440000"


class TestBypassConstants:
    def test_healthz_metrics_in_bypass_paths(self):
        for p in ("/healthz", "/metrics", "/openapi.json", "/docs"):
            assert p in DEFAULT_BYPASS_RLS_PATHS

    def test_public_auth_in_bypass_prefixes(self):
        for p in ("/public/", "/auth/", "/static/"):
            assert p in DEFAULT_BYPASS_RLS_PREFIXES


class TestPathNeedsRlsContext:
    def test_bypass_path_returns_false(self):
        assert path_needs_rls_context("/healthz") is False
        assert path_needs_rls_context("/metrics") is False
        assert path_needs_rls_context("/") is False

    def test_bypass_prefix_returns_false(self):
        assert path_needs_rls_context("/public/v1/quote") is False
        assert path_needs_rls_context("/auth/sso/login") is False
        assert path_needs_rls_context("/openapi.json") is False

    def test_empty_path_returns_false(self):
        assert path_needs_rls_context("") is False

    def test_real_route_needs_context(self):
        assert path_needs_rls_context("/api/v1/investigations/") is True
        assert path_needs_rls_context("/compliance/cases/123") is True


class TestIsValidUuid:
    def test_none_invalid(self):
        assert _is_valid_uuid(None) is False

    def test_empty_invalid(self):
        assert _is_valid_uuid("") is False
        assert _is_valid_uuid("  ") is False

    def test_sample_uuid_valid_lowercase(self):
        assert _is_valid_uuid(SAMPLE_UUID) is True

    def test_sample_uuid_valid_uppercase(self):
        assert _is_valid_uuid(SAMPLE_UUID.upper()) is True

    def test_uuid_without_dashes_accepted_by_uuid_call(self):
        # UUID("550e8400e29b41d4a716446655440000") é aceito, então _is_valid_uuid retorna True
        assert _is_valid_uuid("550e8400e29b41d4a716446655440000") is True

    def test_garbage_invalid(self):
        assert _is_valid_uuid("not-a-uuid") is False

    def test_uuid_regex_pattern(self):
        # SAMPLE_UUID bate regex
        assert UUID_RE.match(SAMPLE_UUID) is not None


class TestExtractOrgIdFromHeaders:
    def test_dict_with_exact_header(self):
        h: dict[str, Any] = {"X-Organization-Id": SAMPLE_UUID}
        assert extract_org_id_from_headers(h) == SAMPLE_UUID

    def test_dict_case_insensitive_fallback(self):
        h = {"x-organization-id": SAMPLE_UUID}
        assert extract_org_id_from_headers(h) == SAMPLE_UUID

    def test_uuid_normalized_lowercase(self):
        h = {"X-Organization-Id": SAMPLE_UUID.upper()}
        out = extract_org_id_from_headers(h)
        assert out == SAMPLE_UUID  # str(uuid.UUID(...)) normaliza pra lowercase

    def test_missing_header_returns_none(self):
        assert extract_org_id_from_headers({}) is None

    def test_invalid_uuid_returns_none(self):
        h = {"X-Organization-Id": "not-uuid"}
        assert extract_org_id_from_headers(h) is None


class TestExtractOrgIdFromJwtPayload:
    def test_organization_id_claim(self):
        payload = {"organization_id": SAMPLE_UUID}
        assert extract_org_id_from_jwt_payload(payload) == SAMPLE_UUID

    def test_tenant_id_claim(self):
        payload = {"tenant_id": SAMPLE_UUID}
        assert extract_org_id_from_jwt_payload(payload) == SAMPLE_UUID

    def test_org_id_inside_list_picks_first(self):
        payload = {"org_id": [SAMPLE_UUID, "other"]}
        assert extract_org_id_from_jwt_payload(payload) == SAMPLE_UUID

    def test_payload_not_dict(self):
        assert extract_org_id_from_jwt_payload(None) is None
        assert extract_org_id_from_jwt_payload([]) is None  # type: ignore[arg-type]

    def test_no_known_key(self):
        assert extract_org_id_from_jwt_payload({"sub": "x"}) is None


class TestApplyRlsConnection:
    def test_sync_conn_none_raises_runtime(self):
        with pytest.raises(RuntimeError):
            apply_rls_context_on_connection(None, SAMPLE_UUID)

    @pytest.mark.asyncio
    async def test_async_conn_none_raises_runtime(self):
        with pytest.raises(RuntimeError):
            await apply_rls_context_on_async_connection(None, SAMPLE_UUID)


class TestMiddlewareFactory:
    def test_make_middleware_returns_callable(self):
        mw = make_rls_context_middleware()
        assert callable(mw)

    def test_register_middleware_no_pool_no_app_state_pool_survives(self):
        """Apenas garantir que chamar register_rls_context_middleware em app vazio
        não levanta exceção (ele cria a classe BaseHTTPMiddleware e registra)."""
        app = FastAPI()
        try:
            register_rls_context_middleware(app)
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"register_rls_context_middleware raised unexpectedly: {exc}")
        # pelo menos 1 middleware adicionado (não testamos a execução pois precisaria de pool PG)
        assert len(app.user_middleware) >= 1
