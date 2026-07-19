#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent


def load_module(module_name: str, relative_path: str):
    module_path = ROOT_DIR / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"nao_foi_possivel_carregar_modulo: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WEEKLY_MODULE = load_module(
    "render_staging_window_weekly_governance",
    "scripts/render_staging_window_weekly_governance.py",
)


DEFAULT_BOARD_FILE = ROOT_DIR / "docs" / "project-operational-execution-board.md"


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def derive_p0_04_status(*, p0_02_status: str, p0_03_status: str) -> str:
    promotable = {"ready_for_validation", "done"}
    if p0_02_status in promotable and p0_03_status in promotable:
        return "ready"
    return "todo"


def derive_regulatory_scope_label(*, weekly_model: dict[str, str]) -> str:
    p0_02_in_scope = weekly_model.get("p0_02_in_scope") == "true"
    p0_03_in_scope = weekly_model.get("p0_03_in_scope") == "true"
    if p0_02_in_scope and p0_03_in_scope:
        return "P0-02/P0-03"
    if p0_02_in_scope:
        return "P0-02"
    if p0_03_in_scope:
        return "P0-03"
    return "none"


def replace_line(lines: list[str], prefix: str, new_line: str, *, required: bool = True) -> None:
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = new_line
            return
    if required:
        raise ValueError(f"linha_nao_encontrada: {prefix}")


def build_model(*, payload: dict[str, Any], payload_file: Path) -> dict[str, str]:
    weekly_model = WEEKLY_MODULE.build_weekly_sync_model(
        payload=payload,
        payload_file=payload_file,
        run_url="pending",
    )
    p0_04_status = derive_p0_04_status(
        p0_02_status=weekly_model["p0_02_status"],
        p0_03_status=weekly_model["p0_03_status"],
    )
    regulatory_scope_label = derive_regulatory_scope_label(weekly_model=weekly_model)
    return {
        "window_id": weekly_model["window_id"],
        "regulatory_scope_label": regulatory_scope_label,
        "regulatory_scope_is_combined": "true" if regulatory_scope_label == "P0-02/P0-03" else "false",
        "blocking_classification": weekly_model.get("blocking_classification", "unknown"),
        "blocking_summary": weekly_model.get("blocking_summary", "indisponivel"),
        "p0_02_in_scope": weekly_model.get("p0_02_in_scope", "false"),
        "p0_03_in_scope": weekly_model.get("p0_03_in_scope", "false"),
        "p0_01_status": weekly_model["p0_01_status"],
        "p0_02_status": weekly_model["p0_02_status"],
        "p0_03_status": weekly_model["p0_03_status"],
        "p0_04_status": p0_04_status,
    }


def update_operational_board_markdown(content: str, model: dict[str, str]) -> str:
    lines = content.splitlines()
    regulatory_scope_label = model["regulatory_scope_label"]
    p0_02_attempt_note = (
        "tentativa atual cobre `P0-02` e ja existe trilho de evidência para execucao assim que a credencial AML/KYT chegar"
        if model["p0_02_in_scope"] == "true"
        else "trilha fora do escopo da tentativa atual; manter `P0-02` pronta para a janela combinada oficial"
    )
    p0_03_attempt_note = (
        "tentativa atual cobre `P0-03` e ja existe rito claro para execucao assim que a URL tokenizada real chegar"
        if model["p0_03_in_scope"] == "true"
        else "trilha fora do escopo da tentativa atual; manter `P0-03` pronta para a janela combinada oficial"
    )
    p0_04_dependencies = (
        "`P0-02`, `P0-03`"
        if model["regulatory_scope_is_combined"] == "true"
        else f"tentativa atual: `{regulatory_scope_label}`; promocao oficial ainda exige `P0-02` + `P0-03`"
    )
    p0_04_closure = (
        "bundle reflete AML/KYT + sancoes UE sem erro residual nao classificado"
        if model["regulatory_scope_is_combined"] == "true"
        else (
            f"tentativa atual cobre `{regulatory_scope_label}`, mas a promocao oficial so fecha quando `P0-02` e `P0-03` convergirem na mesma trilha revisavel"
        )
    )
    p0_04_rationale = (
        "depende diretamente da conclusao operacional de `P0-02` e `P0-03`"
        if model["regulatory_scope_is_combined"] == "true"
        else (
            f"tentativa atual cobre `{regulatory_scope_label}`, mas `P0-04` ainda depende do fechamento combinado de `P0-02` e `P0-03`"
        )
    )
    if model["blocking_classification"] == "regulatory_blocked":
        p0_02_attempt_note = f"{p0_02_attempt_note}; bloqueio dominante atual: {model['blocking_summary']}"
        p0_03_attempt_note = f"{p0_03_attempt_note}; bloqueio dominante atual: {model['blocking_summary']}"
        p0_04_rationale = f"{p0_04_rationale}; bloqueio dominante atual: {model['blocking_summary']}"
    elif model["blocking_classification"] == "technical_gate_blocked":
        p0_04_rationale = f"{p0_04_rationale}; falha tecnica dominante: {model['blocking_summary']}"
    replace_line(
        lines,
        "| `P0-01` |",
        "| `P0-01` | "
        f"`{model['p0_01_status']}` | Homologar `OIDC + MFA` serio | Backend/Auth | owner IdP, ambiente serio, claims finais | "
        "`preflight_oidc_serious_env.py` verde, `smoke_auth_oidc_mode.py` verde, bundle `<window>-oidc-readiness-bundle.json`, Playwright critico verde | muito alto | "
        "fluxos sensiveis exigem auth serio e MFA homologado sem fallback silencioso |",
    )
    replace_line(
        lines,
        "| `P0-02` |",
        "| `P0-02` | "
        f"`{model['p0_02_status']}` | Homologar `AML/KYT live` | Backend/Compliance | credencial real do provider | "
        "`check_compliance_provider_runtime.py` verde + artefato JSON | muito alto | readiness interna e API publica convergem com provider `live` |",
    )
    replace_line(
        lines,
        "| `P0-03` |",
        "| `P0-03` | "
        f"`{model['p0_03_status']}` | Ativar feed UE real | Backend/Compliance | URL tokenizada valida | "
        "JSONs da janela UE + `check_sanctions_sync_status.py` verde | muito alto | `EU_CONSOLIDATED` fica valido e os artefatos da janela sao persistidos |",
    )
    replace_line(
        lines,
        "| `P0-04` |",
        "| `P0-04` | "
        f"`{model['p0_04_status']}` | Gerar bundle regulatorio oficial | Platform/SRE | {p0_04_dependencies} | "
        f"`<window>-regulatory-readiness-bundle.json` | muito alto | {p0_04_closure} |",
    )
    replace_line(
        lines,
        "| `P0-01` | `blocked` | ainda depende de owner IdP, ambiente serio e validacao externa de MFA |",
        "| `P0-01` | "
        f"`{model['p0_01_status']}` | ainda depende de owner IdP, ambiente serio e validacao externa de MFA | "
        "mover para `in_progress` so quando houver owner confirmado e trilho serio verificavel |",
        required=False,
    )
    replace_line(
        lines,
        "| `P0-02` | `ready` | a trilha ja tem owner e checker definido, mas ainda depende de credencial real |",
        "| `P0-02` | "
        f"`{model['p0_02_status']}` | {p0_02_attempt_note} | "
        "mover para `in_progress` quando a credencial AML/KYT estiver disponivel para execucao |",
        required=False,
    )
    replace_line(
        lines,
        "| `P0-03` | `ready` | a trilha ja tem owner e rito claro, mas ainda depende de URL tokenizada real da UE |",
        "| `P0-03` | "
        f"`{model['p0_03_status']}` | {p0_03_attempt_note} | "
        "mover para `in_progress` quando a URL real estiver confirmada no ambiente |",
        required=False,
    )
    replace_line(
        lines,
        "| `P0-04` | `todo` | depende diretamente da conclusao operacional de `P0-02` e `P0-03` |",
        "| `P0-04` | "
        f"`{model['p0_04_status']}` | {p0_04_rationale} | "
        "mover para `ready` apenas depois que `P0-02` e `P0-03` estiverem ao menos em `ready_for_validation` |",
        required=False,
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sincroniza o board operacional global a partir do payload consolidado da janela seria."
    )
    parser.add_argument("--payload-file", required=True)
    parser.add_argument("--board-file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload_file = Path(args.payload_file)
    board_file = Path(args.board_file) if args.board_file else DEFAULT_BOARD_FILE

    try:
        payload = load_json_file(payload_file)
        model = build_model(payload=payload, payload_file=payload_file)
        content = board_file.read_text(encoding="utf-8")
        updated_content = update_operational_board_markdown(content, model)
        board_file.write_text(updated_content, encoding="utf-8")
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "staging_window_operational_board_render",
                    "status": "failed",
                    "payload_file": str(payload_file),
                    "errors": [str(exc)],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 1

    sys.stdout.write(
        json.dumps(
            {
                "kind": "staging_window_operational_board_render",
                "status": "ok",
                "payload_file": str(payload_file),
                "board_file": str(board_file),
                "window_id": model["window_id"],
                "blocking_classification": model["blocking_classification"],
                "blocking_summary": model["blocking_summary"],
                "p0_01_status": model["p0_01_status"],
                "p0_02_status": model["p0_02_status"],
                "p0_03_status": model["p0_03_status"],
                "p0_04_status": model["p0_04_status"],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
