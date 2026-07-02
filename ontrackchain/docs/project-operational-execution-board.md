# Matriz Operacional de Execucao para 95%

## Objetivo

Traduzir o plano trimestral e o board estrategico em uma matriz executavel unica, com:

- status operacional padronizado
- owner sugerido e owner nominal
- prazo alvo
- risco associado
- artefato esperado
- proxima evidencia esperada

## Baseline Atual

- `91%` de construcao tecnica
- `78%` de prontidao regulatoria
- `87%` de construcao total consolidada

Baseline canônica de referencia:

- [Governança Semanal 2026-07-01](governance-weekly/2026-07-01-weekly-governance.md)
- [Atualização de KPI 2026-07-01](governance-weekly/2026-07-01-kpi-scorecard-update.md)

## Regra de Status

| Status | Significado |
| --- | --- |
| `todo` | item reconhecido, ainda sem janela ou preparacao suficiente |
| `ready` | dependencias minimas atendidas |
| `in_progress` | execucao ativa com evidencia parcial |
| `blocked` | existe impedimento externo ou institucional |
| `done` | criterio de aceite atingido com evidencia |

## Matriz Mestre

| ID | Trimestre | Status Atual | Dominio | Owner Sugerido | Prazo Alvo | Risco | Artefato Esperado | Proxima Evidencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-01` | T1 | `blocked` | Auth | Backend/Auth | `T1-S1` | `R-01` | evidencias de OIDC serio + MFA federado | janela com auth serio homologado + aceite institucional |
| `P0-02` | T1 | `ready` | Compliance | Compliance/Backend | `T1-S1` | `R-02` | bundle de homologacao `AML/KYT live` + gate de runtime verde | `make check-compliance-provider-runtime` + homologacao externa anexada |
| `P0-03` | T1 | `ready` | Sancoes | Compliance/Backend | `T1-S1` | `R-03` | runner da janela UE verde com feed real | `<janela>-eu-sanctions-preflight.json` + `<janela>-eu-sanctions-sync.json` |
| `P0-04` | T1 | `done` | Produto/Contrato | Backend | `T1-S2` | `R-04` | docs + catalogo alinhados | testes e `operations` refletindo endpoint live |
| `P0-05` | T1 | `done` | Evidencias | Backend/Arquitetura | `T1-S2` | `R-06` | inventario de eventos alinhado | source of truth unico + `test_evidence_event_catalog_sync.py` verde |
| `RUN-STG-01` | T1 | `ready` | Release | DevOps/Platform | `T1-S2` | `R-08` | dossier de janela `ok` | artifact oficial + JSONs de checks anexados |
| `P1-01` | T2 | `in_progress` | Governanca | Security/Platform | `T2-S1` | `R-07` | sign-off formal retention/recovery | aceite registrado |
| `P1-02` | T2 | `in_progress` | Operacao | Platform/SRE | `T2-S1` | `R-08` | aceite formal de owners/SLA/runbooks | sign-off operacional |
| `P1-03` | T2 | `todo` | Compliance | Compliance/Product | `T2-S2` | `R-05` | artefatos de manual review DD/SoF | trilha minima de manual review |
| `REL-02` | T2 | `todo` | Release | DevOps/Platform | `T2-S2` | `R-08` | segunda janela seria comparavel | historico de dossiers |
| `SEC-01` | T3 | `todo` | Seguranca | Security/Platform | `T3-S1` | `R-07` | plano de vault e segredos de producao | ADR/roteiro aprovado |
| `OPS-01` | T3 | `todo` | Operacao | Platform/SRE | `T3-S1` | `R-08` | war room kit e RCA executado | evidencia de simulacao/incidente |
| `AUD-01` | T3 | `todo` | Evidencias | Security/Compliance | `T3-S2` | `R-06` | proposta de selagem/assinatura | estrategia aprovada |

## Gate de Avanco

### `todo -> ready`

- dependencias identificadas
- owner aceito
- artefato esperado definido

### `ready -> in_progress`

- janela, credencial ou ambiente disponivel
- comando e rito de execucao definidos

### `in_progress -> done`

- criterio de aceite comprovado por artefato, teste, evidência operacional ou sign-off
- risco residual reclassificado
- documentacao canonica atualizada

## Decisao Recomendada

- atualizar esta matriz somente com base em evidencia real
- usar `blocked` sempre que a pendencia depender de credencial, owner externo ou aceite formal
- nao marcar itens do T2/T3 como resolvidos enquanto T1 regulatorio permanecer aberto
- usar `91% / 78% / 87%` como baseline executiva ate nova evidencia material publicada na governanca semanal
