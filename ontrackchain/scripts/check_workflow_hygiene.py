#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT.parent / ".github" / "workflows"
REQUIRED_CHECK_SNIPPET = "make check-workflow-hygiene"

SECRETS_IN_IF_RE = re.compile(r"^\s*if:\s*.*\bsecrets\.", re.IGNORECASE)
HEREDOC_QUOTED_RE = re.compile(r"<<\s*'([A-Za-z_][A-Za-z0-9_]*)'")
SHELL_EXPANSION_RE = re.compile(r"\$\(|\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]*")
EXECUTABLE_HYGIENE_CMD_RE = re.compile(
    r"(^|[;&|]\s*|\bthen\s+|\bdo\s+)"
    r"(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*"
    r"make\s+check-workflow-hygiene\b"
)


def _display_workflow_path(workflow: Path) -> Path:
    try:
        return workflow.relative_to(REPO_ROOT.parent)
    except ValueError:
        # Allows unit tests to validate logic using temporary directories.
        return workflow


def check_secrets_in_if(workflow: Path, lines: list[str], failures: list[str]) -> None:
    for line_no, line in enumerate(lines, start=1):
        if SECRETS_IN_IF_RE.search(line):
            failures.append(
                f"{workflow}:L{line_no}: uso de secrets em if pode quebrar validacao local; mova o guard para dentro de run"
            )


def check_context_issue_number(workflow: Path, content: str, failures: list[str]) -> None:
    if "context.issue.number" not in content:
        return

    # Heuristica simples: somente permitir quando workflow declara eventos de issue/PR.
    has_issue_events = any(token in content for token in ("pull_request", "issues:", "issue_comment"))
    if not has_issue_events:
        failures.append(
            f"{workflow}: uso de context.issue.number sem evento de issue/PR; prefira numero vindo de output/lookup"
        )


def check_quoted_heredoc_with_expansion(workflow: Path, lines: list[str], failures: list[str]) -> None:
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        match = HEREDOC_QUOTED_RE.search(line)
        if not match:
            idx += 1
            continue

        marker = match.group(1)
        start_line = idx + 1
        idx += 1
        block_has_expansion = False

        while idx < len(lines):
            current = lines[idx]
            if current.strip() == marker:
                break
            if SHELL_EXPANSION_RE.search(current):
                block_has_expansion = True
            idx += 1

        if block_has_expansion:
            failures.append(
                f"{workflow}:L{start_line}: heredoc quoted (<<'{marker}') com expansao de shell no corpo; remova aspas do marcador"
            )

        idx += 1


def check_required_hygiene_step(workflow: Path, content: str, failures: list[str]) -> None:
    lines = content.splitlines()
    has_required_step = False

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        inline_run_match = re.search(r"^\s*-\s*run:\s*(.*)$", line)
        if inline_run_match:
            inline_cmd = inline_run_match.group(1).strip()
            if EXECUTABLE_HYGIENE_CMD_RE.search(inline_cmd):
                has_required_step = True
                break

        if stripped.startswith("run:"):
            run_cmd = stripped.split("run:", 1)[1].strip()
            if EXECUTABLE_HYGIENE_CMD_RE.search(run_cmd):
                has_required_step = True
                break

        if EXECUTABLE_HYGIENE_CMD_RE.search(stripped):
            has_required_step = True
            break

    if not has_required_step:
        failures.append(
            f"{workflow}: ausencia do passo obrigatorio de higiene (`{REQUIRED_CHECK_SNIPPET}`)"
        )


def _list_workflow_files() -> list[Path]:
    workflow_files = list(WORKFLOWS_DIR.glob("*.yml"))
    workflow_files.extend(WORKFLOWS_DIR.glob("*.yaml"))
    return sorted(workflow_files)


def main() -> int:
    if not WORKFLOWS_DIR.exists():
        sys.stderr.write(f"Diretorio de workflows nao encontrado: {WORKFLOWS_DIR}\n")
        return 1

    failures: list[str] = []
    workflow_files = _list_workflow_files()

    for workflow in workflow_files:
        content = workflow.read_text(encoding="utf-8")
        lines = content.splitlines()
        display_workflow = _display_workflow_path(workflow)
        check_required_hygiene_step(display_workflow, content, failures)
        check_secrets_in_if(display_workflow, lines, failures)
        check_context_issue_number(display_workflow, content, failures)
        check_quoted_heredoc_with_expansion(display_workflow, lines, failures)

    if failures:
        sys.stderr.write("\n".join(failures) + "\n")
        return 1

    print("OK: workflow hygiene sem regressao detectada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
