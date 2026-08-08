from __future__ import annotations

import argparse
import re
from pathlib import Path


def _safe_word(word: str) -> str:
    escaped = re.escape(word)
    return rf"(?<![-_/\.])\b{escaped}\b(?![-_/\.])"


REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(_safe_word("autenticacao"), re.IGNORECASE), "autenticação"),
    (re.compile(_safe_word("autorizacao"), re.IGNORECASE), "autorização"),
    (re.compile(_safe_word("configuracao"), re.IGNORECASE), "configuração"),
    (re.compile(_safe_word("consolidacao"), re.IGNORECASE), "consolidação"),
    (re.compile(_safe_word("documentacao"), re.IGNORECASE), "documentação"),
    (re.compile(_safe_word("evidencia"), re.IGNORECASE), "evidência"),
    (re.compile(_safe_word("evidencias"), re.IGNORECASE), "evidências"),
    (re.compile(_safe_word("governanca"), re.IGNORECASE), "governança"),
    (re.compile(_safe_word("integracao"), re.IGNORECASE), "integração"),
    (re.compile(_safe_word("integracoes"), re.IGNORECASE), "integrações"),
    (re.compile(_safe_word("migracao"), re.IGNORECASE), "migração"),
    (re.compile(_safe_word("migracoes"), re.IGNORECASE), "migrações"),
    (re.compile(_safe_word("observacao"), re.IGNORECASE), "observação"),
    (re.compile(_safe_word("observacoes"), re.IGNORECASE), "observações"),
    (re.compile(_safe_word("operacao"), re.IGNORECASE), "operação"),
    (re.compile(_safe_word("operacoes"), re.IGNORECASE), "operações"),
    (re.compile(_safe_word("proximo"), re.IGNORECASE), "próximo"),
    (re.compile(_safe_word("proximos"), re.IGNORECASE), "próximos"),
    (re.compile(_safe_word("regulatorio"), re.IGNORECASE), "regulatório"),
    (re.compile(_safe_word("regulatorios"), re.IGNORECASE), "regulatórios"),
    (re.compile(_safe_word("requisicao"), re.IGNORECASE), "requisição"),
    (re.compile(_safe_word("requisicoes"), re.IGNORECASE), "requisições"),
    (re.compile(_safe_word("relatorio"), re.IGNORECASE), "relatório"),
    (re.compile(_safe_word("relatorios"), re.IGNORECASE), "relatórios"),
    (re.compile(_safe_word("revisavel"), re.IGNORECASE), "revisável"),
    (re.compile(_safe_word("revisaveis"), re.IGNORECASE), "revisáveis"),
    (re.compile(_safe_word("seguranca"), re.IGNORECASE), "segurança"),
    (re.compile(_safe_word("validacao"), re.IGNORECASE), "validação"),
    (re.compile(_safe_word("validacoes"), re.IGNORECASE), "validações"),
    (re.compile(_safe_word("canonica"), re.IGNORECASE), "canônica"),
    (re.compile(_safe_word("canonicas"), re.IGNORECASE), "canônicas"),
    (re.compile(_safe_word("canonico"), re.IGNORECASE), "canônico"),
    (re.compile(_safe_word("canonicos"), re.IGNORECASE), "canônicos"),
]


CODE_FENCE_RE = re.compile(r"(^```.*?$)", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"(`[^`]*`)")
LINK_TARGET_RE = re.compile(r"(\]\([^\)]*\))")
AUTO_LINK_RE = re.compile(r"(<https?://[^>]+>)")
REF_LINK_DEF_LINE_RE = re.compile(r"^\[[^\]]+\]:\s+\S+")


def _apply_replacements(text: str) -> str:
    updated = text

    def _preserve_case(match: re.Match[str], replacement: str) -> str:
        token = match.group(0)
        if token.isupper():
            return replacement.upper()
        if token[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement

    for pattern, replacement in REPLACEMENTS:
        updated = pattern.sub(lambda m, r=replacement: _preserve_case(m, r), updated)
    return updated


def _normalize_non_code(text: str) -> str:
    out_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if REF_LINK_DEF_LINE_RE.match(line.strip()):
            out_lines.append(line)
            continue

        segments = INLINE_CODE_RE.split(line)
        normalized_segments: list[str] = []
        for idx, seg in enumerate(segments):
            if idx % 2 == 1:
                normalized_segments.append(seg)
                continue

            auto_parts = AUTO_LINK_RE.split(seg)
            normalized_auto: list[str] = []
            for a_idx, a_seg in enumerate(auto_parts):
                if a_idx % 2 == 1:
                    normalized_auto.append(a_seg)
                    continue

                link_parts = LINK_TARGET_RE.split(a_seg)
                for lp_idx, lp in enumerate(link_parts):
                    if lp_idx % 2 == 1:
                        normalized_auto.append(lp)
                    else:
                        normalized_auto.append(_apply_replacements(lp))
            normalized_segments.append("".join(normalized_auto))

        out_lines.append("".join(normalized_segments))

    merged = "".join(out_lines)
    merged = re.sub(r"(?m)^observação\b", "Observação", merged)
    merged = re.sub(r"(?m)^(\#{1,6}\s+)validação\b", r"\1Validação", merged)
    return merged


def normalize_markdown(content: str) -> str:
    parts = CODE_FENCE_RE.split(content)
    out: list[str] = []
    in_fence = False
    for part in parts:
        if part.startswith("```"):
            in_fence = not in_fence
            out.append(part)
            continue
        if in_fence:
            out.append(part)
            continue
        out.append(_normalize_non_code(part))
    return "".join(out)


def _iter_markdown_targets(root: Path, targets: list[str]) -> list[Path]:
    if not targets:
        docs_dir = root / "docs"
        return sorted(docs_dir.rglob("*.md"))

    resolved: list[Path] = []
    for raw in targets:
        p = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
        if p.is_dir():
            resolved.extend(sorted(p.rglob("*.md")))
        elif p.is_file() and p.suffix.lower() == ".md":
            resolved.append(p)
    unique: list[Path] = []
    seen: set[Path] = set()
    for p in resolved:
        if p not in seen:
            unique.append(p)
            seen.add(p)
    return unique


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        help="Arquivos ou diretórios (relativos ao diretório ontrackchain/) para normalizar. Default: docs/**.md",
    )
    args = parser.parse_args()

    changed = 0
    for path in _iter_markdown_targets(root, list(args.paths)):
        original = path.read_text(encoding="utf-8")
        updated = normalize_markdown(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"files_changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
