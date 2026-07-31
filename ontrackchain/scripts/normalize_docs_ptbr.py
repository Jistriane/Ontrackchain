from __future__ import annotations

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
    for pattern, replacement in REPLACEMENTS:
        updated = pattern.sub(replacement, updated)
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
    return "".join(out_lines)


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


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    docs_dir = root / "docs"
    changed = 0
    for path in sorted(docs_dir.rglob("*.md")):
        original = path.read_text(encoding="utf-8")
        updated = normalize_markdown(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"files_changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
