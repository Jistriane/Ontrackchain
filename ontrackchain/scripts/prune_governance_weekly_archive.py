import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class ArchiveTarget:
    directory: Path
    update_readme: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_file_date(file_name: str) -> date | None:
    match = re.match(r"^(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})-", file_name)
    if not match:
        return None
    try:
        return date(int(match.group("y")), int(match.group("m")), int(match.group("d")))
    except ValueError:
        return None


def _first_heading(path: Path) -> str | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("# "):
                    return line[2:].strip()
    except OSError:
        return None
    return None


def _render_weekly_index_lines(weekly_dir: Path) -> list[str]:
    entries: list[tuple[date, str, str]] = []
    for md_file in sorted(weekly_dir.glob("*.md")):
        if md_file.name == "README.md":
            continue
        file_date = _parse_file_date(md_file.name)
        if not file_date:
            continue
        title = _first_heading(md_file) or md_file.name
        entries.append((file_date, md_file.name, title))

    entries.sort(key=lambda item: (item[0], item[1]))
    return [f"- [{title}](./{file_name})" for _, file_name, title in entries]


def _update_weekly_readme(weekly_dir: Path) -> None:
    readme = weekly_dir / "README.md"
    if not readme.exists():
        return
    content = readme.read_text(encoding="utf-8", errors="ignore").splitlines()

    start = None
    end = None
    for idx, line in enumerate(content):
        if line.strip() == "## Documentos Disponiveis":
            start = idx
            continue
        if start is not None and idx > start and line.startswith("## "):
            end = idx
            break

    if start is None:
        return
    if end is None:
        end = len(content)

    before = content[: start + 1]
    after = content[end:]
    middle = [""] + _render_weekly_index_lines(weekly_dir) + [""]

    readme.write_text("\n".join(before + middle + after).rstrip() + "\n", encoding="utf-8")


def _prune_directory(directory: Path, cutoff: date, dry_run: bool) -> list[Path]:
    pruned: list[Path] = []
    for md_file in sorted(directory.glob("*.md")):
        if md_file.name == "README.md":
            continue
        file_date = _parse_file_date(md_file.name)
        if not file_date:
            continue
        if file_date >= cutoff:
            continue
        pruned.append(md_file)
        if not dry_run:
            md_file.unlink(missing_ok=True)
    return pruned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--today", default=None)

    args = parser.parse_args()

    today = date.today()
    if args.today:
        today = datetime.strptime(args.today, "%Y-%m-%d").date()

    cutoff = today - timedelta(days=args.days)

    root = _repo_root()
    targets = [
        ArchiveTarget(
            directory=root / "docs" / "governance-weekly" / "archive" / "weekly",
            update_readme=True,
        ),
        ArchiveTarget(
            directory=root / "docs" / "governance-weekly" / "archive" / "sprint-tracking",
            update_readme=False,
        ),
    ]

    total_pruned = 0
    for target in targets:
        if not target.directory.exists():
            continue
        pruned = _prune_directory(target.directory, cutoff=cutoff, dry_run=args.dry_run)
        total_pruned += len(pruned)
        if target.update_readme and not args.dry_run:
            _update_weekly_readme(target.directory)

    if args.dry_run:
        print(f"dry-run: would prune {total_pruned} files older than {cutoff.isoformat()}")
    else:
        print(f"pruned {total_pruned} files older than {cutoff.isoformat()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
