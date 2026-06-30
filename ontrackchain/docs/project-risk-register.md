# Registro de Riscos do Projeto

## Objetivo

Consolidar os principais riscos tecnicos, operacionais e regulatorios do Ontrackchain em um registro vivo, com:

- probabilidade
- impacto
- severidade
- mitigacao
- owner sugerido
- gatilho de acompanhamento

Este documento complementa:

- [Avaliacao de Maturidade do Projeto](project-maturity-assessment.md)
- [Plano de Execucao para 90%](project-execution-plan-to-90.md)
- [Board de Prioridades do Projeto](project-priority-board.md)
- [Gates de Release para Staging Serio](project-release-gates.md)
- [Readiness Regulatorio](regulatory-readiness.md)
- [Plano Operacional Trimestral para 95%](project-operational-plan-to-95.md)

## Resumo Executivo

Leituras oficiais recomendadas:

- `89%` de construcao tecnica
- `76%` de prontidao regulatoria

Interpretacao:

- o risco estrutural do projeto caiu em `CI/CD`, restore, evidencias e governanca basica
- os riscos dominantes restantes estao concentrados em homologacao seria de identidade, providers reais e aceite formal de controles publicados
- parte dos riscos abaixo ja saiu do estado "ausente" para "mitigado parcialmente", mas ainda nao pode ser tratada como controlada

## Escala Utilizada

### Probabilidade

- `Alta`
- `Media`
- `Baixa`

### Impacto

- `P0` — risco critico para seguranca, dados, compliance ou operacao do core
- `P1` — risco alto com degradacao significativa, mas recuperavel
- `P2` — risco moderado com impacto controlavel

### Severidade

Calculo qualitativo:

- `Critica`
- `Alta`
- `Media`
- `Baixa`

## Registro Atual

| ID | Risco | Categoria | Status Atual | Probabilidade | Impacto | Severidade | Owner Sugerido | Mitigacao | Gatilho de Revisao |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-01 | Dependencia excessiva do modo `AUTH_MODE=dev` em fluxo serio | Auth | mitigado parcialmente | Media | P0 | Critica | Backend/Auth | homologar IdP real, manter `DEV_AUTH_ENABLED=false` fora de `local|test` e executar janela seria com evidencias | qualquer promocao para staging |
| R-02 | MFA/2FA ainda nao homologado de forma seria em fluxo sensivel | Seguranca | mitigado parcialmente | Alta | P0 | Critica | Backend/Auth + Frontend | federar MFA pelo IdP ou operacionalizar segundo fator serio, proibir fallback silencioso e publicar runbook de indisponibilidade do IdP/MFA | qualquer fluxo com `legal_report` ou incidente de identidade |
| R-03 | RBAC ainda amplo demais fora do corte administrativo principal | Seguranca | mitigado parcialmente | Media | P0 | Alta | Arquiteto + Backend | expandir granularidade por dominio e homologar enforcement em ambiente serio | exposicao de endpoint sensivel novo |
| R-04 | Negacoes sensiveis nao gerarem trilha auditavel suficiente fora do core fechado | Auditoria | mitigado parcialmente | Media | P0 | Alta | Backend | ampliar cobertura de `authorization_denied` e validar dominios ainda sem trilha completa | tentativa negativa relevante sem log |
| R-05 | Compliance core ainda depender de stub em ambiente-alvo | Compliance | aberto | Alta | P0 | Critica | Compliance/Backend | remover stubs criticos remanescentes e integrar provider real | promocao para staging regulado |
| R-06 | Provider AML/KYT externo introduzir indisponibilidade ou resposta inconsistente | Integracao | mitigado parcialmente | Media | P1 | Alta | Compliance/Backend | timeout, retry, fallback, preflight, homologacao externa e telemetria por provider | falha repetida do provider |
| R-07 | RPC primario indisponivel quebrar investigation ou observacao | Integracao | mitigado parcialmente | Media | P1 | Alta | Backend Core | operar com primario + fallback, medir degradacao e homologar janela seria | aumento de timeout ou erro RPC |
| R-08 | Inconsistencia em reserva/fechamento de credito afetar billing | Billing | mitigado parcialmente | Media | P0 | Alta | Backend Core | reforcar smoke, trilha de ledger, idempotencia e testes de regressao | divergencia em `credit_ledger` |
| R-09 | Worker assíncrono degradar sem deteccao rapida | Operacao | mitigado parcialmente | Media | P1 | Alta | Platform/SRE + Backend Core | ampliar alertas, DLQ observavel, correlacao cross-domain e runbook de reprocessamento | aumento de backlog ou DLQ |
| R-10 | Falha em backup/restore inviabilizar recuperacao | Dados | mitigado parcialmente | Baixa | P0 | Alta | Platform/DBA | repetir restore periodicamente, anexar manifestos e transformar baseline em rito operacional | qualquer promocao apos mudanca de schema critica |
| R-11 | Retention insuficiente comprometer cadeia de custodia | Governanca | mitigado parcialmente | Media | P0 | Alta | Security/Platform | obter sign-off formal de retention minima, classificar evidencias e institucionalizar descarte/hold | nova exigencia regulatoria ou export sensivel |
| R-12 | Exportacao de evidencias sem controle fino ampliar superficie de vazamento | Auditoria | mitigado parcialmente | Media | P0 | Alta | Backend + Frontend | manter exportacao autorizada, filtrada, auditada e evoluir classificacao de sensibilidade | ampliacao de escopo do `/audit` |
| R-13 | Pipeline atual nao bloquear regressao de qualidade suficiente em ambiente serio | CI/CD | mitigado parcialmente | Baixa | P1 | Media | DevOps | consolidar tempos/caches, manter `quality-gates` e exercitar promocao seria com dossier e evidencias | regressao detectada apenas apos deploy |
| R-14 | Observabilidade insuficiente mascarar incidente cross-domain | Observabilidade | aberto | Media | P1 | Media | Platform/SRE | enriquecer correlacao por `request_id`, alertas de seguranca e dashboards com foco em RCA | incidente sem causa raiz clara |
| R-15 | Ausencia de aceite formal de runbooks e owners atrasar resposta operacional | Operacao | mitigado parcialmente | Media | P1 | Media | Platform/SRE | obter aceite formal de owners/SLA/runbooks e exercitar war room/escala | incidente com handoff confuso |
| R-16 | Documentacao refletir um estado mais maduro do que o runtime real | Governanca | mitigado parcialmente | Baixa | P1 | Baixa | Arquitetura/Engenharia | revalidar docs a cada corte importante com smoke, evidencias e revisao dos percentuais oficiais | discrepancia entre README/docs e comportamento real |

## Top Riscos Atuais

### 1. Auth forte ainda incompleto

Motivo:

- afeta diretamente identidade, segregacao de acesso e credibilidade de staging serio

Riscos associados:

- `R-01`
- `R-02`
- `R-03`

### 2. Compliance core ainda parcial

Motivo:

- compromete a leitura de prontidao regulatoria e reduz aderencia do produto ao alvo declarado

Riscos associados:

- `R-05`
- `R-06`
- `R-12`

### 3. Sign-off e cadeia de custodia

Motivo:

- sem sign-off formal, janela seria executada e cadeia de custodia forte, o ambiente pode parecer pronto sem governanca suficiente

Riscos associados:

- `R-10`
- `R-11`
- `R-15`

## Mitigacoes Prioritarias

| Faixa | Itens | Resultado Esperado |
| --- | --- | --- |
| Imediata | `R-01`, `R-02`, `R-05`, `R-06` | atravessar os maiores bloqueios de identidade e compliance real |
| Curto prazo | `R-07`, `R-08`, `R-09`, `R-14` | estabilizar resiliencia operacional e RCA cross-domain |
| Medio prazo | `R-10`, `R-11`, `R-12`, `R-13`, `R-15`, `R-16` | consolidar governanca, cadeia de custodia e promocao seria |

## Criterios para Encerrar um Risco

Um risco so deve ser marcado como reduzido ou controlado quando houver:

- implementacao da mitigacao principal
- evidencia objetiva de validacao
- owner aceitando formalmente o status
- atualizacao do impacto residual

## Rito Recomendado

### Revisao Semanal

- revisar `Top Riscos`
- atualizar severidade
- mover riscos entre `aberto`, `mitigando`, `controlado`

### Revisao por Sprint

- reavaliar riscos introduzidos por novas features
- validar se algum risco deixou de ser hipotese e virou incidente

### Gate de Promocao

- nenhum risco `Critica` sem mitigacao aceitavel deve passar para staging serio

## Suposicoes

- o projeto mantera viés regulatorio e necessidade de trilha auditavel forte
- o registro de riscos sera tratado como artefato vivo, nao como documento estatico
- owners sugeridos podem ser adaptados conforme a estrutura real do time
