"""
PreventivePreScreening — Stage 1 do sistema de bloqueio preventivo.

Executado como ForwardAuth pelo Traefik ANTES do auth principal.
Verifica a blocklist Redis de endereços confirmados pelo Stage 2 (backend).

Arquitetura de 2 estágios:
  Stage 1 (este módulo): Redis lookup O(1), < 50ms
    - Verifica hits OFAC confirmados (≥0.95 confiança) pré-carregados no Redis
    - Bloqueados pelo PreventiveBlockAgent e sincronizados pelo SanctionsAgent
    - Retorna HTTP 451 (RFC 7725 — Unavailable For Legal Reasons) para hits
    - NÃO registra na evidence_trail (Stage 2 faz isso com contexto completo)

  Stage 2 (preventive_block.py): Decisão completa, < 500ms
    - Score AML, todas as listas, KYW Framework
    - Registra na evidence_trail (auditável para BCB)

Integração com Traefik:
  O Traefik chama /validate com o request original.
  Se o pre-screening detectar um bloqueio, retorna 403 (Traefik interpreta como bloqueio).
  O corpo do response de 403 inclui os headers X-Block-* para diagnóstico.
  Requests limpos passam com 200 + headers padrão de auth.

Base regulatória:
  - BCB 520 Art. 43 §2° V: listas de sanções (CSNU, OFAC)
  - Lei 13.810/2019: indisponibilidade imediata para hits CSNU
  - Lei 9.613/98 Art. 11: vedação à continuidade de operação suspeita
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Request, Response

logger = logging.getLogger(__name__)

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────

# Prefixo das keys na blocklist Redis
# Formato: otk:blocklist:confirmed:{chain}
# Populado por: PreventiveBlockAgent._update_redis_blocklist()
# Sincronizado por: SanctionsAgent (sync OFAC a cada 6h)
REDIS_BLOCKLIST_PREFIX = "otk:blocklist:confirmed"

# Chains suportadas no pre-screening
SUPPORTED_CHAINS = {
    "ethereum", "polygon", "bsc", "arbitrum", "base",
    "optimism", "bitcoin", "solana", "stellar",
}

# Padrões de extração de endereço de carteira da URL/body da request
# Evita parsear o body completo (latência) — só extrai da URL quando possível
ADDRESS_PATTERNS = [
    # EVM: 0x + 40 hex chars
    re.compile(r"/(0x[0-9a-fA-F]{40})(?:/|$|\?)", re.IGNORECASE),
    # Bitcoin bech32: bc1...
    re.compile(r"/(bc1[0-9a-z]{25,90})(?:/|$|\?)", re.IGNORECASE),
    # Bitcoin legacy: 1... ou 3...
    re.compile(r"/([13][1-9A-HJ-NP-Za-km-z]{25,34})(?:/|$|\?)", re.IGNORECASE),
    # Stellar: G + 55 base32 chars
    re.compile(r"/(G[A-Z2-7]{55})(?:/|$|\?)", re.IGNORECASE),
    # Solana: base58 43-44 chars
    re.compile(r"/([1-9A-HJ-NP-Za-km-z]{43,44})(?:/|$|\?)", re.IGNORECASE),
]

# Header com chain da request (definido pelo client ou pelo Traefik rule)
CHAIN_HEADER = "X-Chain"
DEFAULT_CHAIN = "ethereum"


def extract_address_from_path(path: str) -> Optional[str]:
    """
    Extrai endereço de carteira da URL da request.
    Testa padrões em ordem de prioridade (EVM primeiro, mais comum).
    Retorna None se nenhum padrão encontrar endereço válido.
    """
    for pattern in ADDRESS_PATTERNS:
        match = pattern.search(path)
        if match:
            return match.group(1)
    return None


async def pre_screen_blocklist(
    request: Request,
    redis_client: aioredis.Redis,
) -> Optional[Response]:
    """
    Stage 1: Pre-screening da blocklist Redis.

    Chamado pelo endpoint /validate antes da validação de JWT/OIDC.
    Retorna None se o endereço não está bloqueado (request passa).
    Retorna Response HTTP 451 se o endereço está na blocklist.

    Latência alvo: < 50ms (Redis O(1) SISMEMBER).

    IMPORTANTE: Este stage NÃO registra na evidence_trail.
    O Stage 2 (PreventiveBlockAgent no backend) registra o contexto completo
    quando a transação é processada.
    """
    path = request.url.path
    chain = request.headers.get(CHAIN_HEADER, DEFAULT_CHAIN).lower()

    if chain not in SUPPORTED_CHAINS:
        chain = DEFAULT_CHAIN

    address = extract_address_from_path(path)
    if not address:
        # Não há endereço de carteira na URL — pre-screening não se aplica
        # O Stage 2 (backend) avalia endereços do body quando necessário
        return None

    address_lower = address.lower()
    redis_key = f"{REDIS_BLOCKLIST_PREFIX}:{chain}"

    try:
        is_blocked = await redis_client.sismember(redis_key, address_lower)
    except Exception as exc:
        # Falha no Redis NÃO bloqueia a request — fail-open intencional
        # Stage 2 (backend) avalia com latência maior mas com contexto completo
        logger.error(
            "pre_screen.redis_error",
            extra={
                "error": str(exc),
                "address": address_lower,
                "chain": chain,
                "action": "FAIL_OPEN — Stage 2 avaliará",
            },
        )
        return None

    if not is_blocked:
        return None

    request_id = request.headers.get("X-Request-Id", "")

    logger.warning(
        "pre_screen.blocklist_hit",
        extra={
            "address": address_lower,
            "chain": chain,
            "request_id": request_id,
            "stage": "gateway_stage1",
        },
    )

    # HTTP 451 — Unavailable For Legal Reasons (RFC 7725)
    # O Traefik trata qualquer resposta não-2xx do ForwardAuth como bloqueio
    # e retorna 403 ao client com os headers de diagnóstico
    return Response(
        status_code=451,
        content=b"address_blocked_legal",
        headers={
            "X-Block-Stage": "gateway_pre_screening",
            "X-Block-Reason": "sanctions_list_confirmed",
            "X-Block-Chain": chain,
            # NÃO inclui qual lista específica (segurança operacional)
            # NÃO inclui o endereço bloqueado (evita confirmação a atacantes)
            "X-Request-Id": request_id,
            "X-Regulatory-Basis": "BCB 520 Art. 43-2-V | Lei 13.810/2019",
            "X-Stage2-Required": "true",  # Sinaliza que Stage 2 deve registrar
        },
    )
