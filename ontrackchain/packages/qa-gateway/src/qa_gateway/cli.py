"""
qa-gateway CLI (console entry-point: `qa-gateway <command> <args>`).

Documentado em ADR-018 qa-gateway-ssot-rls-shared-first-fallback-inline.md

Comandos implementados (MVP):
  - qa-gateway scan rls --db-url $DATABASE_URL   [Faz scan TABELAS x RLS+POLICY+INDEX]
  - qa-gateway health --endpoints <file.txt|comma-sep>  [Health check paralelo]
  - qa-gateway scan lgpd --dump-file /tmp/db.sql  [Varre CPF plaintext + chaves privadas]

(Próximos comandos pós Sprint 2): scan sla, report summary, ci-comment-json.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, List, NamedTuple, Optional

import click
import psycopg
import requests

from .rls import TABLES_EXPECTED_TO_HAVE_ORG_ID, assert_tables_have_rls, scan_all_rls_tables


CPF_REGEX = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
PRIVATE_KEY_REGEXES = [
    re.compile(r"-----BEGIN (RSA|EC|OPENSSH|ED25519|DSA|PGP) PRIVATE KEY-----"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
]

DEFAULT_HTTP_TIMEOUT = 5.0


# ---------------------------------------------------------------------
# Helper: Exit Code rigoroso (0 = sucesso, 1 = scan detectou problema,
# 2 = erro conexão/infra, 3 = parametro inválido, 4 = arquivo não existe)
# ---------------------------------------------------------------------
def _exit_report(all_ok: bool, issues: list[str], failures_json_path: Optional[str] = None) -> None:
    if failures_json_path:
        try:
            Path(failures_json_path).write_text(
                json.dumps(
                    {"ok": all_ok, "issues": issues, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:  # noqa: BLE001
            pass

    if all_ok:
        click.echo("✅ OK")
        sys.exit(0)
    click.echo(f"❌ FAIL ({len(issues)} issues):\n  • " + "\n  • ".join(issues))
    sys.exit(1)


# ==============================================================
# CLI RAIZ
# ==============================================================
@click.group(help="OnTrackChain QA Gateway (SSOT de asserções de segurança RLS/LGPD/Health).")
@click.version_option(package_name="ontrackchain-qa-gateway", prog_name="qa-gateway")
def cli() -> None:
    pass


# ==============================================================
# COMANDO 1: scan rls
# ==============================================================
@cli.command(name="scan-rls", help="Scan RLS em TODAS tabelas esperadas com org_id.")
@click.option(
    "--db-url",
    "db_url",
    required=False,
    default=None,
    envvar="ONTRACKCHAIN_DATABASE_URL",
    help="Connection string PostgreSQL (ex: postgresql://user:pass@host:5432/db). Lê env ONTRACKCHAIN_DATABASE_URL se omitido.",
)
@click.option(
    "--failures-json",
    "failures_json",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Opcional: path para salvar relatório JSON com falhas.",
)
@click.option(
    "--expected-tables",
    "expected_tables",
    type=str,
    default=",".join(sorted(TABLES_EXPECTED_TO_HAVE_ORG_ID)),
    show_default=True,
    help="Override da lista de tabelas esperadas (CSV separado por vírgula).",
)
def cmd_scan_rls(db_url: Optional[str], failures_json: Optional[str], expected_tables: str) -> None:
    if not db_url:
        click.echo(
            "❌ Parâmetro --db-url obrigatório ou env ONTRACKCHAIN_DATABASE_URL indefinido.",
            err=True,
        )
        sys.exit(3)

    tables = [t.strip() for t in expected_tables.split(",") if t.strip()]
    if not tables:
        click.echo("❌ --expected-tables está vazio (3+ tabelas esperadas).", err=True)
        sys.exit(3)

    try:
        with psycopg.connect(db_url) as conn:
            all_ok, statuses = assert_tables_have_rls(conn, expected_tables=tables)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"❌ Erro de conexão PostgreSQL: {type(exc).__name__}: {exc}", err=True)
        sys.exit(2)

    issues: list[str] = []
    for s in statuses:
        mark = "PASS" if s.ok else "FAIL"
        line = f"  [{mark}] {s.table_name:40s}  issues={s.issues or '[]'}"
        click.echo(line)
        if not s.ok:
            issues.append(f"{s.table_name}: {s.summary}")

    total = len(statuses)
    pass_count = total - len(issues)
    click.echo(f"\nResumo: {pass_count}/{total} PASSARAM | {len(issues)} FALHARAM")
    _exit_report(len(issues) == 0, issues, failures_json)


# ==============================================================
# COMANDO 2: health (paralelo, N endpoints)
# ==============================================================
@cli.command(name="health", help="Health check paralelo em múltiplos endpoints /healthz.")
@click.option(
    "--endpoints",
    "endpoints_arg",
    type=str,
    required=True,
    help="Ou CSV separado por vírgula OU caminho para .txt com 1 URL por linha.",
)
@click.option(
    "--http-timeout",
    "http_timeout",
    type=float,
    default=DEFAULT_HTTP_TIMEOUT,
    show_default=True,
    help="Timeout em segundos por request HTTP.",
)
@click.option(
    "--max-workers",
    "max_workers",
    type=int,
    default=10,
    show_default=True,
    help="Workers paralelos (ThreadPoolExecutor).",
)
@click.option(
    "--failures-json",
    "failures_json",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Opcional: path relatório JSON falhas.",
)
def cmd_health(endpoints_arg: str, http_timeout: float, max_workers: int, failures_json: Optional[str]) -> None:
    # Resolve CSV vs arquivo .txt
    candidates: list[str] = []
    if Path(endpoints_arg).is_file():
        for raw in Path(endpoints_arg).read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if s and not s.startswith("#"):
                candidates.append(s)
    else:
        candidates = [x.strip() for x in endpoints_arg.split(",") if x.strip()]

    if not candidates:
        click.echo("❌ --endpoints: 0 URLs válidas.", err=True)
        sys.exit(3)

    click.echo(f"Rodando health check em {len(candidates)} endpoints (workers={max_workers} timeout={http_timeout}s)...")

    def _one(url: str) -> tuple[str, bool, str]:
        t0 = time.time()
        try:
            r = requests.get(url, timeout=http_timeout)
            if 200 <= r.status_code < 400:
                return url, True, f"{r.status_code} OK {(time.time()-t0)*1000:.0f}ms"
            return url, False, f"HTTP {r.status_code} {(time.time()-t0)*1000:.0f}ms"
        except Exception as exc:  # noqa: BLE001
            return url, False, f"{type(exc).__name__}: {exc}"

    issues: list[str] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_one, u): u for u in candidates}
        for fut in as_completed(futures):
            url, ok, detail = fut.result()
            mark = "✅" if ok else "❌"
            click.echo(f"  {mark} {url:<70s}  {detail}")
            if not ok:
                issues.append(f"{url}: {detail}")

    click.echo(f"\nResumo: {len(candidates)-len(issues)}/{len(candidates)} endpoints saudáveis")
    _exit_report(len(issues) == 0, issues, failures_json)


# ==============================================================
# COMANDO 3: scan lgpd (CPF plaintext + chaves privadas em dump SQL)
# ==============================================================
@cli.command(name="scan-lgpd", help="Varre dump SQL buscando CPF plaintext / chaves privadas.")
@click.option(
    "--dump-file",
    "dump_file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    required=True,
    help="Caminho para arquivo .sql de dump pg_dump.",
)
@click.option(
    "--exclude-columns",
    "exclude_cols",
    type=str,
    default="sha256,hash,digest,signature,encrypted,token",
    show_default=True,
    help="Nomes de colunas (CSV) para SUSPEITAR de falso positivo (hashes). Ignorar linhas com INSERT nelas.",
)
@click.option(
    "--max-matches-report",
    "max_matches",
    type=int,
    default=10,
    show_default=True,
    help="Limite de matches mostrados por categoria (evita gigantesco output).",
)
@click.option(
    "--failures-json",
    "failures_json",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Opcional: path relatório JSON falhas.",
)
def cmd_scan_lgpd(dump_file: Path, exclude_cols: str, max_matches: int, failures_json: Optional[str]) -> None:
    click.echo(f"Analisando dump SQL: {dump_file} (tamanho {dump_file.stat().st_size:,} bytes)...")
    excl = {e.strip().lower() for e in exclude_cols.split(",") if e.strip()}
    try:
        text = dump_file.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"❌ Falha leitura arquivo: {type(exc).__name__}: {exc}", err=True)
        sys.exit(4)

    issues: list[str] = []
    # ---- 1. CPF plaintext ----
    cpf_hits = CPF_REGEX.findall(text)
    if cpf_hits:
        sample = cpf_hits[:max_matches]
        click.echo(f"  ⚠️  CPF plaintext detectado: {len(cpf_hits)} ocorrências (amostra 10 primeiros: {sample})")
        issues.append(f"LGPD-CPF-PLAINTEXT: {len(cpf_hits)} matchs")
    else:
        click.echo("  ✅ 0 ocorrências de CPF plaintext")

    # ---- 2. Chaves privadas ----
    priv_hits = []
    for i, line in enumerate(text.splitlines(), 1):
        for r in PRIVATE_KEY_REGEXES:
            if r.search(line):
                priv_hits.append((i, line[:100]))
                break
    if priv_hits:
        sample = priv_hits[:max_matches]
        click.echo(f"  ⚠️  CHAVE PRIVADA detectada: {len(priv_hits)} linhas (amostra {sample})")
        issues.append(f"LGPD-PRIVATE-KEY-IN-DB: {len(priv_hits)} linhas")
    else:
        click.echo("  ✅ 0 chaves privadas detectadas no dump")

    # ---- 3. (Bônus) exclusão de colunas hash / false positives ----
    lines_hash_insert = [ln for ln in text.splitlines() if excl and excl & {w.strip().lower() for w in ln.split()}]
    if lines_hash_insert:
        click.echo(f"  ℹ️  {len(lines_hash_insert)} INSERTs com colunas hash/encrypted (considerados safe, omitidos de falha)")

    click.echo(f"\nResumo LGPD: {len(issues)} problema(s) crítico(s).")
    _exit_report(len(issues) == 0, issues, failures_json)


# ==============================================================
# COMANDO 4: scan-sla (24h Dead Man Switch — investigações live)
# ==============================================================
@cli.command(name="scan-sla", help="Valida SLA 24h exploração live (último sucesso há < --sla-seconds).")
@click.option(
    "--db-url",
    "db_url",
    required=False,
    default=None,
    envvar="ONTRACKCHAIN_DATABASE_URL",
    help="Connection string PostgreSQL (opcional). Se omitido, usa --last-success-unix ou arquivo .prom",
)
@click.option(
    "--last-success-unix",
    "last_success_unix",
    type=int,
    default=None,
    envvar="INVESTIGATION_EXPLORER_LAST_SUCCESS_UNIX",
    help="Unix timestamp último sucesso conhecido (sobrescreve query DB se fornecido).",
)
@click.option(
    "--sla-seconds",
    "sla_seconds",
    type=int,
    default=86400,
    show_default=True,
    help="Janela SLA em segundos. Default 86400 = 24h.",
)
@click.option(
    "--prom-file",
    "prom_file",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    default=None,
    envvar="INVESTIGATION_SLA_PROM_FILE",
    help="Opcional: arquivo .txt/.prom com linha `investigation_explorer_last_success_timestamp <unix>` usado como source quando DB/last-success-unix não fornecidos.",
)
@click.option(
    "--failures-json",
    "failures_json",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Opcional: path relatório JSON falhas.",
)
def cmd_scan_sla(
    db_url: Optional[str],
    last_success_unix: Optional[int],
    sla_seconds: int,
    prom_file: Optional[Path],
    failures_json: Optional[str],
) -> None:
    resolved_last: Optional[int] = None
    source: str = "none"

    # 1. Tenta last_success_unix explicito (env var --last-success-unix)
    if last_success_unix is not None and last_success_unix > 0:
        resolved_last = last_success_unix
        source = "--last-success-unix"

    # 2. Tenta arquivo prom (se fornecido/existir e nenhum valor explicito)
    if resolved_last is None and prom_file is not None and prom_file.is_file():
        for line in prom_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if s.startswith("#") or not s:
                continue
            if s.startswith("investigation_explorer_last_success_timestamp"):
                parts = s.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    v = int(parts[1])
                    if v > 0:
                        resolved_last = v
                        source = f"prom-file:{prom_file.name}"
                        break

    # 3. Tenta query SQL (DB)
    if resolved_last is None and db_url:
        try:
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT EXTRACT(EPOCH FROM MAX(completed_at))::BIGINT AS last_ts
                        FROM cases
                        WHERE status IN ('completed', 'COMPLETED', 'success', 'SUCCESS')
                          AND completed_at IS NOT NULL
                          AND completed_at >= NOW() - INTERVAL '30 days'
                        LIMIT 1
                        """,
                    )
                    row = cur.fetchone()
                    if row and row[0]:
                        resolved_last = int(row[0])
                        source = "sql/cases.completed_at"
        except Exception as exc:  # noqa: BLE001
            click.echo(f"  ℹ️  Query DB falhou (ignorado): {type(exc).__name__}: {exc}")

    now = int(time.time())
    issues: list[str] = []
    click.echo(f"SLA 24h (janela={sla_seconds}s) · source_last_success={source}")
    if resolved_last is None or resolved_last <= 0:
        click.echo(f"  ❌ Não foi possível obter last_success (resolved_last={resolved_last})")
        age_reported = sla_seconds + 1
        issues.append(
            "SLA-DEADMAN-NO-LAST-SUCCESS: nenhuma fonte de timestamp (unix/prom/sql) forneceu dado."
        )
    else:
        age_reported = now - resolved_last
        click.echo(f"  last_success_unix = {resolved_last} ({time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(resolved_last))})")
        click.echo(f"  now_unix          = {now} ({time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))})")
        click.echo(f"  idade(seconds)    = {age_reported}  ·  limite SLA={sla_seconds}s  →  "
                   f"{'OK ✅' if age_reported <= sla_seconds else 'VIOLADO 🔴'}")
        if age_reported > sla_seconds:
            issues.append(
                f"SLA-DEADMAN-VIOLATED: último sucesso há {age_reported}s (> limite {sla_seconds}s). "
                f"Fonte={source}."
            )

    # Escreve prometheus gauge em /tmp se env OUTPUT_PROM_FILE setado
    out_prom_env = os.environ.get("SLA_GAUGE_OUTPUT_FILE")
    if out_prom_env:
        Path(out_prom_env).parent.mkdir(parents=True, exist_ok=True)
        with open(out_prom_env, "w", encoding="utf-8") as fh:
            fh.write(
                "# HELP investigation_explorer_last_success_timestamp Unix timestamp da última investigação com sucesso\n"
                "# TYPE investigation_explorer_last_success_timestamp gauge\n"
                f"investigation_explorer_last_success_timestamp {resolved_last or 0}\n"
                "# HELP investigation_explorer_sla_window_seconds Janela SLA configurada\n"
                "# TYPE investigation_explorer_sla_window_seconds gauge\n"
                f"investigation_explorer_sla_window_seconds {sla_seconds}\n"
                "# HELP investigation_explorer_age_seconds Idade do último sucesso (0 se unknown)\n"
                "# TYPE investigation_explorer_age_seconds gauge\n"
                f"investigation_explorer_age_seconds {0 if resolved_last is None or resolved_last ==0 else age_reported}\n"
            )
        click.echo(f"  ℹ️  Gauge Prometheus escrito em {out_prom_env}")

    click.echo(f"  resumo: {len(issues)} problema(s)")
    _exit_report(len(issues) == 0, issues, failures_json)


# ---------------------------------------------------------------------------
# COMANDO 6: scan-rbac — valida roles claim JWT + require_role_with_audit
# ---------------------------------------------------------------------------
@cli.command(
    name="scan-rbac",
    help="Valida RBAC: endpoints protegidos por _require_role_with_audit, roles claim em JWT e tabela users.role corretos.",
)
@click.option(
    "--targets",
    "targets",
    default="auth-service,case-management,investigation-api",
    show_default=True,
    help="CSV serviços alvo (code scan em apps/*/src para detectar role-check ausente em POST/PUT/DELETE).",
)
@click.option("--project-root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=None)
@click.option("--db-url", required=False, envvar="ONTRACKCHAIN_DATABASE_URL")
@click.option(
    "--max-anonymous-write-per-service",
    type=int,
    default=0,
    show_default=True,
    help="Máximo permitido de endpoints POST/PUT/PATCH/DELETE sem _require_role_with_audit por serviço (0 = nenhum permitido).",
)
@click.option("--failures-json", type=click.Path(dir_okay=False, writable=True))
def cmd_scan_rbac(
    targets: str,
    project_root: Optional[Path],
    db_url: Optional[str],
    max_anonymous_write_per_service: int,
    failures_json: Optional[str],
) -> None:
    """
    SCAN-RBAC: Duas fases.
      (A) Static scan: busca cada main.py FastAPI por rotas write method sem role check.
      (B) DB scan: valida que users.role contém apenas {VIEWER,ANALYST,COMPLIANCE,ADMIN,OWNER}
          e que ninguém tem OWNER duplicado por organização.
    """
    issues: List[str] = []
    if project_root is None:
        # default raiz apps/
        here = Path(__file__).resolve().parents[5]  # qa-gateway/src/qa_gateway/cli.py → ontrackchain/
        project_root = here
    apps_root = project_root / "apps"

    # --- FASE A: static scan por serviço ---
    svc_list = [x.strip() for x in targets.split(",") if x.strip()]
    click.echo("🚦 SCAN-RBAC FASE A (code scan FastAPI):")
    for svc in svc_list:
        svc_root = apps_root / svc / "src" / svc.replace("-", "_") / "main.py"
        if not svc_root.exists():
            issues.append(f"[RBAC-A/{svc}] arquivo main.py não existe esperado em {svc_root}")
            continue
        content = svc_root.read_text(encoding="utf-8")
        endpoints_write = _extract_rbac_routes(content)
        anon = [e for e in endpoints_write if not e.has_role_check]
        click.echo(f"  · {svc:28s}: {len(endpoints_write)} endpoints write;  {len(anon)} SEM role-check")
        if len(anon) > max_anonymous_write_per_service:
            for e in anon:
                issues.append(
                    f"[RBAC-A/{svc}] {e.method} {e.path} linha {e.line} não chama _require_role_with_audit nem requires(... roles=[...]) — risco escrita anônima permitida."
                )
        # + garante existência de _require_role_with_audit como função em qualquer lugar
        if "_require_role_with_audit" not in content and "requires" not in content:
            issues.append(f"[RBAC-A/{svc}] NENHUM role-check encontrado em todo main.py ({svc_root})")

    # --- FASE B: DB scan users.role e owners por organização ---
    click.echo("🚦 SCAN-RBAC FASE B (DB scan users.role):")
    if not db_url:
        click.echo("  ⚠️  --db-url / ONTRACKCHAIN_DATABASE_URL não informado → skip FASE B.")
    else:
        import psycopg  # type: ignore
        ALLOWED_ROLES = {"VIEWER", "ANALYST", "COMPLIANCE", "ADMIN", "OWNER", "SYSTEM"}
        try:
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, organization_id, email, role FROM users WHERE deleted_at IS NULL")
                    rows = cur.fetchall()
                    invalid = [(r[0], r[1], r[2], r[3]) for r in rows if (r[3] or "").upper() not in ALLOWED_ROLES]
                    if invalid:
                        for uid, org, email, role in invalid:
                            issues.append(
                                f"[RBAC-B/DB] user_id={uid} org={org} email={email} role='{role}' NÃO está em ALLOWED={sorted(ALLOWED_ROLES)}."
                            )
                    # multi-OWNER por org
                    cur.execute(
                        """
                        SELECT organization_id, COUNT(*)
                          FROM users
                         WHERE deleted_at IS NULL AND UPPER(role)='OWNER'
                         GROUP BY organization_id
                        HAVING COUNT(*) > 1
                        """
                    )
                    multi_owners = cur.fetchall()
                    for org, cnt in multi_owners:
                        issues.append(
                            f"[RBAC-B/DB] organização {org} tem {cnt} OWNERs (espera <=1 por org — viola SSOT role)."
                        )
                    click.echo(f"  · usuários lidos: {len(rows)};  roles inválidas: {len(invalid)};  multi-OWNER orgs: {len(multi_owners)}")
        except Exception as exc:  # noqa: BLE001
            issues.append(f"[RBAC-B/DB] Erro conexão/query: {type(exc).__name__}: {str(exc)[:220]}")

    click.echo(f"  resumo: {len(issues)} problema(s)")
    _exit_report(len(issues) == 0, issues, failures_json)


# ---------------------------------------------------------------------------
# Helpers para scan-rbac (static parse rotas FastAPI)
# ---------------------------------------------------------------------------
class _RbacRoute(NamedTuple):
    method: str
    path: str
    line: int
    has_role_check: bool


def _extract_rbac_routes(main_content: str) -> List[_RbacRoute]:
    import re
    results: List[_RbacRoute] = []
    lines = main_content.splitlines()
    WRITE_METHODS = ("post", "put", "patch", "delete")
    for idx, ln in enumerate(lines, start=1):
        # busca padrão @app.post("...") / @router.put(...) etc
        m = re.match(r"\s*@(?:app|router)\.(post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']", ln)
        if not m:
            continue
        method = m.group(1).lower()
        path = m.group(2)
        if method not in WRITE_METHODS:
            continue
        # olha 20 linhas seguintes no corpo da função por token de role check
        body_fragment = "\n".join(lines[idx : min(idx + 20, len(lines))])
        has_rc = any(
            t in body_fragment
            for t in [
                "_require_role_with_audit(",
                "requires(roles=[",
                "security=[Depends(requires(",
                "rbac_required(",
            ]
        )
        results.append(_RbacRoute(method=method.upper(), path=path, line=idx, has_role_check=has_rc))
    return results


if __name__ == "__main__":
    cli()
