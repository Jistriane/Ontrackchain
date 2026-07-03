# Avaliacao de Maturidade do Projeto

## Objetivo

Consolidar uma leitura executiva e tecnica do estado atual do Ontrackchain apos Sprint 6 com todos 7 paineis de historico de workspace consolidados nos cockpits regulatorios (counterparties DD/SoF, sanctions, evidence, reports, blocks, ros-coaf, alerts).

## Escopo Canonico

Use este documento para:

- comunicar a leitura executiva da maturidade tecnica e regulatoria do projeto
- explicar o por que da baseline oficial `91% / 78% / 87%`
- orientar discussoes de prioridade, risco residual e proximos degraus de maturidade

Nao use este documento como fonte primaria para:

- calcular o KPI oficial da semana: use [Scorecard Oficial do Projeto](project-kpi-scorecard.md)
- decidir `go/no-go` de uma janela especifica: use [Gates de Release para Staging Serio](project-release-gates.md)
- executar a janela, preencher owners ou conduzir war room: use os runbooks e checklists operacionais da trilha de staging serio

## Resumo Executivo

Leituras oficiais recalibradas:

- `91%` de construcao tecnica como plataforma funcional
- `78%` de prontidao para operacao regulada forte

Formula canonica complementar:

- `87%` de construcao total consolidada conforme [Scorecard Oficial do Projeto](project-kpi-scorecard.md)

Interpretacao:

- o projeto ultrapassou o corte de scaffold avancado e hoje possui core regulatorio funcional em runtime real
- o ganho de maturidade veio principalmente de `evidence_trail`, `preventive_blocks`, `counterparties`, `sanctions cache` e `ROS/COAF`
- a camada `regulatory_work_items` passou a existir como fila compartilhada multiusuario no servidor, ja conectada a `sanctions` e `alerts`
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

- `91%`

### 2. Prontidao Regulatoria

Mede o quanto o projeto esta pronto para contexto forte de operacao regulada:

- IdP e MFA homologados
- providers reais e operacao recorrente
- retention, recovery e cadeia de custodia formal
- aceite institucional dos controles

Resultado atual:

- `78%`

## Matriz de Maturidade

| Dominio | Maturidade | Comentario |
| --- | ---: | --- |
| Arquitetura e Runtime | 94% | stack coerente, migrations reguladas e boundary claro |
| Auth e Identidade | 88% | trilho serio desenhado, homologacao externa ainda pendente |
| Investigation + Billing | 90% | worker real, fallback e trilha financeira operacional |
| Compliance Core | 90% | sancoes locais, bloqueios, contrapartes, ROS e fila compartilhada inicial via `work-items` ja implementados |
| Monitoring Operacional | 91% | backlog global, triagem e export auditado |
| Reports e Evidencias | 92% | hashes deterministas, evidence trail e ROS auditado |
| Frontend Operacional | 93% | `/audit` e `/monitoring` maduros; todos 7 cockpits (`sanctions`, `alerts`, `counterparties`, `evidence`, `reports`, `blocks`, `ros-coaf`) agora sincronizam fila compartilhada via `work-items` e possuem paineis de historico consolidados com i18n tri-locale |
| Observabilidade e Alerting | 88% | cobertura boa, ainda faltam sinais de seguranca mais fortes |
| Testes e CI/CD | 94% | smoke, E2E e preflights bem institucionalizados |
| Seguranca e Governanca | 85% | controles tecnicos fortes; sign-off formal e rotina seria ainda incompletos |

## O Que Aumentou a Maturidade

- `evidence_trail` append-only com encadeamento `SHA-256`
- `preventive_blocks` com hash, base regulatoria e fluxo de lift controlado
- `counterparties` com KYC/KYB, PEP, DD e historico
- `sanctions_hits_cache` e `sanctions_lists_meta` como screening local real
- `ROS/COAF` com geracao, aprovacao/rejeicao e submissao manual auditada
- `check_sanctions_sync_status.py` e rito serio de feed de sancoes
- `check_compliance_provider_runtime.py` como gate leve de runtime AML/KYT
- `run_eu_sanctions_window.py` e alvos `make run-eu-sanctions-window*` para a janela UE
- `regulatory_work_items` + `regulatory_work_events` + `regulatory_work_comments` como fila compartilhada multiusuario por modulo/recurso
- integracao dessa fila em todos 7 cockpits regulatorios no frontend via `work-items` sync
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
- `due_diligence` e `source_of_funds` permanecem em `manual_review_required`
- falta prova recorrente institucional de janelas externas, apesar dos runners e checkers ja estarem prontos
- paineis de historico ja consolidados; proxima fase: integracao mais profunda de actions customizadas (escalacao, reassignment de owner)

### Regulatorio-operacional

- MFA federado homologado ainda nao foi exercitado como trilho oficial recorrente
- sign-off formal de retention/recovery e owners operacionais ainda esta pendente
- a URL tokenizada real da UE ainda precisa ser ativada na janela seria correspondente
- falta institucionalizar rotina recorrente de janela, RCA e aceite formal

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
3. obter sign-off formal de retention/recovery e owners
4. executar janelas serias recorrentes com dossier aceito
5. adicionar actions customizadas aos paineis de historico (escalacao, reassignment, comentarios inline)
