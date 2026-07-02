# Board de Prioridades do Projeto

## Objetivo

Consolidar a visao estrategica das iniciativas necessarias para levar o Ontrackchain de um runtime tecnicamente maduro para uma operacao seria mais homologada e regulatoriamente convincente.

## Baseline Atual

- `91%` de construcao tecnica
- `78%` de prontidao regulatoria
- `87%` de construcao total consolidada

Baseline canônica de referencia:

- [Governança Semanal 2026-07-01](governance-weekly/2026-07-01-weekly-governance.md)
- [Atualização de KPI 2026-07-01](governance-weekly/2026-07-01-kpi-scorecard-update.md)

Leitura executiva:

- o core regulatorio principal ja foi implementado
- as prioridades agora sao homologacao externa, coerencia contratual final e institucionalizacao operacional
- o KPI total oficial permanece em `87%` ate nova evidencia material

## Prioridades P0

| ID | Status | Iniciativa | Motivo |
| --- | --- | --- | --- |
| P0-01 | blocked | Homologar `OIDC` e MFA federado em ambiente serio | fecha o maior risco de identidade, mas ainda depende de evidência externa e aceite institucional |
| P0-02 | ready | Homologar provider `AML/KYT` live | fecha o maior gap funcional/regulatorio restante e ja possui gate canônico de runtime |
| P0-03 | ready | Ativar feed UE tokenizado real e validar `EU_CONSOLIDATED` | fecha a janela critica de sancoes europeias e ja possui runner/checker dedicados |
| P0-04 | done | Alinhar catalogo `sanctions_check` com endpoint direto live | contradicao contratual removida e coberta por testes |
| P0-05 | done | Alinhar inventario de eventos da `evidence_trail` | source of truth unico + teste cruzado removeram o drift atual |

## Prioridades P1

| ID | Status | Iniciativa | Motivo |
| --- | --- | --- | --- |
| P1-01 | in_progress | Formalizar sign-off de retention/recovery | transforma baseline em controle aceito |
| P1-02 | in_progress | Executar janela seria recorrente com dossier aceito | sai de validacao pontual para rotina |
| P1-03 | todo | Estruturar artefatos de manual review para DD/SoF | reduz o gap de compliance residual |

## Prioridades P2

| ID | Status | Iniciativa | Motivo |
| --- | --- | --- | --- |
| P2-01 | todo | Refinar UX regulatoria de `/audit` e evidence bundles | melhora operacao e troubleshooting |
| P2-02 | todo | Expandir alertas e RCA cross-domain | melhora visibilidade operacional |

## Itens Ja Consolidados

- `evidence_trail` append-only com `SHA-256`
- `preventive_blocks`
- `counterparties` + `counterparty_history`
- `sanctions_lists_meta` + `sanctions_hits_cache`
- `ROS/COAF` com aprovacao/rejeicao/submissao manual
- `check_sanctions_sync_status.py`
- `check_compliance_provider_runtime.py`
- `run_eu_sanctions_window.py` + targets `make run-eu-sanctions-window*`
- janela seria com `run_staging_window.py`

## Ordenacao Recomendada

1. homologar identidade forte e `AML/KYT live` com gate de runtime verde
2. fechar feed UE tokenizado real com runner dedicado e JSONs anexados
3. institucionalizar sign-off e janela recorrente
4. evoluir artefatos de manual review e UX operacional
5. reforcar retention/recovery e aceite institucional

## Regra de Baseline

- manter `91% / 78% / 87%` como referencia executiva ate existir nova evidencia material publicada na governanca semanal
- nao promover `P0-01`, `P0-02` ou `P0-03` sem artefato real anexavel, checker verde ou aceite institucional correspondente
