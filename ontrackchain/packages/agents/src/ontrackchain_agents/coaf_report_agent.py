from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class CoafReportDraft:
    title: str
    body_text: str
    generated_at: str
    file_hash_sha256: str
    content_type: str = "application/pdf"


class CoafReportAgent:
    """
    Geração determinística de rascunho de ROS/COAF.

    Mantém a estrutura previsível para auditoria e permite evoluir
    depois para HTML/Jinja2 + renderização PDF real sem alterar contrato.
    """

    AGENT_ID = "CoafReportAgent"

    def generate(
        self,
        *,
        ros_id: str,
        case_id: str | None,
        trigger_reason: str,
        tipologia_code: str,
        suspected_amount_brl: float | None,
        suspected_address: str | None,
        suspected_chain: str | None,
    ) -> CoafReportDraft:
        generated_at = datetime.now(timezone.utc).isoformat()
        lines = [
            "ONTRACKCHAIN - RELATORIO DE OPERACAO SUSPEITA (ROS/COAF)",
            f"ROS ID: {ros_id}",
            f"Case ID: {case_id or 'N/A'}",
            f"Tipologia: {tipologia_code}",
            f"Motivo: {trigger_reason}",
            f"Valor suspeito BRL: {suspected_amount_brl if suspected_amount_brl is not None else 'N/A'}",
            f"Endereco suspeito: {suspected_address or 'N/A'}",
            f"Chain: {suspected_chain or 'N/A'}",
            f"Gerado em: {generated_at}",
            "",
            "Observacao:",
            "Este documento e um rascunho interno para validacao do Compliance Officer",
            "antes da submissao manual ao portal COAF ONLINE.",
        ]
        body_text = "\n".join(lines)
        file_hash = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
        return CoafReportDraft(
            title="ROS/COAF",
            body_text=body_text,
            generated_at=generated_at,
            file_hash_sha256=file_hash,
        )
