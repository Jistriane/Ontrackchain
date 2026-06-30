# Matriz Operacional de Execucao para 95%

## Objetivo

Traduzir o plano trimestral e o board estrategico em uma matriz executavel unica, com:

- status operacional padronizado
- owners sugeridos
- owner nominal por frente
- prazo alvo por ciclo
- risco associado
- artefato esperado
- dependencias explicitas
- proxima evidencia esperada
- gate de promocao entre estados

Este documento complementa:

- [Plano Operacional Trimestral para 95%](project-operational-plan-to-95.md)
- [Board de Prioridades do Projeto](project-priority-board.md)
- [Registro de Riscos do Projeto](project-risk-register.md)
- [Runbook de Governanca Semanal](project-weekly-governance-runbook.md)
- [Checklist de Evidencia Minima da Primeira Janela Seria](first-serious-window-evidence-checklist.md)

## Regra de Status

| Status | Significado |
| --- | --- |
| `todo` | item reconhecido, mas ainda sem janela ou preparacao suficiente |
| `ready` | dependencias minimas atendidas, item pode entrar em execucao |
| `in_progress` | execucao ativa com evidencias parciais ou homologacao em curso |
| `blocked` | existe impedimento externo, de credencial, owner ou ambiente |
| `done` | criterio de aceite atingido com evidencia suficiente |

## Gate de Avanco

### `todo -> ready`

- dependencias tecnicas identificadas
- owner sugerido aceito
- criterio de aceite descrito

### `ready -> in_progress`

- janela de execucao definida
- ambiente e segredos minimos disponiveis
- comando, runbook ou trilha operacional identificados

### `in_progress -> done`

- criterio de aceite comprovado por artefato, teste, evidência operacional ou sign-off formal
- risco residual reclassificado
- documentacao canônica atualizada

## Convencao de Ownership e Prazos

- `Owner Sugerido`: disciplina ou squad responsavel pelo fechamento tecnico do item
- `Owner Nominal`: papel operacional que deve responder pelo proximo movimento do item no ciclo atual
- `Prazo Alvo`: horizonte esperado para mover o item ao proximo estado, usando `T1`, `T2` ou `T3` e um corte de semana do ciclo quando aplicavel
- quando o owner real for conhecido, ele deve substituir o papel nominal sem alterar a estrutura da matriz

## Matriz Mestre

| ID | Trimestre | Status Atual | Prioridade | Dominio | Owner Sugerido | Owner Nominal | Prazo Alvo | Risco Associado | Artefato Esperado | Dependencias | Proxima Evidencia Esperada | Gate para `done` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-01` | T1 | `in_progress` | P0 | Auth | Backend/Auth | Tech Lead Auth | `T1-S1` | `R-01` | evidencias de login OIDC serio e output do preflight | IdP, claims, secrets nao-dev | execucao `OIDC` seria sem `localhost` e sem `DEV_AUTH_ENABLED` | login real homologado em ambiente serio com evidencias e preflight verde |
| `P0-02` | T1 | `in_progress` | P0 | Auth | Backend/Auth + Frontend | Security Champion de Auth | `T1-S2` | `R-02` | evidencia de MFA serio e runbook de indisponibilidade | `P0-01` | evidencia de MFA serio ou federado e runbook de indisponibilidade | fluxo sensivel protegido com trilha auditavel e sem fallback silencioso |
| `P0-05` | T1 | `in_progress` | P0 | Compliance | Compliance/Backend | Owner de Integracao AML | `T1-S1` | `R-05`, `R-06` | bundle de homologacao externa AML/KYT em `live` | contrato, credenciais, provider | `provider-readiness` verde e homologacao externa em modo `live` | provider real operando com timeout, retry, degradacao honesta e evidencias anexaveis |
| `P0-06` | T1 | `in_progress` | P0 | Investigation | Backend Core | Owner de Integracao RPC | `T1-S1` | `R-07` | bundle de homologacao RPC com primario e fallback | providers aceitos, segredos, endpoints | `rpc-readiness` verde com `primary_url + fallback_url` | investigacao homologada com fallback funcional e evidencias de janela |
| `RUN-STG-01` | T1 | `ready` | P1 | Release | DevOps/Platform | Release Manager Tecnico | `T1-S2` | `R-13`, `R-16` | dossier de janela `ok` e artifact `serious-staging-window-<janela>` | `P0-01`, `P0-05`, `P0-06` minimamente prontos; `GitHub Environment` com `STAGING_WINDOW_PRIVATE_ENV` | execucao real do workflow `Staging Serious Window` com artifact anexavel | dossier de janela `ok` e artifact do workflow anexados ao sign-off |
| `P1-01` | T2 | `in_progress` | P0 | Governanca | Security/Platform | Security Officer Operacional | `T2-S1` | `R-11` | sign-off formal de retention/recovery | baseline publicada | aprovacao formal de retention/recovery | sign-off formal registrado e politica tratada como controle aceito |
| `P2-02` | T2 | `in_progress` | P1 | Operacao | Platform/SRE | Incident Manager | `T2-S1` | `R-15` | aceite formal de owners, SLA e runbooks | owners e runbooks publicados | aceite formal dos owners, SLA e ritos | ownership operacional aceito e exercitado em incidente/janela |
| `GOV-01` | T2 | `todo` | P1 | Governanca | Security/Compliance | Data Governance Owner | `T2-S2` | `R-11`, `R-12` | matriz minima de classificacao de evidencias | `P1-01` | classificacao minima de evidencias por sensibilidade | classificacao aplicada aos fluxos e artefatos mais criticos |
| `REL-02` | T2 | `todo` | P1 | Release | DevOps/Platform | Release Manager Tecnico | `T2-S2` | `R-13`, `R-16` | segundo dossier comparavel de janela seria | `RUN-STG-01` | segunda janela seria com historico comparavel | pelo menos duas janelas serias consistentes e anexaveis |
| `OBS-01` | T2 | `todo` | P1 | Observabilidade | Platform/SRE | SRE Lead | `T2-S2` | `R-14` | runbook de RCA cross-domain e evidencias de triagem | trilha de incidentes, alertas atuais | RCA cross-domain com correlacao por `request_id` | alerta, triagem e RCA minimamente exercitados |
| `SEC-01` | T3 | `todo` | P0 | Seguranca | Security/Platform | Platform Security Lead | `T3-S1` | `R-11`, `R-16` | ADR ou plano de migracao para vault | auth serio estabilizado, ambientes estaveis | decisao de vault e desenho de migracao de secrets | segredos de producao fora de arquivo local sensivel |
| `OPS-01` | T3 | `todo` | P1 | Operacao | Platform/SRE | Incident Manager | `T3-S1` | `R-15`, `R-14` | war room kit e template de RCA executado | `P2-02` | war room, escalacao e template de RCA | incidente exercitado com evidencias formais |
| `AUD-01` | T3 | `todo` | P1 | Evidencias | Security/Compliance + Backend | Compliance Evidence Owner | `T3-S2` | `R-11`, `R-12` | proposta de selagem, assinatura ou equivalente | `GOV-01` | estrategia de selagem, assinatura ou equivalente | cadeia de custodia reforcada para evidencias mais sensiveis |
| `REL-03` | T3 | `todo` | P1 | Release | DevOps | Release Engineering Lead | `T3-S2` | `R-13` | workflow de promocao superior com menos passos manuais | `REL-02` | automacao maior da promocao para ambiente superior | promocao menos manual e mais previsivel |
| `SEC-02` | T3 | `todo` | P1 | Seguranca | Arquiteto + Backend | Arquiteto de Dominio | `T3-S2` | `R-03` | ADR ou matriz de papeis refinados por dominio | `P0-03`, `P0-01` | proposta de granularizacao regulatoria por dominio | RBAC refinado alem do corte administrativo principal |

## Sequencia Operacional Recomendada

1. fechar primeiro os itens que mudam o estado de `staging` serio de forma crivel
2. na sequencia transformar controles publicados em controles aceitos
3. por fim reduzir dependencia de governanca manual dispersa

## Critérios de Priorizacao

1. seguranca e identidade
2. compliance e integracoes reais
3. governanca de evidencias e retention
4. release readiness e janelas serias
5. observabilidade, RCA e refinamentos institucionais

## Mapa de Bloqueios Atuais

| Item | Tipo de Bloqueio | Impacto |
| --- | --- | --- |
| `P0-01` | credenciais, configuracao seria do IdP | impede corte claro de auth serio |
| `P0-02` | definicao do modelo de MFA serio | impede fechamento honesto de fluxos sensiveis |
| `P0-05` | provider real AML/KYT e contrato | impede compliance serio sem stub |
| `P0-06` | endpoints e homologacao real de RPC | impede resiliencia validada em ambiente serio |
| `P1-01` | aceite formal de Security/Compliance | impede promocao de baseline para controle aceito |
| `P2-02` | aceite operacional formal | impede institucionalizacao de owners e SLA |

## Risco por Item

| Item | Riscos Principais | Leitura |
| --- | --- | --- |
| `P0-01` | `R-01` | autenticacao seria ainda nao homologada fora do local |
| `P0-02` | `R-02` | fluxo sensivel ainda depende da definicao final do MFA serio |
| `P0-05` | `R-05`, `R-06` | compliance core ainda nao pode ser tratado como totalmente real |
| `P0-06` | `R-07` | resiliencia de RPC ainda precisa de homologacao seria |
| `RUN-STG-01` | `R-13`, `R-16` | sem primeira janela real, a governanca ainda e majoritariamente preparatoria |
| `P1-01` | `R-11` | retention existe como baseline, mas ainda nao como controle aceito |
| `P2-02` | `R-15` | ownership existe no papel, mas ainda nao em rito aceito |
| `GOV-01` | `R-11`, `R-12` | classificacao de evidencias segue incompleta |
| `REL-02` | `R-13`, `R-16` | repetibilidade operacional ainda nao foi comprovada |
| `OBS-01` | `R-14` | RCA cross-domain ainda e um gap real |
| `SEC-01` | `R-11`, `R-16` | segredos de producao ainda nao estao institucionalizados |
| `OPS-01` | `R-14`, `R-15` | incidente serio ainda depende de rito informal |
| `AUD-01` | `R-11`, `R-12` | cadeia de custodia ainda nao esta forte o suficiente |
| `REL-03` | `R-13` | promocao superior ainda tem dependencia manual relevante |
| `SEC-02` | `R-03` | granularidade regulatoria de acesso ainda pode evoluir |

## KPIs Operacionais

| KPI | Meta |
| --- | --- |
| Itens T1 com evidencia real | `100%` dos itens criticos T1 com artefato ou homologacao |
| Janelas serias executadas | `>= 2` ate o fim do T2 |
| Itens em `blocked` por mais de 1 ciclo | `0` P0 persistentes |
| Sign-offs formais pendentes do T2 | `0` para retention/recovery e ownership |
| Itens T3 iniciados antes da hora | `0` enquanto T1 seguir aberto criticamente |

## Decisao Recomendada

- usar esta matriz como camada operacional entre o board estrategico e a execucao semanal
- atualizar o `Status Atual` somente com evidencia, nunca por expectativa
- considerar `blocked` sempre que o impedimento depender de credencial, provider, owner externo ou aceite formal
- refletir no [Board de Prioridades do Projeto](project-priority-board.md) apenas as mudancas de leitura estrategica, e nao cada movimento operacional de curto ciclo
- executar a revisao da matriz pelo rito definido no [Runbook de Governanca Semanal](project-weekly-governance-runbook.md)

## Suposicoes

- os owners sugeridos poderao ser refinados sem quebrar a estrutura da matriz
- o board estrategico continua sendo a fonte principal de prioridade
- esta matriz existe para governar execucao e nao para substituir ADR, runbook ou checklist de release
