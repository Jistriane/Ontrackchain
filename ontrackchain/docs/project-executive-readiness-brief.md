# Resumo Executivo de Readiness

## Objetivo

Oferecer uma leitura curta, executiva e canonica do estado atual do Ontrackchain para diretoria, sponsors e stakeholders que precisam entender rapidamente:

- o quanto ja foi construido
- o que ainda impede `95%`
- qual ordem de fechamento move mais maturidade real

Este documento nao substitui o detalhamento tecnico de:

- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md)
- [Avaliacao de Status](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)

## Papel na Trilha Documental

Use este documento como porta de entrada quando a pergunta for "qual e o estado atual e o que falta fechar?".

Leitura recomendada por nivel:

- leitura curta para diretoria, sponsors e stakeholders: este documento
- baseline viva com racional tecnico e regulatorio: [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md)
- parecer formal datado de calibracao e `go/no-go`: [Avaliacao de Status](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)

## Snapshot Atual

Leitura executiva oficial:

- `92%` de construcao tecnica
- `79%` de prontidao regulatoria/operacional
- `88%` de maturidade consolidada

Interpretacao honesta:

- o Ontrackchain ja esta majoritariamente construido como plataforma
- o gap principal deixou de ser ausencia de codigo
- o gargalo atual esta em homologacao externa, prova operacional e aceite institucional

## Regra de Taxonomia

- `P0` representa o caminho mais curto e auditavel para cruzar `90%+`
- `P1` representa a institucionalizacao minima que sustenta esse salto sem regressao operacional
- `P2` representa o trabalho pos-90, focado em sustentacao, reducao de debito e preparacao para `95%`

## O Que Ja Esta Forte

- arquitetura modular com boundaries claros, gateway unico, RLS e servicos por dominio
- frontend operacional real com cockpits dedicados, i18n tri-locale, labels institucionais e contratos compartilhados
- camada regulatoria funcional com `evidence_trail`, `preventive_blocks`, `counterparties`, `ROS/COAF` e screening local de sancoes
- operacao multiusuario sustentada por `regulatory_work_items`, timeline e comentarios estruturados
- trilha de incidente cross-domain agora conecta `alerts`, `monitoring`, export administrativo e governanca executiva com RCA leve reaproveitando `work-items`, sem abrir servico novo
- observabilidade, runbooks, bundles de readiness e harnesses de validacao institucionalizados

## Sinal Novo de Sustentacao Operacional

- `P1-01` concluiu a padronizacao de metadata dos `work-items`, reduzindo drift entre cockpit, backend e contrato de API
- `P2-03` saiu de desenho abstrato para trilha canônica leve: playbook indexado, RCA persistida no `work-item` do alerta, leitura read-only em `/monitoring`, export administrativo enriquecido e resumo opcional para snapshot/comms executivos
- `P2-05` entrou em trilho real de enforcement fino: `REVIEWER` e `BILLING_ADMIN` ja operam em superficies concretas, incluindo `manual-package`, `ROS/COAF`, `billing/balance`, `billing/reconciliation` e a degradação coerente de CTAs e do acesso direto ao dashboard financeiro no frontend
- a segregacao regulatoria de `ROS/COAF` agora tambem aparece de forma explicita na UX: `REVIEWER` segue aprovando/rejeitando, mas nao recebe a superficie de submissao manual reservada a `COMPLIANCE_OFFICER`
- isso reduz ambiguidade entre triagem tecnica e narrativa executiva, porque a causa raiz deixa de ficar implícita ou dispersa entre UI, comentário e export
- este avanço melhora qualidade operacional e auditabilidade, mas ainda nao altera a baseline oficial `92/79/88` por si só
- o ganho executivo formal so deve ocorrer quando houver uso recorrente em janela real, com resumo RCA materializado e revisão humana coerente com o rito semanal

## O Que Ainda Impede `95%`

Bloqueadores principais:

1. `P0-01` homologar `OIDC + MFA` federado em trilho serio e recorrente
2. `P0-02` fechar `AML/KYT` live com credencial real e evidencia anexavel
3. `P0-03` ativar feed UE real com URL tokenizada e persistencia auditavel
4. `P0-04` consolidar `P0-02 + P0-03` em bundle regulatorio revisavel; tentativas parciais ajudam a endurecer correlacao e dossier, mas nao fecham o item
5. `P0-05` executar a primeira janela seria material com `go/no-go` formal
6. `P0-06` formalizar o sign-off minimo de retention/recovery
7. `P1-02` institucionalizar owners, SLA e rito recorrente da janela

## Ordem Recomendada

Sequencia executiva de melhor retorno:

1. fechar `P0-02`
2. fechar `P0-03`
3. consolidar `P0-04` apenas depois da prova combinada de `P0-02` e `P0-03`
4. homologar `P0-01`
5. executar `P0-05`
6. formalizar `P0-06`
7. publicar `P0-07`

## Regra de Governanca

Nenhuma promocao de maturidade deve ocorrer por:

- intencao
- configuracao pronta
- evidencia parcial
- sucesso nao reproduzivel

Promocao de status so e permitida quando houver:

- execucao real em ambiente valido
- evidencia preservada em artefato rastreavel
- coerencia entre runtime, contrato e narrativa executiva
- revisao humana
- aprovacao explicita do accountable

Leitura executiva adicional:

- tentativa parcial de `P0-02` ou `P0-03` conta como progresso operacional e reduz risco de execucao
- a promocao oficial para `90%+` continua exigindo prova combinada e revisavel, preferencialmente selada por `P0-04`
- sinais de RCA cross-domain (`rca_attached_count`, `critical_open_count`, dominios afetados) ajudam a qualificar risco operacional e handoff executivo, mas nao substituem evidência de janela seria nem mudam KPI sozinhos

Decisao formal relacionada:

- [ADR-010 — Promocao de Maturidade Baseada em Evidencia](./adrs/ADR-010-promocao-de-maturidade-baseada-em-evidencia.md)
- [Kit de Execucao por Evidencia](./project-maturity-evidence-execution-kit.md)

## Resultado Esperado

Se `P0-02`, `P0-03`, `P0-04`, `P0-01` e `P0-05` forem fechados com evidencia real, o projeto entra na faixa plausivel de `93%+` consolidado e abre a reta final legitima para `95%`. Antes disso, tentativas parciais servem para endurecer a trilha executiva, nao para antecipar o fechamento oficial.

## Quando Usar Este Documento

Use este resumo quando a necessidade for:

- comunicar status executivo rapidamente
- alinhar patrocinadores e owners sobre o foco imediato
- evitar confusao entre "falta codigo" e "falta readiness comprovado"
