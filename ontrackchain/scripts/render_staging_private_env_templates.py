#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = REPO_ROOT / ".env.staging.example"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "staging" / "templates"
BASELINE_FILENAME = "staging-private-baseline.example.env"
HOMOLOGATED_FILENAME = "staging-private-homologated.example.env"
TOKEN_KEY = "ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN"
MFA_HOMOLOGATED_KEY = "MFA_EXTERNAL_PROVIDER_HOMOLOGATED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def render_mode_template(*, env_lines: list[str], mode: str, generated_at: str) -> str:
    is_homologated = mode == "homologated"
    header_lines = [
        f"# Template redigido gerado em {generated_at}",
        f"# Modo da janela: {mode}",
        "# Arquivo derivado de .env.staging.example; preencher apenas em canal seguro.",
        (
            "# Neste modo, ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN pode permanecer como placeholder "
            "enquanto MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false."
            if not is_homologated
            else "# Neste modo, ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN deve ser preenchido com token OIDC administrativo valido."
        ),
        "",
    ]

    rendered_lines: list[str] = []
    for raw_line in env_lines:
        stripped = raw_line.strip()
        if stripped.startswith(f"{MFA_HOMOLOGATED_KEY}="):
            rendered_lines.append(f"{MFA_HOMOLOGATED_KEY}={'true' if is_homologated else 'false'}")
            continue
        if stripped.startswith(f"{TOKEN_KEY}="):
            if is_homologated:
                rendered_lines.append("# Obrigatorio quando MFA federado homologado fizer parte da janela.")
            else:
                rendered_lines.append("# Opcional nesta janela; o checker aceita o placeholder enquanto MFA homologado estiver desligado.")
            rendered_lines.append(raw_line)
            continue
        rendered_lines.append(raw_line)

    return "\n".join(header_lines + rendered_lines).rstrip() + "\n"


def write_templates(*, env_file: Path, output_dir: Path, generated_at: str) -> dict[str, str]:
    env_lines = env_file.read_text(encoding="utf-8").splitlines()
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_path = output_dir / BASELINE_FILENAME
    homologated_path = output_dir / HOMOLOGATED_FILENAME

    baseline_path.write_text(
        render_mode_template(env_lines=env_lines, mode="baseline", generated_at=generated_at),
        encoding="utf-8",
    )
    homologated_path.write_text(
        render_mode_template(env_lines=env_lines, mode="homologated", generated_at=generated_at),
        encoding="utf-8",
    )

    return {
        "baseline": str(baseline_path),
        "homologated": str(homologated_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera templates redigidos de .env.staging.private para as janelas baseline e homologada."
    )
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--generated-at", help="timestamp ISO-8601 para reproducibilidade")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_file = Path(args.env_file)
    generated_at = args.generated_at or utc_now().isoformat()

    if not env_file.exists():
        payload = {
            "kind": "staging_private_env_templates",
            "status": "failed",
            "errors": [f"arquivo_ausente: {env_file}"],
        }
        sys.stderr.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
        return 1

    files = write_templates(
        env_file=env_file,
        output_dir=Path(args.output_dir),
        generated_at=generated_at,
    )
    payload = {
        "kind": "staging_private_env_templates",
        "status": "ok",
        "generated_at": generated_at,
        "env_file": str(env_file),
        "output_dir": str(Path(args.output_dir)),
        "files": files,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
