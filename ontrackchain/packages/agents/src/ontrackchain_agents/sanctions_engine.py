"""
SanctionsEngine — Motor de screening e sincronização de listas de sanções.

Responsabilidades:
  1. SanctionsScreener: screening de endereços contra cache local (< 100ms)
  2. SanctionsSync: workers de sincronização das listas externas via Celery Beat

Fontes de dados (conforme sanctions_lists_meta):
  - OFAC_SDN: sync a cada 6h (TREASURY.GOV)
  - UN_CSNU: sync a cada 24h (scsanctions.un.org)
  - EU_CONSOLIDATED: sync a cada 24h (EU EEAS)
  - COAF_INTERNAL: sync a cada 12h (COAF/FAZENDA)
  - OPENSANCTIONS: sync a cada 24h (api.opensanctions.org — requer API key)

Estratégia de matching:
  1. Busca exata por endereço de carteira (O(1) no cache JSONB+GIN)
  2. Busca full-text no nome da entidade (GIN tsvector 'simple')
  3. Busca por documento (CPF/CNPJ/Passport) nos entity_documents JSONB

Base regulatória:
  - BCB 520 Art. 34 III — controles de listas de sanções
  - BCB 520 Art. 43 §2° V — screening contra CSNU/OFAC/EU
  - Lei 13.810/2019 — cumprimento resoluções CSNU
  - FATF R.6 — Targeted Financial Sanctions
"""

from __future__ import annotations

import hashlib
import json
import logging
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── TIPOS ───────────────────────────────────────────────────────────────────

@dataclass
class ScreeningMatch:
    """Hit individual encontrado no screening."""
    list_name: str
    entity_name: str
    confidence: float        # 0.0 a 1.0
    match_type: str          # "wallet_exact" | "name_fuzzy" | "document_exact"
    sanctions_programs: list[str] = field(default_factory=list)
    designation_date: Optional[str] = None
    regulatory_basis: str = ""


@dataclass
class ScreeningResult:
    """Resultado completo do screening de um endereço."""
    address: str
    chain: str
    has_hit: bool
    hits: list[ScreeningMatch] = field(default_factory=list)
    screened_lists: list[str] = field(default_factory=list)
    screening_duration_ms: int = 0
    screened_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class SyncResult:
    """Resultado de uma operação de sync de lista."""
    list_name: str
    success: bool
    records_added: int = 0
    records_deactivated: int = 0
    source_hash: str = ""
    error_message: str = ""
    synced_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ─── SCREENER ────────────────────────────────────────────────────────────────

class SanctionsScreener:
    """
    Motor de screening de endereços contra o cache local de sanções.

    Usa o banco de dados local (sanctions_hits_cache) — não depende de APIs
    externas em tempo de screening, garantindo < 100ms mesmo com APIs indisponíveis.

    Uso:
        screener = SanctionsScreener(conn)
        result = await screener.screen_address("0x...", "ethereum")
        if result.has_hit:
            # PreventiveBlockAgent avalia o resultado
    """

    # Limiar mínimo de confiança para considerar um hit
    # (abaixo disso o resultado é ignorado para evitar falsos positivos)
    MIN_CONFIDENCE_BY_LIST = {
        "UN_CSNU":         0.90,
        "OFAC_SDN":        0.95,
        "EU_CONSOLIDATED": 0.90,
        "COAF_INTERNAL":   0.90,
        "OPENSANCTIONS":   0.85,
    }

    REGULATORY_BASIS_BY_LIST = {
        "UN_CSNU":         "Lei 13.810/2019 Art. 1° · BCB 520 Art. 43 §2° V",
        "OFAC_SDN":        "BCB 520 Art. 43 §2° V — Lista OFAC/SDN",
        "EU_CONSOLIDATED": "FATF R.6 · BCB 520 Art. 34 III",
        "COAF_INTERNAL":   "BCB 520 Art. 43 §2° V · Lei 9.613/98",
        "OPENSANCTIONS":   "FATF R.6 · BCB 520 Art. 34 III",
    }

    def __init__(self, conn) -> None:
        # conn: psycopg3 connection (síncrono, dentro de with pool.connection())
        self._conn = conn

    @staticmethod
    def _row_value(row, key: str, index: int, default: Any = None) -> Any:
        if isinstance(row, dict):
            return row.get(key, default)
        value = row[index]
        return default if value is None else value

    def screen_address(
        self,
        address: str,
        chain: str,
        entity_name: Optional[str] = None,
        entity_document: Optional[str] = None,
    ) -> ScreeningResult:
        """
        Screening completo em 3 passes:
          1. Wallet exact match (GIN JSONB — mais rápido)
          2. Name full-text match (GIN tsvector — se entity_name fornecido)
          3. Document exact match (se entity_document fornecido)

        Retorna ScreeningResult com todos os hits encontrados.
        """
        import time
        start_ms = time.monotonic() * 1000

        all_hits: list[ScreeningMatch] = []
        screened_lists: list[str] = []

        # ── PASS 1: Wallet exact match ────────────────────────────────────────
        wallet_hits = self._screen_wallet(address.lower(), chain)
        all_hits.extend(wallet_hits)

        # ── PASS 2: Name fuzzy (full-text) ───────────────────────────────────
        if entity_name:
            name_hits = self._screen_name(entity_name)
            # Deduplica: se o mesmo registro já foi encontrado pelo wallet, ignora
            existing_names = {h.entity_name for h in all_hits}
            all_hits.extend(h for h in name_hits if h.entity_name not in existing_names)

        # ── PASS 3: Document exact ────────────────────────────────────────────
        if entity_document:
            doc_hits = self._screen_document(entity_document)
            existing_names = {h.entity_name for h in all_hits}
            all_hits.extend(h for h in doc_hits if h.entity_name not in existing_names)

        # Coleta listas que foram verificadas
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT list_name FROM sanctions_lists_meta WHERE status = 'ACTIVE'"
            )
            screened_lists = [
                str(self._row_value(row, "list_name", 0, ""))
                for row in cur.fetchall()
                if self._row_value(row, "list_name", 0, "")
            ]

        duration_ms = int(time.monotonic() * 1000 - start_ms)

        # Filtra por limiar mínimo de confiança por lista
        qualified_hits = [
            h for h in all_hits
            if h.confidence >= self.MIN_CONFIDENCE_BY_LIST.get(h.list_name, 0.85)
        ]

        return ScreeningResult(
            address=address,
            chain=chain,
            has_hit=len(qualified_hits) > 0,
            hits=qualified_hits,
            screened_lists=screened_lists,
            screening_duration_ms=duration_ms,
        )

    def _screen_wallet(self, address_lower: str, chain: str) -> list[ScreeningMatch]:
        """Busca exata de endereço de carteira no cache JSONB."""
        matches = []
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    shc.list_name,
                    shc.entity_name,
                    shc.sanctions_programs,
                    shc.designation_date
                FROM sanctions_hits_cache shc
                JOIN sanctions_lists_meta slm ON slm.list_name = shc.list_name
                WHERE shc.is_active = TRUE
                  AND slm.status = 'ACTIVE'
                  AND shc.wallet_addresses @> %s::jsonb
                """,
                (json.dumps([{"address": address_lower, "chain": chain}]),),
            )
            for row in cur.fetchall():
                list_name = str(self._row_value(row, "list_name", 0, ""))
                entity_name = str(self._row_value(row, "entity_name", 1, ""))
                sanctions_programs = self._row_value(row, "sanctions_programs", 2) or []
                designation_date = self._row_value(row, "designation_date", 3)
                matches.append(ScreeningMatch(
                    list_name=list_name,
                    entity_name=entity_name,
                    confidence=1.0,          # Match exato = confiança máxima
                    match_type="wallet_exact",
                    sanctions_programs=sanctions_programs,
                    designation_date=str(designation_date) if designation_date else None,
                    regulatory_basis=self.REGULATORY_BASIS_BY_LIST.get(list_name, ""),
                ))
        return matches

    def _screen_name(self, entity_name: str) -> list[ScreeningMatch]:
        """Busca full-text no nome da entidade (GIN tsvector 'simple')."""
        matches = []
        # Quebra o nome em tokens para busca parcial
        tokens = " & ".join(
            w for w in entity_name.split()
            if len(w) >= 3  # Ignora palavras muito curtas (artigos, preposições)
        )
        if not tokens:
            return matches

        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    shc.list_name,
                    shc.entity_name,
                    shc.sanctions_programs,
                    shc.designation_date,
                    ts_rank(shc.entity_name_tsv, to_tsquery('simple', %s)) AS rank
                FROM sanctions_hits_cache shc
                JOIN sanctions_lists_meta slm ON slm.list_name = shc.list_name
                WHERE shc.is_active = TRUE
                  AND slm.status = 'ACTIVE'
                  AND shc.entity_name_tsv @@ to_tsquery('simple', %s)
                ORDER BY rank DESC
                LIMIT 10
                """,
                (tokens, tokens),
            )
            for row in cur.fetchall():
                # Converte o rank do postgres (0.0-1.0) em confiança
                list_name = str(self._row_value(row, "list_name", 0, ""))
                entity_name = str(self._row_value(row, "entity_name", 1, ""))
                sanctions_programs = self._row_value(row, "sanctions_programs", 2) or []
                designation_date = self._row_value(row, "designation_date", 3)
                rank = self._row_value(row, "rank", 4, 0.0)
                confidence = min(0.50 + float(rank) * 0.45, 0.95)
                matches.append(ScreeningMatch(
                    list_name=list_name,
                    entity_name=entity_name,
                    confidence=confidence,
                    match_type="name_fuzzy",
                    sanctions_programs=sanctions_programs,
                    designation_date=str(designation_date) if designation_date else None,
                    regulatory_basis=self.REGULATORY_BASIS_BY_LIST.get(list_name, ""),
                ))
        return matches

    def _screen_document(self, document: str) -> list[ScreeningMatch]:
        """Busca exata de documento (CPF/CNPJ/Passport) no cache JSONB."""
        matches = []
        doc_clean = document.replace(".", "").replace("-", "").replace("/", "").strip()

        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    shc.list_name,
                    shc.entity_name,
                    shc.sanctions_programs,
                    shc.designation_date
                FROM sanctions_hits_cache shc
                JOIN sanctions_lists_meta slm ON slm.list_name = shc.list_name
                WHERE shc.is_active = TRUE
                  AND slm.status = 'ACTIVE'
                  AND EXISTS (
                    SELECT 1
                    FROM jsonb_array_elements(shc.entity_documents) doc
                    WHERE doc->>'number' = %s
                      OR replace(replace(replace(doc->>'number', '.', ''), '-', ''), '/', '') = %s
                  )
                """,
                (doc_clean, doc_clean),
            )
            for row in cur.fetchall():
                list_name = str(self._row_value(row, "list_name", 0, ""))
                entity_name = str(self._row_value(row, "entity_name", 1, ""))
                sanctions_programs = self._row_value(row, "sanctions_programs", 2) or []
                designation_date = self._row_value(row, "designation_date", 3)
                matches.append(ScreeningMatch(
                    list_name=list_name,
                    entity_name=entity_name,
                    confidence=1.0,          # Match exato de documento = confiança máxima
                    match_type="document_exact",
                    sanctions_programs=sanctions_programs,
                    designation_date=str(designation_date) if designation_date else None,
                    regulatory_basis=self.REGULATORY_BASIS_BY_LIST.get(list_name, ""),
                ))
        return matches


# ─── SYNC WORKERS ────────────────────────────────────────────────────────────

class SanctionsSyncWorker:
    """
    Worker de sincronização das listas de sanções.

    Cada método de sync é chamado pelo Celery Beat na frequência configurada
    em sanctions_lists_meta.

    Estratégia de upsert:
      1. Download da fonte externa
      2. Calcula SHA-256 do arquivo — se igual ao last_sync_hash, skip (sem mudanças)
      3. Marca todos os registros da lista como is_active=FALSE
      4. INSERT dos novos registros
      5. Atualiza sanctions_lists_meta com status e timestamp
    """

    def __init__(self, conn) -> None:
        self._conn = conn

    DEFAULT_OFAC_SDN_URLS = (
        "https://sanctionslistservice.ofac.treas.gov/api/download/SDN_ADVANCED.XML",
        "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN_ADVANCED.XML",
        "https://sanctionslistservice.ofac.treas.gov/api/download/SDN.XML",
    )

    DEFAULT_EU_CONSOLIDATED_URLS = (
        "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content",
        "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content",
    )

    # ── OFAC SDN ─────────────────────────────────────────────────────────────

    def sync_ofac_sdn(self) -> SyncResult:
        """
        Sincroniza OFAC SDN (Specially Designated Nationals).
        Fonte: https://www.treasury.gov/ofac/downloads/sdn_advanced.xml
        Frequência: 6h (configurado em sanctions_lists_meta)
        """
        list_name = "OFAC_SDN"

        try:
            raw, _ = self._download_with_fallback(
                list_name,
                self._candidate_urls(list_name, self.DEFAULT_OFAC_SDN_URLS),
                timeout=60,
            )
        except Exception as exc:
            return self._fail(list_name, f"Download falhou: {exc}")

        source_hash = hashlib.sha256(raw).hexdigest()

        # Skip se arquivo não mudou desde o último sync
        if self._is_same_hash(list_name, source_hash):
            logger.info("sanctions_sync.ofac_sdn.skip_unchanged")
            return self._skip(list_name, source_hash)

        try:
            root = ET.fromstring(raw.decode("utf-8"))

            entries = []
            for entry in self._iter_descendants(root, "sdnEntry"):
                uid = self._findtext_descendant(entry, "uid")
                first = self._findtext_descendant(entry, "firstName")
                last = self._findtext_descendant(entry, "lastName")
                full_name = f"{first} {last}".strip() or f"OFAC-{uid}"
                entity_type = self._findtext_descendant(entry, "sdnType") or "INDIVIDUAL"

                aliases = [
                    self._findtext_descendant(alias, "wholeName")
                    or self._findtext_descendant(alias, "aka")
                    or ""
                    for alias in self._iter_descendants(entry, "aka")
                ]
                aliases = [a for a in aliases if a]

                programs = [
                    (program.text or "").strip()
                    for program in self._iter_descendants(entry, "program")
                ]
                programs = [p for p in programs if p]

                entries.append({
                    "list_name": list_name,
                    "entity_type": self._normalize_entity_type(entity_type),
                    "entity_name": full_name,
                    "entity_aliases": aliases,
                    "entity_documents": [],
                    "wallet_addresses": [],
                    "sanctions_programs": programs,
                    "source_entity_id": uid,
                })

        except ET.ParseError as exc:
            return self._fail(list_name, f"Parse XML falhou: {exc}")

        return self._upsert_entries(list_name, entries, source_hash)

    # ── UN CSNU ──────────────────────────────────────────────────────────────

    def sync_un_csnu(self) -> SyncResult:
        """
        Sincroniza Lista Consolidada CSNU (ONU).
        Fonte: https://scsanctions.un.org/resources/xml/en/consolidated.xml
        Frequência: 24h
        Base: Lei 13.810/2019 Art. 1° — cumprimento imediato de resoluções CSNU
        """
        list_name = "UN_CSNU"
        url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"

        try:
            raw = self._download(url, timeout=45)
        except Exception as exc:
            return self._fail(list_name, f"Download falhou: {exc}")

        source_hash = hashlib.sha256(raw).hexdigest()
        if self._is_same_hash(list_name, source_hash):
            logger.info("sanctions_sync.un_csnu.skip_unchanged")
            return self._skip(list_name, source_hash)

        try:
            root = ET.fromstring(raw.decode("utf-8"))
            entries = []

            for individual in root.findall(".//INDIVIDUAL"):
                uid = individual.findtext("DATAID") or ""
                first = individual.findtext("FIRST_NAME") or ""
                second = individual.findtext("SECOND_NAME") or ""
                third = individual.findtext("THIRD_NAME") or ""
                full_name = " ".join(p for p in [first, second, third] if p).strip()
                if not full_name:
                    full_name = f"UN-IND-{uid}"

                aliases = []
                for alias in individual.findall(".//ALIAS"):
                    a_name = " ".join(p for p in [
                        alias.findtext("FIRST_NAME") or "",
                        alias.findtext("SECOND_NAME") or "",
                        alias.findtext("THIRD_NAME") or "",
                    ] if p).strip()
                    if a_name:
                        aliases.append(a_name)

                entries.append({
                    "list_name": list_name,
                    "entity_type": "INDIVIDUAL",
                    "entity_name": full_name,
                    "entity_aliases": aliases,
                    "entity_documents": [],
                    "wallet_addresses": [],
                    "sanctions_programs": ["UN_CSNU"],
                    "source_entity_id": uid,
                })

            for entity in root.findall(".//ENTITY"):
                uid = entity.findtext("DATAID") or ""
                name = entity.findtext("FIRST_NAME") or f"UN-ENT-{uid}"

                aliases = []
                for alias in entity.findall(".//ALIAS"):
                    a_name = alias.findtext("ALIAS_NAME") or alias.findtext("FIRST_NAME") or ""
                    if a_name:
                        aliases.append(a_name)

                entries.append({
                    "list_name": list_name,
                    "entity_type": "ORGANIZATION",
                    "entity_name": name,
                    "entity_aliases": aliases,
                    "entity_documents": [],
                    "wallet_addresses": [],
                    "sanctions_programs": ["UN_CSNU"],
                    "source_entity_id": uid,
                })

        except ET.ParseError as exc:
            return self._fail(list_name, f"Parse XML falhou: {exc}")

        return self._upsert_entries(list_name, entries, source_hash)

    # ── EU CONSOLIDATED ───────────────────────────────────────────────────────

    def sync_eu_consolidated(self) -> SyncResult:
        """
        Sincroniza EU Consolidated Financial Sanctions List.
        Frequência: 24h
        Base: FATF R.6 · BCB 520 Art. 34 III
        """
        list_name = "EU_CONSOLIDATED"

        try:
            raw, _ = self._download_with_fallback(
                list_name,
                self._candidate_urls(list_name, self.DEFAULT_EU_CONSOLIDATED_URLS),
                timeout=45,
            )
        except Exception as exc:
            return self._fail(list_name, f"Download falhou: {exc}")

        source_hash = hashlib.sha256(raw).hexdigest()
        if self._is_same_hash(list_name, source_hash):
            logger.info("sanctions_sync.eu_consolidated.skip_unchanged")
            return self._skip(list_name, source_hash)

        try:
            root = ET.fromstring(raw.decode("utf-8"))
            entries = []

            for subject in self._iter_descendants(root, "sanctionEntity"):
                uid = subject.get("euReferenceNumber") or subject.get("logicalId") or ""
                subject_type = subject.get("subjectType") or "person"

                # Nome principal
                name_aliases = list(self._iter_descendants(subject, "nameAlias"))
                name_elem = next(
                    (alias for alias in name_aliases if (alias.get("mainEntry") or "").lower() == "true"),
                    None,
                )
                if name_elem is None and name_aliases:
                    name_elem = name_aliases[0]

                main_name = ""
                if name_elem is not None:
                    parts = [
                        name_elem.get("firstName") or "",
                        name_elem.get("middleName") or "",
                        name_elem.get("lastName") or "",
                        name_elem.get("wholeName") or "",
                    ]
                    main_name = " ".join(p for p in parts if p).strip()

                if not main_name:
                    main_name = f"EU-{uid}"

                # Aliases
                aliases = []
                for alias in name_aliases:
                    if alias is name_elem:
                        continue
                    whole = alias.get("wholeName") or ""
                    parts = [
                        alias.get("firstName") or "",
                        alias.get("lastName") or "",
                    ]
                    a_name = whole or " ".join(p for p in parts if p).strip()
                    if a_name:
                        aliases.append(a_name)

                # Programas (regulations)
                programs = []
                for reg in self._iter_descendants(subject, "regulation"):
                    prog = reg.get("programme") or reg.get("publicationTitle") or ""
                    if prog:
                        programs.append(prog)

                entries.append({
                    "list_name": list_name,
                    "entity_type": self._normalize_entity_type(subject_type),
                    "entity_name": main_name,
                    "entity_aliases": aliases,
                    "entity_documents": [],
                    "wallet_addresses": [],
                    "sanctions_programs": programs or ["EU_SANCTIONS"],
                    "source_entity_id": uid,
                })

        except ET.ParseError as exc:
            return self._fail(list_name, f"Parse XML falhou: {exc}")

        return self._upsert_entries(list_name, entries, source_hash)

    # ── OPENSANCTIONS (requer API key) ────────────────────────────────────────

    def sync_opensanctions(self, api_key: str) -> SyncResult:
        """
        Sincroniza OpenSanctions (base consolidada internacional).
        Requer OPENSANCTIONS_API_KEY.
        Frequência: 24h
        """
        list_name = "OPENSANCTIONS"

        if not api_key:
            return self._fail(
                list_name,
                "OPENSANCTIONS_API_KEY não configurada — "
                "configure o secret e altere status para ACTIVE em sanctions_lists_meta"
            )

        url = "https://api.opensanctions.org/entities/_all?schema=LegalEntity&limit=10000"
        headers = {"Authorization": f"ApiKey {api_key}"}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
        except Exception as exc:
            return self._fail(list_name, f"Download OpenSanctions falhou: {exc}")

        source_hash = hashlib.sha256(raw).hexdigest()
        if self._is_same_hash(list_name, source_hash):
            return self._skip(list_name, source_hash)

        try:
            data = json.loads(raw.decode("utf-8"))
            entries = []

            for entity in (data.get("results") or data.get("entities") or []):
                props = entity.get("properties") or {}
                name_list = props.get("name") or props.get("alias") or []
                main_name = name_list[0] if name_list else f"OS-{entity.get('id','?')}"
                aliases = name_list[1:] if len(name_list) > 1 else []

                # Wallets crypto
                wallets = []
                for addr in (props.get("cryptoWallet") or []):
                    wallets.append({"chain": "unknown", "address": addr.lower()})

                entries.append({
                    "list_name": list_name,
                    "entity_type": "INDIVIDUAL" if entity.get("schema") == "Person"
                                   else "ORGANIZATION",
                    "entity_name": main_name,
                    "entity_aliases": aliases,
                    "entity_documents": [],
                    "wallet_addresses": wallets,
                    "sanctions_programs": props.get("program") or ["OPENSANCTIONS"],
                    "source_entity_id": entity.get("id") or "",
                })

        except (json.JSONDecodeError, KeyError) as exc:
            return self._fail(list_name, f"Parse OpenSanctions falhou: {exc}")

        return self._upsert_entries(list_name, entries, source_hash)

    # ── HELPERS INTERNOS ──────────────────────────────────────────────────────

    def _download(self, url: str, timeout: int = 30) -> bytes:
        """Download simples com urllib (sem dependências extras)."""
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "OnTrackChain-SanctionsSync/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()

    def _candidate_urls(self, list_name: str, default_urls: tuple[str, ...]) -> list[str]:
        urls: list[str] = []
        configured_url = self._get_source_url(list_name)
        if configured_url:
            urls.append(configured_url)
        urls.extend(default_urls)

        unique_urls: list[str] = []
        seen: set[str] = set()
        for url in urls:
            normalized = (url or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_urls.append(normalized)
        return unique_urls

    def _download_with_fallback(
        self,
        list_name: str,
        urls: list[str],
        *,
        timeout: int,
    ) -> tuple[bytes, str]:
        attempts: list[str] = []
        had_403 = False

        for url in urls:
            try:
                raw = self._download(url, timeout=timeout)
            except urllib.error.HTTPError as exc:
                if exc.code == 403:
                    had_403 = True
                attempts.append(f"{url} -> HTTP {exc.code}")
                continue
            except urllib.error.URLError as exc:
                attempts.append(f"{url} -> URL error: {exc.reason}")
                continue
            except Exception as exc:
                attempts.append(f"{url} -> {type(exc).__name__}: {exc}")
                continue

            if not self._looks_like_xml(raw):
                attempts.append(f"{url} -> payload nao parece XML")
                continue

            self._persist_working_source_url(list_name, url)
            return raw, url

        detail = "; ".join(attempts) if attempts else "nenhum endpoint configurado"
        if list_name == "EU_CONSOLIDATED" and had_403:
            detail += (
                " | O portal da UE rejeitou os endpoints publicos. "
                "Atualize `sanctions_lists_meta.source_url` com a URL XML tokenizada "
                "obtida em `https://webgate.ec.europa.eu/fsd/fsf#!/files`."
            )
        raise RuntimeError(detail)

    @staticmethod
    def _looks_like_xml(raw: bytes) -> bool:
        prefix = raw[:4096].decode("utf-8", errors="ignore").lstrip().lower()
        if not prefix:
            return False
        if "<html" in prefix or "<!doctype html" in prefix:
            return False
        return prefix.startswith("<?xml") or prefix.startswith("<")

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1] if "}" in tag else tag

    @classmethod
    def _iter_descendants(cls, root: ET.Element, element_name: str):
        for element in root.iter():
            if cls._local_name(element.tag) == element_name:
                yield element

    @classmethod
    def _findtext_descendant(cls, root: ET.Element, element_name: str) -> str:
        for element in cls._iter_descendants(root, element_name):
            if element.text:
                return element.text.strip()
        return ""

    @staticmethod
    def _normalize_entity_type(entity_type: str) -> str:
        normalized = (entity_type or "").strip().lower()
        if normalized in {"individual", "person"}:
            return "INDIVIDUAL"
        if normalized in {"vessel", "ship"}:
            return "VESSEL"
        if normalized in {"aircraft", "plane"}:
            return "AIRCRAFT"
        return "ORGANIZATION"

    def _get_source_url(self, list_name: str) -> Optional[str]:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT source_url FROM sanctions_lists_meta WHERE list_name = %s",
                    (list_name,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                if isinstance(row, dict):
                    return row.get("source_url")
                return row[0]
        except Exception:
            return None

    def _persist_working_source_url(self, list_name: str, source_url: str) -> None:
        current_source_url = self._get_source_url(list_name)
        if current_source_url == source_url:
            return
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE sanctions_lists_meta
                    SET source_url = %s,
                        updated_at = NOW()
                    WHERE list_name = %s
                    """,
                    (source_url, list_name),
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()

    def _is_same_hash(self, list_name: str, new_hash: str) -> bool:
        """Verifica se o arquivo baixado é idêntico ao último sync."""
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT last_sync_hash FROM sanctions_lists_meta WHERE list_name = %s",
                    (list_name,),
                )
                row = cur.fetchone()
                if not row:
                    return False
                last_sync_hash = row.get("last_sync_hash") if isinstance(row, dict) else row[0]
                return bool(last_sync_hash == new_hash)
        except Exception:
            return False

    def _skip(self, list_name: str, source_hash: str) -> SyncResult:
        """Registra skip (sem mudanças) na meta-tabela."""
        with self._conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sanctions_lists_meta
                SET last_sync_at = NOW(),
                    last_sync_status = 'SUCCESS',
                    last_sync_hash = %s,
                    next_sync_at = NOW() + (sync_interval_hours || ' hours')::interval,
                    updated_at = NOW()
                WHERE list_name = %s
                """,
                (source_hash, list_name),
            )
        self._conn.commit()
        return SyncResult(list_name=list_name, success=True,
                          records_added=0, source_hash=source_hash)

    def _fail(self, list_name: str, error: str) -> SyncResult:
        """Registra falha de sync na meta-tabela."""
        logger.error("sanctions_sync.failed", extra={"list": list_name, "error": error})
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE sanctions_lists_meta
                    SET last_sync_at = NOW(),
                        last_sync_status = 'FAILED',
                        status_reason = %s,
                        next_sync_at = NOW() + INTERVAL '1 hour',
                        updated_at = NOW()
                    WHERE list_name = %s
                    """,
                    (error[:500], list_name),
                )
            self._conn.commit()
        except Exception:
            pass
        return SyncResult(list_name=list_name, success=False, error_message=error)

    def _upsert_entries(
        self,
        list_name: str,
        entries: list[dict],
        source_hash: str,
    ) -> SyncResult:
        """
        Upsert completo da lista:
          1. Desativa registros antigos (is_active=FALSE)
          2. INSERT dos novos registros
          3. Atualiza sanctions_lists_meta
        """
        added = 0
        try:
            with self._conn.cursor() as cur:
                # Desativa todos os registros antigos desta lista
                cur.execute(
                    "UPDATE sanctions_hits_cache SET is_active = FALSE WHERE list_name = %s",
                    (list_name,),
                )

                # INSERT dos novos registros
                for entry in entries:
                    cur.execute(
                        """
                        INSERT INTO sanctions_hits_cache (
                            list_name, entity_type, entity_name, entity_aliases,
                            entity_documents, wallet_addresses, sanctions_programs,
                            source_entity_id, synced_at, is_active
                        )
                        VALUES (
                            %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, NOW(), TRUE
                        )
                        ON CONFLICT (list_name, source_entity_id)
                        DO UPDATE SET
                            entity_name = EXCLUDED.entity_name,
                            entity_aliases = EXCLUDED.entity_aliases,
                            entity_documents = EXCLUDED.entity_documents,
                            wallet_addresses = EXCLUDED.wallet_addresses,
                            sanctions_programs = EXCLUDED.sanctions_programs,
                            synced_at = NOW(),
                            is_active = TRUE
                        WHERE sanctions_hits_cache.source_entity_id IS NOT NULL
                        """,
                        (
                            entry["list_name"],
                            entry["entity_type"],
                            entry["entity_name"],
                            json.dumps(entry["entity_aliases"]),
                            json.dumps(entry["entity_documents"]),
                            json.dumps(entry["wallet_addresses"]),
                            entry["sanctions_programs"],
                            entry["source_entity_id"] or None,
                        ),
                    )
                    added += 1

                # Atualiza meta-tabela
                cur.execute(
                    """
                    UPDATE sanctions_lists_meta
                    SET last_sync_at = NOW(),
                        last_sync_status = 'SUCCESS',
                        last_sync_record_count = %s,
                        last_sync_hash = %s,
                        next_sync_at = NOW() + (sync_interval_hours || ' hours')::interval,
                        status = 'ACTIVE',
                        status_reason = NULL,
                        updated_at = NOW()
                    WHERE list_name = %s
                    """,
                    (added, source_hash, list_name),
                )

            self._conn.commit()
            logger.info(
                "sanctions_sync.completed",
                extra={"list": list_name, "added": added},
            )

        except Exception as exc:
            self._conn.rollback()
            return self._fail(list_name, f"Upsert falhou: {exc}")

        return SyncResult(
            list_name=list_name,
            success=True,
            records_added=added,
            source_hash=source_hash,
        )
