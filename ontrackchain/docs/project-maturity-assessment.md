# Avaliacao de Maturidade do Projeto

## Objetivo

Consolidar a leitura viva de maturidade tecnica e regulatoria do Ontrackchain, explicando a baseline oficial e os fatores estruturais que sustentam o estado atual do projeto.

Este documento funciona como a narrativa canonica e evolutiva da baseline. Ele deve ser atualizado quando a interpretacao de maturidade mudar de forma material, mesmo que nao exista ainda um novo parecer formal datado de `go/no-go`.

## Escopo Canonico

Use este documento para:

- explicar o por que da baseline oficial `93% / 79% / 89%`
- sustentar a leitura viva de maturidade tecnica e regulatoria do projeto
- orientar discussoes de prioridade, risco residual e proximos degraus de maturidade
- detalhar o racional por dominio por tras da maturidade atual

Nao use este documento como fonte primaria para:

- comunicar status executivo rapidamente para sponsors: use [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)
- calcular o KPI oficial da semana: use [Scorecard Oficial do Projeto](project-kpi-scorecard.md)
- emitir parecer formal datado de `go/no-go`: use [Avaliacao Consolidada de Status do Projeto](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)
- decidir `go/no-go` de uma janela especifica: use [Gates de Release para Staging Serio](project-release-gates.md)
- executar a janela, registrar owners ou conduzir war room: use [Deploy e Staging](deploy-and-staging.md), [GitHub Environment para Staging Serio](github-environment-staging-serious.md), [Matriz de Execucao por Owner para Janela Seria](staging-serious-window-war-room-matrix.md) e [Governanca Semanal](./governance-weekly/README.md)

## Papel na Trilha Documental

Leitura recomendada por nivel:

- leitura curta para diretoria e sponsors: [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)
- baseline viva com racional tecnico e regulatorio: este documento
- parecer formal datado de calibracao e `go/no-go`: [Avaliacao Consolidada de Status do Projeto](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)

## Resumo Executivo

Leituras oficiais recalibradas:

- `93%` de construcao tecnica como plataforma funcional
- `79%` de prontidao para operacao regulada forte
- `89%` de maturidade consolidada conforme [Scorecard Oficial do Projeto](project-kpi-scorecard.md)

Interpretacao:

- o projeto ultrapassou o corte de scaffold avancado e hoje possui core regulatorio funcional em runtime real
- o ganho de maturidade veio principalmente de `evidence_trail`, `preventive_blocks`, `counterparties`, `sanctions cache`, `ROS/COAF` e da cadeia de custodia forte DD/SoF
- a camada `regulatory_work_items` passou a existir como fila compartilhada multiusuario no servidor, ja conectada a `sanctions` e `alerts`
- `P1-01` concluiu a padronizacao canonica de metadata dos `work-items`, reduzindo drift entre frontend, backend e contrato de API
- a trilha `P2-03` agora conecta `alerts`, `/monitoring`, export administrativo e governanca executiva com RCA leve derivada de `work-items`, reduzindo drift entre triagem, resposta e narrativa
- `P2-05` saiu de taxonomia abstrata e passou a enforcement incremental real em `manual-package`, `ROS/COAF`, `billing/balance` e `billing/reconciliation`
- o gap residual mudou de natureza: menos ausencia de codigo, mais homologacao externa, alinhamento final de contratos e sign-off formal

## Regua Utilizada

### 1. Construcao Tecnica do Produto

Mede o quanto o sistema ja esta construido como plataforma:

- servicos e contratos
- fluxos de negocio
- trilha auditavel
- core regulatorio
- testes e operacao

Resultado atual:

- `93%`

### 2. Prontidao Regulatoria

Mede o quanto o projeto esta pronto para contexto forte de operacao regulada:

- IdP e MFA homologados
- providers reais e operacao recorrente
- retention, recovery e cadeia de custodia formal
- aceite institucional dos controles

Resultado atual:

- `79%`

## Matriz de Maturidade

| Dominio | Maturidade | Comentario |
| --- | ---: | --- |
| Arquitetura e Runtime | 94% | stack coerente, migrations reguladas e boundary claro |
| Auth e Identidade | 88% | trilho serio desenhado, homologacao externa ainda pendente |
| Investigation + Billing | 91% | worker real, fallback, trilha financeira operacional, cockpit desacoplado da projeção lateral de `team/users` e superfícies administrativas mais coerentes |
| Compliance Core | 92% | sancoes locais, bloqueios, contrapartes, ROS, fila compartilhada, metadata canônica de `work-items` e gates finos ampliados para `estimate`, `start`, `report`, `counterparties`, `due-diligence` e `source-of-funds` |
| Monitoring Operacional | 93% | backlog global, triagem, export auditado, leitura read-only de RCA em `/monitoring` e alinhamento preventivo estabilizado com `alerts` |
| Reports e Evidencias | 95% | hashes deterministas, `evidence_trail`, ROS auditado e selagem institucional forte DD/SoF ponta a ponta |
| Frontend Operacional | 95% | `/audit`, `/monitoring`, `/alerts`, `/reports`, `/team` e `/cases/[id]` agora mostram recortes preventivos e handoffs mais coerentes, com fila compartilhada e deep-links operacionais relevantes |
| Observabilidade e Alerting | 90% | cobertura boa, bundles e artefatos mais coerentes; `alerts` agora persiste RCA leve, escreve timeline automatica e compartilha contratos visuais e RBAC preventivo com `/monitoring` |
| Testes e CI/CD | 95% | smoke, E2E e preflights bem institucionalizados, com ampliacao da cobertura de custodia e governanca |
| Seguranca e Governanca | 90% | RBAC, quorum e governanca pos-selagem fortaleceram a base; `P2-05` agora endurece papeis reais com gates semanticos, negacao auditada e UX preventiva mais consistente, embora provider institucional definitivo e rotina seria ainda incompletos |

## O Que Aumentou a Maturidade

- `evidence_trail` append-only com encadeamento `SHA-256`
- trilha forte DD/SoF com `package_sha256`, sign-off por papel, `finalize`, `revoke`, `supersede` e preset de governanca no `audit`
- `preventive_blocks` com hash, base regulatoria e fluxo de lift controlado
- `counterparties` com KYC/KYB, PEP, DD e historico
- `sanctions_hits_cache` e `sanctions_lists_meta` como screening local real
- `ROS/COAF` com geracao, aprovacao/rejeicao e submissao manual auditada
- `check_sanctions_sync_status.py` e rito serio de feed de sancoes
- `check_compliance_provider_runtime.py` como gate leve de runtime AML/KYT
- `run_eu_sanctions_window.py` e alvos `make run-eu-sanctions-window*` para a janela UE
- `regulatory_work_items` + `regulatory_work_events` + `regulatory_work_comments` como fila compartilhada multiusuario por modulo/recurso
- `P1-01` consolidado com metadata canonica unificada para `evidence_event`, `operational_alert` e `ros_record`
- integracao dessa fila em todos 7 cockpits regulatorios no frontend via `work-items` sync
- `P2-03` consolidado: playbook canonico de incidente cross-domain, RCA leve persistida no `work-item` do alerta, comentario automatico na timeline, leitura read-only em `/monitoring`, export administrativo enriquecido e resumo opcional para snapshot/comms executivos
- `P2-05` em execucao incremental: `REVIEWER` e `BILLING_ADMIN` ja atuam em superficies reais com negacao auditada e UX coerente
- paineis de historico de workspace consolidados em Sprint 6 com i18n tri-locale (pt-BR/en/es):
  - `counterparties`: DD/SoF manual review status com historico rastreado
  - `sanctions`: painel de triagens por endereco com filtro cliente
  - `evidence`: painel de eventos rastreados com navegacao para timeline
  - `reports`: painel de casos rastreados com busca cross-field
  - `blocks`: painel de avaliacoes historicas de bloqueio
  - `ros-coaf`: painel de registros historicos com status colorido
  - `alerts`: painel de alertas rastreados como work-items com severity

## O Que Ainda Segura o Projeto

### Tecnico-operacional

- `AML/KYT` live ainda depende de credenciais e homologacao real
- `due_diligence` e `source_of_funds` permanecem em `manual_review_required`, embora a cadeia de custodia forte dessa trilha ja esteja materializada
- falta prova recorrente institucional de janelas externas, apesar dos runners e checkers ja estarem prontos
- paineis de historico ja consolidados; proxima fase: integrar actions customizadas mais profundas em incidentes e ownership sem quebrar a baseline leve de RCA

### Regulatorio-operacional

- MFA federado homologado ainda nao foi exercitado como trilho oficial recorrente
- sign-off formal de retention/recovery e owners operacionais ainda esta pendente
- a URL tokenizada real da UE ainda precisa ser ativada na janela seria correspondente
- falta institucionalizar rotina recorrente de janela, RCA e aceite formal; a trilha leve de `P2-03` endurece o rito, mas ainda nao substitui war room exercitado nem artefato recorrente

## Decisao Atual

### Maturidade Tecnica

- o projeto ja pode ser tratado como plataforma tecnicamente pronta para continuar a implementacao incremental sem retorno a fase de scaffold
- a discussao principal sai de "falta construir" e vai para "falta homologar e operar com prova"

### Maturidade Regulatoria

- ainda nao deve ser tratado como pronto para producao regulada
- a leitura honesta continua sendo que o maior gap esta na camada de homologacao, aceite formal e provider real

## Proximos Degraus para 95%

1. homologar `AML/KYT` live com evidencias recorrentes
2. fechar a ativacao real da URL tokenizada da UE
3. homologar o provider institucional definitivo da selagem e o trust bundle versionado
4. obter sign-off formal de retention/recovery e owners
5. executar janelas serias recorrentes com dossier aceito
