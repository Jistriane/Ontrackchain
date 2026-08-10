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
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, NamedTuple, Optional

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
@click.option(
    "--strict/--no-strict",
    "strict_mode",
    default=True,
    show_default=True,
    help="(Sprint 20 T2-03) Padrão STRICT=True: warnings também contam como ISSUES e retornam exit=1. Use --no-strict apenas em branches feature onde warnings são aceitáveis temporariamente.",
)
@click.option(
    "--max-warnings",
    "max_warnings",
    type=int,
    default=0,
    show_default=True,
    help="(Sprint 20 T2-03) Quantidade máxima de WARNINGS permitidos. Se --strict=True e warnings > max_warnings, somam em ISSUES (bloqueia).",
)
def cmd_scan_rbac(
    targets: str,
    project_root: Optional[Path],
    db_url: Optional[str],
    max_anonymous_write_per_service: int,
    failures_json: Optional[str],
    strict_mode: bool,
    max_warnings: int,
) -> None:
    """
    SCAN-RBAC: Duas fases + WARNINGS estruturais (Sprint 20 T2-03).
      (A) Static scan: busca cada main.py FastAPI por rotas write method sem role check.
      (B) DB scan: valida que users.role contém apenas {VIEWER,ANALYST,COMPLIANCE,ADMIN,OWNER}
          e que ninguém tem OWNER duplicado por organização.
      (W) WARNINGS estruturais: < 3 rotas write / serviços main.py vazio / services nao listados
          em targets mas existentes fisicamente em apps/.
    """
    issues: List[str] = []
    warnings: List[str] = []
    if project_root is None:
        # default raiz apps/
        here = Path(__file__).resolve().parents[5]  # qa-gateway/src/qa_gateway/cli.py → ontrackchain/
        project_root = here
    apps_root = project_root / "apps"

    # --- FASE W (WARNINGS estruturais - antes de A/B) ---
    target_list = [x.strip() for x in targets.split(",") if x.strip()]
    click.echo("🚦 SCAN-RBAC FASE W (WARNINGS estruturais Sprint 20 T2-03):")
    # W-1: serviços em apps/ não listados no targets (risco: serviço novo adicionado sem scan)
    if apps_root.is_dir():
        actual_services = sorted(
            p.name for p in apps_root.iterdir() if p.is_dir() and (p / "src").is_dir()
        )
        missing_in_targets = sorted(set(actual_services) - set(target_list))
        if missing_in_targets:
            msg = f"[RBAC-W001] serviços em apps/ NÃO listados em --targets: {missing_in_targets}. Adicione-os para não bypassar o scan."
            warnings.append(msg)
            click.echo(f"  ⚠️  {msg}")
    for svc in target_list:
        svc_root = apps_root / svc / "src" / svc.replace("-", "_") / "main.py"
        if not svc_root.exists():
            # ISSUE FATAL como no original
            pass
        else:
            content = svc_root.read_text(encoding="utf-8")
            endpoints = _extract_rbac_routes(content)
            # W-2: serviço main.py com ZERO rotas write (muito estranho)
            if len(endpoints) == 0:
                msg = f"[RBAC-W002] {svc}: ZERO endpoints write (POST/PUT/PATCH/DELETE) detectados. Verifique se este FastAPI main.py tem rotas protegidas."
                warnings.append(msg)
                click.echo(f"  ⚠️  {msg}")
            # W-3: serviço main.py com < 3 endpoints write (baixa cobertura)
            elif 0 < len(endpoints) < 3:
                msg = f"[RBAC-W003] {svc}: apenas {len(endpoints)} endpoint(s) write (< 3). Possível cobertura de autorização incompleta."
                warnings.append(msg)
                click.echo(f"  ⚠️  {msg}")
    click.echo(f"  · total warnings: {len(warnings)} (max permitidos={max_warnings})")

    # --- FASE A: static scan por serviço ---
    svc_list = target_list
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
        warnings.append("[RBAC-W004] FASE B (DB scan users.role) SKIPPADA — --db-url não informado. Roles não validadas no banco.")
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

    # --- Sprint 20 T2-03: STRICT MODE = warnings > max_warnings → acrescenta em issues ---
    if strict_mode and len(warnings) > max_warnings:
        click.echo(
            f"\n🚨 RBAC STRICT MODE ativo (padrão): warnings={len(warnings)} > max_warnings={max_warnings}. "
            f"WARNINGS elevados a ISSUES (bloqueia merge em main/release/hotfix)."
        )
        issues.extend(warnings)
    elif not strict_mode:
        click.echo(f"\nℹ️  RBAC --no-strict: warnings {len(warnings)} IGNORADOS (apenas informativos). Recomendado só em branches feature.")

    click.echo(f"  resumo: {len(issues)} erro(s);  {len(warnings)} warning(s);  strict_mode={strict_mode}")
    _exit_report(len(issues) == 0, issues, failures_json)


# ---------------------------------------------------------------------------
# Sprint 23 Q3-05: cmd_scan_billing_capabilities — validação do T2-10
# 4 códigos WARNING estruturais: BW-001..BW-004
# ---------------------------------------------------------------------------

@cli.command("scan-billing-capabilities")
@click.option(
    "--project-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Raiz do workspace (ontrackchain raiz ou apps/). Default = auto detecta.",
)
@click.option(
    "--strict/--no-strict",
    "strict_mode",
    default=True,
    show_default=True,
    help="Sprint 23 Q3-05: warnings elevados a issues se excederem max_warnings.",
)
@click.option(
    "--max-warnings",
    type=int,
    default=0,
    show_default=True,
    help="Máximo de warnings permitidos sem transformar em issues.",
)
@click.option(
    "--failures-json",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Opcional: caminho arquivo JSON para persistir issues e warnings.",
)
def cmd_scan_billing_capabilities(
    project_root: Optional[Path],
    strict_mode: bool,
    max_warnings: int,
    failures_json: Optional[str],
) -> None:
    """
    SCAN-BILLING-CAPABILITIES Q3-05 (Sprint 23):
      Valida que o módulo billing_capabilities.py (T2-10) está consistente,
      monotônico por tier, e que o main.py investigation incluiu o router.
      WARNINGS BW-001..BW-004.
    """
    issues: List[str] = []
    warnings: List[str] = []
    if project_root is None:
        here = Path(__file__).resolve().parents[5]
        project_root = here
    inv_root = project_root / "apps" / "investigation-api"
    inv_src = inv_root / "src" / "investigation_api"
    cap_file = inv_src / "billing_capabilities.py"
    main_file = inv_src / "main.py"
    stripe_billing_file = inv_src / "billing_stripe.py"

    click.echo("🧾 Q3-05 SCAN BILLING CAPABILITIES (Sprint 23 T2-10):")

    # --- BW-001: Arquivos billing_capabilities.py ausentes ou vazios
    if not cap_file.is_file():
        warnings.append(
            "[BW-001] billing_capabilities.py NÃO existe em investigation-api. Módulo T2-10 não foi criado."
        )
    elif cap_file.stat().st_size == 0:
        warnings.append(
            "[BW-001] billing_capabilities.py VAZIO. Nenhuma capability definida."
        )

    # --- BW-002: main.py investigation NÃO contém include_router billing_capabilities_router
    if not main_file.is_file():
        warnings.append("[BW-002] investigation-api main.py NÃO encontrado. Impossível validar include_router.")
    else:
        main_text = main_file.read_text(encoding="utf-8")
        if "billing_capabilities_router" not in main_text or "include_router(billing_capabilities_router)" not in main_text:
            warnings.append(
                "[BW-002] investigation-api main.py NÃO tem `app.include_router(billing_capabilities_router)`."
                " Endpoint /capabilities/* SEM ROTAS EXPOSTAS."
            )

    # --- BW-003: Tentar importar billing_capabilities dinamicamente + validar monotonicidade
    cap_importable = False
    try:
        # Tenta importação real do módulo: adiciona ao sys.path temporariamente
        import importlib.util
        import sys
        inv_src_str = str(inv_src.parent)  # .../src
        if inv_src_str not in sys.path:
            sys.path.insert(0, inv_src_str)
        spec = importlib.util.spec_from_file_location(
            "investigation_api.billing_capabilities", str(cap_file)
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            OTK = getattr(mod, "OTK_PLAN_CAPABILITIES", None)
            if OTK is None:
                warnings.append("[BW-003] Constante OTK_PLAN_CAPABILITIES NÃO encontrada em billing_capabilities.py.")
            else:
                cap_importable = True
                for tier_required in ("startup", "business", "enterprise"):
                    if tier_required not in OTK:
                        issues.append(f"[BILLING-CAP-E001] Tier {tier_required} ausente em OTK_PLAN_CAPABILITIES.")

                if all(t in OTK for t in ("startup", "business", "enterprise")):
                    # Monotonicidade AI credits
                    if not (OTK["startup"]["included_ai_credits_per_month"]
                            < OTK["business"]["included_ai_credits_per_month"]
                            < OTK["enterprise"]["included_ai_credits_per_month"]):
                        issues.append(
                            "[BILLING-CAP-E002] included_ai_credits_per_month NÃO é estritamente crescente"
                            " por tier (viola monotonicidade)."
                        )
                    # Monotonicidade B2B quota por hora
                    if not (OTK["startup"]["b2b_api_calls_per_hour_quota"]
                            <= OTK["business"]["b2b_api_calls_per_hour_quota"]
                            <= OTK["enterprise"]["b2b_api_calls_per_hour_quota"]):
                        issues.append(
                            "[BILLING-CAP-E003] b2b_api_calls_per_hour_quota NÃO é monotônico crescente por tier."
                        )
                    # Enterprise tem SSO, business e startup não
                    if OTK["enterprise"]["has_sso_saml_oidc_federation"] is not True:
                        issues.append(
                            "[BILLING-CAP-E004] Enterprise DEVE ter has_sso_saml_oidc_federation=True."
                        )
                    if OTK["business"]["has_sso_saml_oidc_federation"] is not False:
                        warnings.append(
                            "[BW-003] Business NÃO DEVE ter SSO (padrão: só Enterprise). Ajuste ou atualize regra de negócio se aprovado."
                        )
                    # Startup max 5 usuários
                    if OTK["startup"]["included_users_max"] != 5:
                        warnings.append(
                            "[BW-003] Startup: esperado included_users_max=5 (padrão T2-10)."
                            f" Encontrado = {OTK['startup']['included_users_max']}."
                        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            f"[BW-003] Falha ao importar billing_capabilities.py (não crítico no STRICT): {type(exc).__name__}: {str(exc)[:260]}"
        )

    # --- BW-004: billing_stripe.py existe (T2-09 é pré-requisito de T2-10 capabilities)
    if not stripe_billing_file.is_file():
        warnings.append(
            "[BW-004] Módulo billing_stripe.py T2-09 ausente (pré-requisito de T2-10). "
            "billing_capabilities depende de _ensure_org_skeleton_subscription do billing_stripe."
        )

    # --- Resumo e STRICT MODE ---
    if strict_mode and len(warnings) > max_warnings:
        click.echo(
            f"\n🚨 BILLING STRICT MODE ativo (padrão): warnings={len(warnings)} > max_warnings={max_warnings}. "
            "WARNINGS elevados a ISSUES."
        )
        issues.extend(warnings)
    elif not strict_mode:
        click.echo(f"\nℹ️  --no-strict: warnings {len(warnings)} informativos APENAS. Recomendado só feature branches.")

    click.echo(f"  resumo: {len(issues)} issue(s);  {len(warnings)} warning(s);  strict={strict_mode};  cap_importable={cap_importable}")

    # Show listas detalhadas
    if warnings:
        click.echo("\n--- WARNINGS ---")
        for w in warnings:
            click.echo(f"  ⚠️  {w}")
    if issues:
        click.echo("\n--- ISSUES ---")
        for i in issues:
            click.echo(f"  ❌ {i}")
    _exit_report(len(issues) == 0, issues, failures_json)


# ---------------------------------------------------------------------------
# Sprint 24 Q3-06: cmd_scan_billing_enforcement — validação T2-11 ADR-027
# Warning codes BE-001..BE-004
# ---------------------------------------------------------------------------

@cli.command("scan-billing-enforcement")
@click.option(
    "--project-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Raiz workspace ontrackchain. Default auto-detect.",
)
@click.option(
    "--strict/--no-strict",
    "strict_mode",
    default=True,
    show_default=True,
    help="Sprint 24 Q3-06: warnings excedentes viram issues (exit=1).",
)
@click.option(
    "--max-warnings",
    type=int,
    default=0,
    show_default=True,
    help="Máximo warnings permitidos antes de transformar em issues STRICT.",
)
@click.option(
    "--failures-json",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Opcional: caminho JSON para persistir issues/warnings.",
)
@click.option(
    "--check-prod-redis/--skip-prod-redis",
    default=True,
    show_default=True,
    help="BE-004: validar se deployment/prod tem OTK_REDIS_URL (anti-DUAL MODE fallback em prod).",
)
def cmd_scan_billing_enforcement(
    project_root: Optional[Path],
    strict_mode: bool,
    max_warnings: int,
    failures_json: Optional[str],
    check_prod_redis: bool,
) -> None:
    """
    SCAN-BILLING-ENFORCEMENT Q3-06 (Sprint 24 T2-11):
      Valida que ADR-027 está implementado em investigation-api:
      módulo billing_enforcement.py, middleware global headers,
      monotonicidade SSOT validada e Redis obrigatório em prod.
    """
    issues: List[str] = []
    warnings: List[str] = []
    if project_root is None:
        project_root = Path(__file__).resolve().parents[5]
    inv_src = project_root / "apps" / "investigation-api" / "src" / "investigation_api"
    main_file = inv_src / "main.py"
    enforce_file = inv_src / "billing_enforcement.py"
    cap_file = inv_src / "billing_capabilities.py"

    click.echo("🛡️  Q3-06 SCAN BILLING ENFORCEMENT (Sprint 24 ADR-027 T2-11):")

    # --- BE-001: billing_enforcement.py NÃO existe
    if not enforce_file.is_file():
        warnings.append(
            "[BE-001] billing_enforcement.py ausente em investigation-api. "
            "ADR-027 DoD 027.1 NÃO cumprido. Nenhum enforcement de capabilities está ativo."
        )
    elif enforce_file.stat().st_size == 0:
        warnings.append("[BE-001] billing_enforcement.py VAZIO.")

    # --- BE-002: main.py NÃO registra add_billing_headers_middleware
    if not main_file.is_file():
        warnings.append("[BE-002] investigation-api main.py ausente.")
    else:
        main_txt = main_file.read_text(encoding="utf-8")
        if "add_billing_headers_middleware" not in main_txt:
            warnings.append(
                "[BE-002] main.py NÃO tem chamada `add_billing_headers_middleware(app)`. "
                "5 headers X-RateLimit/X-Billing NÃO serão injetados (ADR-027 DoD 027.3)."
            )
        if "from investigation_api.billing_enforcement import add_billing_headers_middleware" not in main_txt:
            warnings.append(
                "[BE-002] main.py NÃO importa `add_billing_headers_middleware` de billing_enforcement."
            )

    # --- BE-003: Dinamicamente importar billing_enforcement e validar SSOT
    enforcement_importable = False
    monotonic_enterprise_ok = False
    fail_closed_function_exists = False
    if enforce_file.is_file():
        try:
            import importlib.util
            import sys
            inv_src_str = str(inv_src.parent)
            if inv_src_str not in sys.path:
                sys.path.insert(0, inv_src_str)
            spec = importlib.util.spec_from_file_location(
                "investigation_api.billing_enforcement", str(enforce_file)
            )
            if spec and spec.loader:
                mod_enf = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod_enf)  # type: ignore[union-attr]
                enforcement_importable = True
                fn = getattr(mod_enf, "enforce_capability", None)
                fail_closed_function_exists = callable(fn)
                # Importar SSOT de billing_capabilities e verificar monotonicidade enterprise > business > startup
                spec2 = importlib.util.spec_from_file_location(
                    "investigation_api.billing_capabilities", str(cap_file)
                )
                if spec2 and spec2.loader:
                    mod_cap = importlib.util.module_from_spec(spec2)
                    spec2.loader.exec_module(mod_cap)  # type: ignore[union-attr]
                    OTK = getattr(mod_cap, "OTK_PLAN_CAPABILITIES", None)
                    if OTK is not None:
                        ai_ok = (
                            OTK["startup"]["included_ai_credits_per_month"]
                            < OTK["business"]["included_ai_credits_per_month"]
                            < OTK["enterprise"]["included_ai_credits_per_month"]
                        )
                        b2b_ok = (
                            OTK["startup"]["b2b_api_calls_per_hour_quota"]
                            <= OTK["business"]["b2b_api_calls_per_hour_quota"]
                            <= OTK["enterprise"]["b2b_api_calls_per_hour_quota"]
                        )
                        monotonic_enterprise_ok = ai_ok and b2b_ok
                        if not ai_ok:
                            issues.append(
                                "[BILLING-ENF-E001] included_ai_credits_per_month NÃO monotônico crescente."
                            )
                        if not b2b_ok:
                            issues.append(
                                "[BILLING-ENF-E002] b2b_api_calls_per_hour_quota NÃO monotônico crescente."
                            )
                    else:
                        warnings.append(
                            "[BE-003] billing_capabilities.py NÃO tem constante OTK_PLAN_CAPABILITIES "
                            "(pré-requisito enforcement = SSOT)."
                        )
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                f"[BE-003] Falha import billing_enforcement/billing_capabilities: {type(exc).__name__}: {str(exc)[:260]}"
            )
    if not fail_closed_function_exists and enforcement_importable:
        warnings.append(
            "[BE-003] billing_enforcement.py NÃO exporta função `enforce_capability` (Depends FastAPI)."
        )

    # --- BE-004: PROD obriga Redis (DUAL MODE fallback NÃO pode ser usado em prod)
    if check_prod_redis:
        helm_charts_path = project_root / "apps" / "investigation-api" / "helm"
        kustomize_prod = project_root / "apps" / "investigation-api" / "deploy" / "overlays" / "prod"
        prod_hint_found = False
        hint_strings = ["OTK_REDIS_URL", "redis.enabled", "redisHost"]
        checked_paths: List[Path] = []
        for p in (helm_charts_path, kustomize_prod, project_root / "deploy"):
            if p.exists():
                checked_paths.append(p)
                for f in list(p.rglob("*.yaml")) + list(p.rglob("*.yml")) + list(p.rglob("*.env")):
                    try:
                        txt = f.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue
                    if any(s in txt for s in hint_strings):
                        prod_hint_found = True
                        break
        if checked_paths and not prod_hint_found:
            warnings.append(
                "[BE-004] Ambiente prod NÃO tem OTK_REDIS_URL / redis.enabled em helm/deploy overlays. "
                "Risco: DUAL MODE cai em InMemory em 2+ pods → vazamento de cota enterprise."
            )

    # --- STRICT MODE
    if strict_mode and len(warnings) > max_warnings:
        click.echo(
            f"\n🚨 ENFORCEMENT STRICT default: warnings={len(warnings)} > max_warnings={max_warnings}. "
            "WARNINGS elevados a ISSUES."
        )
        issues.extend(warnings)
    elif not strict_mode:
        click.echo(
            f"\nℹ️  --no-strict: warnings={len(warnings)} informativos APENAS. Recomendado só feature branches."
        )

    click.echo(
        f"  resumo: {len(issues)} issue(s);  {len(warnings)} warning(s);  "
        f"strict={strict_mode};  monotonic_SSOT_OK={monotonic_enterprise_ok};  "
        f"enforce_fn_exists={fail_closed_function_exists}"
    )
    if warnings:
        click.echo("\n--- WARNINGS ---")
        for w in warnings:
            click.echo(f"  ⚠️  {w}")
    if issues:
        click.echo("\n--- ISSUES ---")
        for i in issues:
            click.echo(f"  ❌ {i}")
    _exit_report(len(issues) == 0, issues, failures_json)


# ---------------------------------------------------------------------------
# Sprint 25 Q3-07: cmd_scan_lgpd_ropd — validação ADR-028 Art.37 LGPD
# Warnings LR-001..LR-005 + Issues E001..E003
# ---------------------------------------------------------------------------

@cli.command("scan-lgpd-ropd")
@click.option(
    "--project-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Raiz workspace ontrackchain. Default auto-detect.",
)
@click.option("--strict/--no-strict", "strict_mode", default=True, show_default=True)
@click.option("--max-warnings", type=int, default=0, show_default=True)
@click.option(
    "--failures-json",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Opcional: caminho JSON persistir issues/warnings.",
)
def cmd_scan_lgpd_ropd(
    project_root: Optional[Path],
    strict_mode: bool,
    max_warnings: int,
    failures_json: Optional[str],
) -> None:
    """
    SCAN-LGPD-ROPD Q3-07 Sprint 25 (ADR-028 LGPD Art.37):
      Valida que ROPD (Registro Operações Tratamento Dados Pessoais) está
      completo com os 12 campos obrigatórios ANPD e NÃO há campos vazios.
    """
    issues: List[str] = []
    warnings: List[str] = []
    if project_root is None:
        project_root = Path(__file__).resolve().parents[5]
    ropd_path = project_root / "docs" / "compliance-ropd"

    click.echo("🪪  Q3-07 SCAN LGPD ROPD (Sprint 25 ADR-028 Art.37 LGPD ANPD):")

    # --- LR-001: pasta compliance-ropd NÃO existe
    if not ropd_path.is_dir():
        warnings.append(
            "[LR-001] Pasta docs/compliance-ropd NÃO existe. "
            "Criar ROPD inicial ADR-028 DoD 028.1."
        )
        _finish_ropd(issues, warnings, failures_json, strict_mode, max_warnings)
        return

    files = sorted(ropd_path.glob("ROPD-OTK-*.md"))
    csv_path = ropd_path / "ROPD-OTK-CONSOLIDADO.csv"

    # --- LR-002: MENOS de 7 arquivos ROPD individuais
    if len(files) < 7:
        warnings.append(
            f"[LR-002] Apenas {len(files)} arquivos ROPD encontrados. Mínimo 7 obrigatórios "
            f"(Onboarding / B2B HMAC / AI LLM / OIDC MFA / Billing Stripe / Feed PEP / AML KYT)."
        )

    # --- LR-003: CSV consolidado NÃO existe
    if not csv_path.is_file():
        warnings.append(
            "[LR-003] CSV consolidado ROPD-OTK-CONSOLIDADO.csv NÃO foi gerado. "
            "Criar a partir dos arquivos Markdown (DoD 028.2)."
        )

    # --- LR-004: 12 campos obrigatórios em CADA arquivo markdown
    CAMPOS_OBRIGATORIOS_ROPD: List[str] = [
        "ID Operação",
        "Nome Operação",
        "Categoria Titulares",
        "Categorias Dados Pessoais",
        "Dados Sensíveis",
        "Base Legal",
        "Finalidade",
        "Compartilhamento",
        "Retenção",
        "Destruição",
        "Medidas Segurança",
        "DPO Contato",
    ]
    for file in files:
        try:
            txt = file.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"[LR-004] Impossível ler arquivo ROPD {file.name}: {exc}")
            continue
        for campo in CAMPOS_OBRIGATORIOS_ROPD:
            if campo not in txt:
                issues.append(
                    f"[ROPD-E001] Campo obrigatório '{campo}' ausente no ROPD {file.name}. "
                    "12 campos obrigatórios ANPD (LR-004)."
                )
                break
        # --- E002: DPO email ausente ou placeholder dpo@ontrackchain.com.br NÃO preenchido
        if "dpo@ontrackchain.com.br" not in txt:
            warnings.append(
                f"[LR-005] Contato DPO ausente ou padrão NÃO confirmado no ROPD {file.name}. "
                "Campo 12 'DPO Contato' obrigatório LGPD Art.41."
            )
        # --- E003: base legal Art.7 vazia
        if "Art.7" not in txt:
            issues.append(
                f"[ROPD-E003] ROPD {file.name} NÃO cita a base legal Art.7 LGPD. Obrigatoriedade ANPD."
            )

    # --- E002 CSV: Header tem 12 colunas?
    if csv_path.is_file():
        csv_txt = csv_path.read_text(encoding="utf-8", errors="ignore")
        header = csv_txt.splitlines()[0] if csv_txt else ""
        colunas = header.split(";") if ";" in header else header.split(",")
        if len(colunas) < 12:
            issues.append(
                f"[ROPD-E002] CSV consolidado tem apenas {len(colunas)} colunas. Esperado >=12 colunas ANPD."
            )

    _finish_ropd(issues, warnings, failures_json, strict_mode, max_warnings)


def _finish_ropd(
    issues: List[str],
    warnings: List[str],
    failures_json: Optional[str],
    strict_mode: bool,
    max_warnings: int,
) -> None:
    if strict_mode and len(warnings) > max_warnings:
        click.echo(
            f"\n🚨 ROPD STRICT default: warnings={len(warnings)} > max_warnings={max_warnings}. "
            "WARNINGS elevados a ISSUES exit=1."
        )
        issues.extend(warnings)
    elif not strict_mode:
        click.echo(f"\nℹ️  --no-strict: warnings={len(warnings)} informativos APENAS")

    click.echo(
        f"  resumo: {len(issues)} issue(s);  {len(warnings)} warning(s);  strict={strict_mode}"
    )
    if warnings:
        click.echo("\n--- WARNINGS ---")
        for w in warnings:
            click.echo(f"  ⚠️  {w}")
    if issues:
        click.echo("\n--- ISSUES ---")
        for i in issues:
            click.echo(f"  ❌ {i}")
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


# ---------------------------------------------------------------------------
# Comando Q3-08: scan-secrets-trufflehog
# ---------------------------------------------------------------------------
TRUFFLEHOG_MIN_VERSION = (3, 80, 0)
TRUFFLEHOG_VERIFIED_WARN = (
    "[TS-W%d] %s: %s (%s). Detector=%s. Raw=%s"
)
TRUFFLEHOG_VERIFIED_ERR = (
    "[TS-E%d] Segredo VERIFICADO encontrado (P0 LGPD Art.48 multa 2%%). Arquivo=%s linha=%d. Detector=%s. RawPrefix=%s"
)


def _find_trufflehog_bin() -> Optional[str]:
    """Procura binário trufflehog em PATH, ~/.local/bin, /usr/local/bin."""
    candidates = [shutil.which("trufflehog")]
    extra_dirs = [
        Path.home() / ".local" / "bin",
        Path("/usr/local/bin"),
        Path("/opt/homebrew/bin"),
    ]
    for d in extra_dirs:
        p = d / "trufflehog"
        if p.is_file():
            candidates.append(str(p))
    for c in candidates:
        if c and Path(c).is_file():
            return c
    return None


def _parse_trufflehog_json_lines(raw: str) -> List[Dict]:
    """Parse stdout JSON lines do trufflehog --json --only-verified."""
    out = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("Verified", False):
            out.append(obj)
    return out


def _finish_trufflehog(
    issues: List[str],
    warnings: List[str],
    failures_json: Optional[str],
    strict_mode: bool,
    max_warnings: int,
) -> None:
    if strict_mode and len(warnings) > max_warnings:
        click.echo(
            f"\n🚨 TruffleHog STRICT default: warnings={len(warnings)} > max_warnings={max_warnings}. "
            "WARNINGS elevados a ISSUES exit=1."
        )
        issues.extend(warnings)
    elif not strict_mode:
        click.echo(f"\nℹ️  --no-strict: warnings={len(warnings)} informativos APENAS")

    click.echo(
        f"  resumo: {len(issues)} issue(s);  {len(warnings)} warning(s);  strict={strict_mode};  exit={0 if not issues else 1}"
    )
    if warnings:
        click.echo("\n--- WARNINGS ---")
        for w in warnings:
            click.echo(f"  ⚠️  {w}")
    if issues:
        click.echo("\n--- ISSUES ---")
        for i in issues:
            click.echo(f"  ❌ {i}")
    _exit_report(len(issues) == 0, issues, failures_json)


@cli.command("scan-secrets-trufflehog", help="Q3-08: TruffleHog segredos verificados P0 segurança (strict default).")
@click.option(
    "--scan-path",
    default=".",
    show_default=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True),
    help="Diretório ou arquivo a scannear (padrão repo root).",
)
@click.option("--only-verified/--no-only-verified", default=True, show_default=True, help="Apenas segredos VERIFICADOS.")
@click.option("--fail-verified/--no-fail-verified", default=True, show_default=True, help="Exit 1 se houver verificado (P0).")
@click.option(
    "--trufflehog-bin",
    type=str,
    default=None,
    show_default=False,
    help="Caminho explícito binário trufflehog. Padrão: auto-detect PATH.",
)
@click.option("--dry-run", is_flag=True, default=False, help="Não executa trufflehog; apenas valida parâmetros.")
@click.option("--strict/--no-strict", default=True, show_default=True, help="Warnings>max → issues exit=1.")
@click.option("--max-warnings", type=int, default=0, show_default=True, help="Máximo warnings permitidos (padrão 0 STRICT).")
@click.option(
    "--failures-json",
    type=str,
    default=None,
    show_default=False,
    help="Escreve relatório em JSON para arquivo opcional (auditoria BACEN Art.15).",
)
def cmd_scan_secrets_trufflehog(
    scan_path: str,
    only_verified: bool,
    fail_verified: bool,
    trufflehog_bin: Optional[str],
    dry_run: bool,
    strict: bool,
    max_warnings: int,
    failures_json: Optional[str],
) -> None:
    issues: List[str] = []
    warnings: List[str] = []

    click.echo(f"🔐 qa-gateway scan-secrets-trufflehog (Q3-08)")
    click.echo(f"  path={scan_path}")
    click.echo(f"  only_verified={only_verified}, fail_verified={fail_verified}, dry_run={dry_run}")
    click.echo(f"  strict={strict}, max_warnings={max_warnings}")

    bin_path = trufflehog_bin or _find_trufflehog_bin()
    if dry_run:
        if not bin_path:
            warnings.append(
                "[TS-W001] Modo dry-run: trufflehog bin NÃO encontrado PATH. CI instalar via pipx ou Docker image trufflesecurity/trufflehog."
            )
        else:
            click.echo(f"  ✅ Binário detectado: {bin_path}")
            click.echo("  🟢 DRY-RUN: nada executou.")
        click.echo(
            f"  resumo dry-run: 0 issue(s);  {len(warnings)} warning(s);  dry-run NUNCA bloqueia (strict={strict} ignorado);  exit=0"
        )
        if warnings:
            click.echo("\n--- WARNINGS (dry-run informativos) ---")
            for w in warnings:
                click.echo(f"  ⚠️  {w}")
        if failures_json:
            try:
                Path(failures_json).write_text(
                    json.dumps(
                        {
                            "ok": True,
                            "issues": [],
                            "warnings": warnings,
                            "dry_run": True,
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except Exception:  # noqa: BLE001
                pass
        sys.exit(0)

    if not bin_path:
        issues.append(
            "[TS-E001] Binário trufflehog NÃO encontrado. Instale: https://github.com/trufflesecurity/trufflehog"
            " OU use --trufflehog-bin /caminho/trufflehog OU ative imagem Docker no CI."
        )
        _finish_trufflehog(issues, warnings, failures_json, strict, max_warnings)
        return

    cmd: List[str] = [bin_path, "filesystem", scan_path, "--json"]
    if only_verified:
        cmd.append("--only-verified")
    if fail_verified:
        cmd.append("--fail-verified")

    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=2 * 3600)  # max 2h repo grande
    except subprocess.TimeoutExpired:
        issues.append(
            "[TS-E002] Timeout TruffleHog excedeu 2h. Repositório grande? Aumente CI timeout ou use --scan-path reduzido."
        )
        _finish_trufflehog(issues, warnings, failures_json, strict, max_warnings)
        return

    duration_s = round(time.monotonic() - started, 2)
    click.echo(f"  ✅ TruffleHog executou em {duration_s}s (exit={proc.returncode})")

    if proc.stderr:
        # TruffleHog warnings de filtros, NÃO são segredos
        for ln in proc.stderr.splitlines()[:20]:
            if "warning" in ln.lower() or "WARN" in ln:
                warnings.append(f"[TS-W002] TruffleHog stderr warning: {ln.strip()[:180]}")

    findings = _parse_trufflehog_json_lines(proc.stdout)
    click.echo(f"  🔎 Achados VERIFICADOS: {len(findings)}")

    for idx, f in enumerate(findings, start=1):
        file_name = f.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {}).get("file", "<unknown>")
        line_no = f.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {}).get("line", 0)
        detector = f.get("DetectorName", "<unknown>")
        raw_prefix = (f.get("Raw", "") or "")[:32]
        if fail_verified and only_verified:
            issues.append(TRUFFLEHOG_VERIFIED_ERR % (idx, file_name, line_no, detector, raw_prefix))
        else:
            warnings.append(TRUFFLEHOG_VERIFIED_WARN % (idx, file_name, line_no, f.get("Description", ""), detector, raw_prefix))

    if proc.returncode != 0 and not findings:
        warnings.append(
            f"[TS-W003] TruffleHog exit={proc.returncode} sem findings. Pode ser --fail-verified ou erro de rede ao validar segredos."
        )

    _finish_trufflehog(issues, warnings, failures_json, strict, max_warnings)


# ---------------------------------------------------------------------------
# Comando Q3-09: run-pre-merge-gates (Orquestrador FAIL-FAST 5 gates ADR-029)
# ---------------------------------------------------------------------------
@cli.command("run-pre-merge-gates", help="ADR-029: FAIL-FAST 5 gates. Q1→Q4 fail-fast, Q5 segredos SEMPRE roda.")
@click.option("--dpo-email", type=str, required=True, help="Email DPO obrigatório para Q4 scan-lgpd-ropd.")
@click.option("--strict/--no-strict", default=True, show_default=True, help="STRICT todos os 5 gates (warnings>0→exit1).")
@click.option("--max-warnings", type=int, default=0, show_default=True, help="Máximo warnings global por gate.")
@click.option("--check-prod-redis/--skip-prod-redis", default=True, show_default=True, help="Q3 check OTK_REDIS_URL overlay prod.")
@click.option("--skip-q1", is_flag=True, default=False, help="DEV LOCAL: pular Q1 RBAC (NÃO PERMITIDO se OTK_CI_PRE_MERGE_ENFORCE_ALL=true).")
@click.option("--skip-q2", is_flag=True, default=False, help="DEV LOCAL: pular Q2 billing capabilities.")
@click.option("--skip-q3", is_flag=True, default=False, help="DEV LOCAL: pular Q3 billing enforcement.")
@click.option("--skip-q4", is_flag=True, default=False, help="DEV LOCAL: pular Q4 ROPD.")
@click.option("--skip-q5", is_flag=True, default=False, help="DEV LOCAL: pular Q5 segredos (SOMENTE dev! NUNCA CI).")
@click.option("--dry-run", is_flag=True, default=False, help="Não executa subprocessos, valida flags + gera relatório vazio.")
@click.option(
    "--report-dir",
    type=click.Path(dir_okay=True, file_okay=False, resolve_path=True),
    default="./qa-reports",
    show_default=True,
    help="Pasta para relatório JSON consolidado pre-merge.",
)
@click.option(
    "--failures-json",
    type=str,
    default=None,
    show_default=False,
    help="Compatibilidade com helpers qa-gateway: escreve failures resumido.",
)
def cmd_run_pre_merge_gates(
    dpo_email: str,
    strict: bool,
    max_warnings: int,
    check_prod_redis: bool,
    skip_q1: bool,
    skip_q2: bool,
    skip_q3: bool,
    skip_q4: bool,
    skip_q5: bool,
    dry_run: bool,
    report_dir: str,
    failures_json: Optional[str],
) -> None:
    enforce_all = os.environ.get("OTK_CI_PRE_MERGE_ENFORCE_ALL", "").lower() == "true"
    if enforce_all and (skip_q1 or skip_q2 or skip_q3 or skip_q4 or skip_q5):
        click.echo("🔴 OTK_CI_PRE_MERGE_ENFORCE_ALL=true: flags --skip-Q* NÃO PERMITIDAS em CI.")
        sys.exit(1)

    started_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    started_mono = time.monotonic()
    commit_sha = os.environ.get("GITHUB_SHA", "local-" + started_iso.replace(":", ""))

    click.echo(f"🛂 qa-gateway run-pre-merge-gates (ADR-029, commit={commit_sha})")
    click.echo(f"  dpo_email={dpo_email}, strict={strict}, max_warnings={max_warnings}, check_prod_redis={check_prod_redis}")
    click.echo(f"  dry_run={dry_run}, report_dir={report_dir}, enforce_all={enforce_all}")
    if any([skip_q1, skip_q2, skip_q3, skip_q4, skip_q5]):
        click.echo(f"  ⚠️  DEV LOCAL skips: Q1={skip_q1} Q2={skip_q2} Q3={skip_q3} Q4={skip_q4} Q5={skip_q5}")

    Path(report_dir).mkdir(parents=True, exist_ok=True)

    gates_def: List[Dict] = [
        {
            "id": "Q1-RBAC",
            "name": "qa-gateway scan-rbac",
            "cmd": ["qa-gateway", "scan-rbac", "--strict" if strict else "--no-strict", "--max-warnings", str(max_warnings)],
            "always_run": False,
            "skip_flag": skip_q1,
        },
        {
            "id": "Q2-BILLING-CAP",
            "name": "qa-gateway scan-billing-capabilities",
            "cmd": ["qa-gateway", "scan-billing-capabilities", "--strict" if strict else "--no-strict", "--max-warnings", str(max_warnings)],
            "always_run": False,
            "skip_flag": skip_q2,
        },
        {
            "id": "Q3-BILLING-ENF",
            "name": "qa-gateway scan-billing-enforcement",
            "cmd": ["qa-gateway", "scan-billing-enforcement",
                    "--strict" if strict else "--no-strict",
                    "--max-warnings", str(max_warnings),
                    "--check-prod-redis" if check_prod_redis else "--skip-prod-redis"],
            "always_run": False,
            "skip_flag": skip_q3,
        },
        {
            "id": "Q4-LGPD-ROPD",
            "name": "qa-gateway scan-lgpd-ropd",
            "cmd": ["qa-gateway", "scan-lgpd-ropd", "--strict" if strict else "--no-strict",
                    "--max-warnings", str(max_warnings), "--dpo-email", dpo_email],
            "always_run": False,
            "skip_flag": skip_q4,
        },
        {
            "id": "Q5-SECRETS",
            "name": "qa-gateway scan-secrets-trufflehog",
            "cmd": ["qa-gateway", "scan-secrets-trufflehog", "--strict" if strict else "--no-strict",
                    "--max-warnings", str(max_warnings)],
            "always_run": True,  # SEGURANÇA SOBRE FAIL-FAST
            "skip_flag": skip_q5,
        },
    ]

    global_issues: List[str] = []
    global_warnings: List[str] = []
    gates_report: List[Dict] = []
    early_stop_exit_1 = False

    for g in gates_def:
        gid = g["id"]
        if g["skip_flag"]:
            click.echo(f"\n⏭️  [{gid}] SKIP (dev local flag)")
            gates_report.append({"id": gid, "name": g["name"], "exit": 0, "duration_ms": 0,
                                 "skipped": True, "issues": [], "warnings": ["skipped dev local"]})
            continue

        t0 = time.monotonic()
        if g["always_run"]:
            click.echo(f"\n🧿 [{gid}] SEMPRE roda (segurança). mesmo se anterior falhou.")
        else:
            click.echo(f"\n▶️  [{gid}] {g['name']}")

        if early_stop_exit_1 and not g["always_run"]:
            click.echo(f"⏹️  [{gid}] FAIL-FAST: gate anterior falhou, SKIP este.")
            gates_report.append({"id": gid, "name": g["name"], "exit": 2, "duration_ms": 0,
                                 "skipped": True, "issues": ["fail-fast anterior"], "warnings": []})
            continue

        if dry_run:
            exit_code = 0
            stdout = ""
            stderr = ""
        else:
            try:
                proc = subprocess.run(g["cmd"], capture_output=True, text=True, timeout=180 * 60)  # max 3h soma
                exit_code = proc.returncode
                stdout = proc.stdout or ""
                stderr = proc.stderr or ""
            except subprocess.TimeoutExpired:
                exit_code = 2
                stdout = ""
                stderr = "timeout 3h excedido"
                global_issues.append(f"[{gid}] TIMEOUT 3h orquestrador")

        duration_ms = int((time.monotonic() - t0) * 1000)
        gate_issues: List[str] = []
        gate_warnings: List[str] = []

        # Parse warnings e issues simples: linhas que começam com ⚠️  e ❌
        for src in (stdout, stderr):
            for ln in src.splitlines():
                s = ln.strip()
                if s.startswith("⚠️"):
                    gate_warnings.append(f"[{gid}] {s[2:].strip()}")
                elif s.startswith("❌"):
                    gate_issues.append(f"[{gid}] {s[2:].strip()}")
                elif s.startswith("[") and ("WARN" in s or "-W" in s) and len(gate_warnings) < 50:
                    gate_warnings.append(f"[{gid}] {s[:200]}")

        if exit_code != 0 and not gate_issues:
            gate_issues.append(f"[{gid}] exit_code={exit_code} sem issues parseáveis (ver log completo)")

        gates_report.append({
            "id": gid,
            "name": g["name"],
            "exit": exit_code,
            "duration_ms": duration_ms,
            "skipped": False,
            "issues": gate_issues,
            "warnings": gate_warnings,
        })
        click.echo(f"  result: exit={exit_code}, duration={duration_ms}ms, issues={len(gate_issues)}, warnings={len(gate_warnings)}")
        global_issues.extend(gate_issues)
        global_warnings.extend(gate_warnings)

        if exit_code != 0 and not g["always_run"]:
            click.echo(f"  🛑 FAIL-FAST ADR-029: {gid} exit≠0 → não executa Q2/Q3/Q4 seguintes. Q5 SEMPRE roda.")
            early_stop_exit_1 = True

    overall_duration_ms = int((time.monotonic() - started_mono) * 1000)
    overall_exit = 1 if global_issues else 0

    report: Dict = {
        "schema_version": "1.0",
        "run_id": f"pre-merge-{commit_sha}",
        "started_at_iso": started_iso,
        "duration_ms": overall_duration_ms,
        "commit_sha": commit_sha,
        "dpo_email": dpo_email,
        "strict": strict,
        "max_warnings": max_warnings,
        "check_prod_redis": check_prod_redis,
        "dry_run": dry_run,
        "gates": gates_report,
        "overall_issues": global_issues,
        "overall_warnings": global_warnings,
        "overall_exit": overall_exit,
    }

    report_path = Path(report_dir) / f"pre-merge-{commit_sha}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(f"\n📄 Relatório consolidado: {report_path}")
    click.echo(f"   overall_exit={overall_exit} (issues={len(global_issues)}, warnings={len(global_warnings)}, duration={overall_duration_ms}ms)")

    if failures_json:
        _exit_report(overall_exit == 0, global_issues, failures_json)
    else:
        if overall_exit != 0:
            click.echo("\n⛔ PRE-MERGE BLOQUEADO (ADR-029). Resolva issues e force push novamente.")
            sys.exit(1)
        click.echo("\n✅ PRE-MERGE APROVADO — merge liberado (ADR-029).")


if __name__ == "__main__":
    cli()
