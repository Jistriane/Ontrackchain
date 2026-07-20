#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_REQUIRED_IMPORTS = [
    "fastapi",
    "pydantic_settings",
    "psycopg_pool",
]


def _run(command: list[str], *, cwd: Path) -> int:
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=str(cwd), check=False)
    return completed.returncode


def _command_succeeds(command: list[str], *, cwd: Path) -> bool:
    completed = subprocess.run(command, cwd=str(cwd), check=False, capture_output=True, text=True)
    return completed.returncode == 0


def _local_runtime_is_ready(*, app_dir: Path, required_imports: list[str]) -> bool:
    if not required_imports:
        return True
    dependency_check = [
        "python3",
        "-c",
        f"import {', '.join(required_imports)}",
    ]
    return _command_succeeds(dependency_check, cwd=app_dir)


def _build_docker_compose_command(
    *,
    repo_root: Path,
    app_dir: Path,
    docker_service: str,
    docker_mount_repo_root: bool,
    docker_repo_root: str,
    docker_workdir: str,
    python_args: list[str],
) -> list[str]:
    mount_source = repo_root if docker_mount_repo_root else app_dir
    mount_target = docker_repo_root if docker_mount_repo_root else docker_workdir
    return [
        "docker",
        "compose",
        "run",
        "--rm",
        "--no-deps",
        "-T",
        "-v",
        f"{mount_source}:{mount_target}",
        "-w",
        docker_workdir,
        docker_service,
        "python",
        *python_args,
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Roda uma suite unittest de app Python com fallback Docker Compose quando o runtime local nao estiver pronto."
    )
    parser.add_argument(
        "--app-dir",
        required=True,
        help="Diretorio do app relativo a raiz do repositorio.",
    )
    parser.add_argument(
        "--docker-service",
        required=True,
        help="Servico Docker Compose usado no fallback.",
    )
    parser.add_argument(
        "--skip-py-compile",
        action="store_true",
        help="Pula a etapa de py_compile.",
    )
    parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        default=[],
        help="Modulo unittest. Pode ser repetido.",
    )
    parser.add_argument(
        "--py-compile-file",
        action="append",
        dest="py_compile_files",
        default=[],
        help="Arquivo Python para py_compile relativo ao app. Pode ser repetido.",
    )
    parser.add_argument(
        "--required-import",
        action="append",
        dest="required_imports",
        default=[],
        help="Import necessario para considerar o runtime local pronto. Pode ser repetido.",
    )
    parser.add_argument(
        "--force-docker",
        action="store_true",
        help="Forca execucao via Docker Compose mesmo quando o runtime local estiver disponivel.",
    )
    parser.add_argument(
        "--docker-mount-repo-root",
        action="store_true",
        help="Monta a raiz do repositorio no container em vez de apenas o diretorio do app.",
    )
    parser.add_argument(
        "--docker-repo-root",
        default="/workspaces/ontrackchain",
        help="Destino da montagem da raiz do repositorio quando --docker-mount-repo-root estiver ativo.",
    )
    parser.add_argument(
        "--docker-workdir",
        default="/app",
        help="Working directory dentro do container para py_compile/unittest.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    app_dir = (repo_root / args.app_dir).resolve()
    if not app_dir.exists():
        sys.stderr.write(f"Diretorio do app nao encontrado: {app_dir}\n")
        return 1

    if not args.modules:
        sys.stderr.write("Informe ao menos um --module para a suite unittest.\n")
        return 1

    required_imports = args.required_imports or list(DEFAULT_REQUIRED_IMPORTS)
    use_local_runtime = not args.force_docker and _local_runtime_is_ready(
        app_dir=app_dir,
        required_imports=required_imports,
    )
    if use_local_runtime:
        execution_cwd = app_dir
        py_compile_command = [
            "python3",
            "-m",
            "py_compile",
            *args.py_compile_files,
        ]
        unittest_command = [
            "python3",
            "-m",
            "unittest",
            *args.modules,
        ]
    else:
        reason = "--force-docker" if args.force_docker else "dependencias Python locais indisponiveis"
        print(f"# usando fallback Docker Compose ({reason})")
        execution_cwd = repo_root
        py_compile_command = _build_docker_compose_command(
            repo_root=repo_root,
            app_dir=app_dir,
            docker_service=args.docker_service,
            docker_mount_repo_root=args.docker_mount_repo_root,
            docker_repo_root=args.docker_repo_root,
            docker_workdir=args.docker_workdir,
            python_args=["-m", "py_compile", *args.py_compile_files],
        )
        unittest_command = _build_docker_compose_command(
            repo_root=repo_root,
            app_dir=app_dir,
            docker_service=args.docker_service,
            docker_mount_repo_root=args.docker_mount_repo_root,
            docker_repo_root=args.docker_repo_root,
            docker_workdir=args.docker_workdir,
            python_args=["-m", "unittest", *args.modules],
        )

    if not args.skip_py_compile and args.py_compile_files:
        exit_code = _run(py_compile_command, cwd=execution_cwd)
        if exit_code != 0:
            return exit_code

    return _run(unittest_command, cwd=execution_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
