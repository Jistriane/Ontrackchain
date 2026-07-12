# Compliance e Controles de Seguranca

## Objetivo

Consolidar os controles tecnicos e operacionais implementados no runtime atual do Ontrackchain e separar claramente o que ja esta operacional do que ainda depende de homologacao, provider real ou aceite formal.

## Controles Implementados

### 1. Isolamento Multi-tenant

- `PostgreSQL RLS` habilitado nas tabelas multi-tenant
- contexto SQL baseado em `app.organization_id`
- policies alinhadas ao padrao do projeto
- objetivo: impedir vazamento cross-tenant mesmo diante de erro de aplicacao

### 2. Auth e Contexto Centralizados

- `Traefik ForwardAuth` como ponto unico de validacao
- `auth-service` suporta `JWT`, `API Key` e `OIDC`
- enriquecimento de contexto com `X-Org-Id`, `X-User-Id`, `X-Linked-User-Id`, `X-Role`, `X-Plan`, `X-Auth-Method`
- `linked_user_id` conecta identidades federadas a usuarios persistidos para mutacoes sensiveis

### 3. MFA em Fluxos Sensiveis

Controles ativos:

- `legal_report` exige auth forte e segundo fator valido
- `ROS/COAF` exige `external_provider` homologado
- `block lift` exige `external_provider` homologado

Observacao operacional:

- o trilho `TOTP` local continua valido apenas para o scaffold `dev`
- o trilho serio depende de MFA federado homologado

### 4. Trilha Operacional e Trilha Regulatoria

- `audit_logs` registra eventos de negocio, leitura privilegiada, negacoes e exportacoes
- `evidence_trail` registra eventos regulatorios append-only com encadeamento `SHA-256`
- hashes deterministas sao usados em relatorios, bloqueios, contrapartes e comprovantes COAF

### 5. Screening de Sancoes e Sync Local

- `compliance-worker` sincroniza feeds para `sanctions_hits_cache`
- screening direto de carteira usa cache local, nao chamada externa por request
- overrides operacionais:
  - `COMPLIANCE_OFAC_SDN_SOURCE_URL`
  - `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- `preflight_external_integrations.py`, `check_sanctions_sync_status.py` e `run_eu_sanctions_window.py` endurecem a governanca do feed

### 6. Enforcement Regulatorio

- `preventive_blocks` registra acao, gatilhos, base regulatoria, score e hash de evidencia
- `counterparties` registra KYC/KYB, PEP, sanctions clearance, DD reforcada e calendario de revisao
- `ros_records` modela geracao, aprovacao/rejeicao e submissao manual de ROS/COAF

### 7. Custodia Formal de Pacotes Manuais DD/SoF

- o cockpit `evidence` ja gera pacote canonico com manifesto deterministico `manual_review_package/v2`
- a exportacao oficial ja produz `package_sha256`, checksums derivados e evento `evidence_manual_review_package_exported`
- o `audit` ja trata `package_sha256` como hash principal do contexto manual e preserva navegacao bidirecional para a origem DD/SoF
- a selagem institucional forte ja esta implementada com `signoff-request`, sign-offs por papel, `finalize`, `revoke`, `supersede`, lookup canonico por digest e preset de governanca no `audit`
- o contrato publico canônico dessa trilha agora vive em `./api-contracts.md`, enquanto `./evidence-manual-package-strong-sealing-architecture.md` permanece como visao arquitetural

## Matriz de Controles

| Area | Controle Atual | Estado | Observacao |
| --- | --- | --- | --- |
| Tenant isolation | `RLS` + contexto SQL | forte | aderente ao padrao `app.organization_id` |
| Auth | `ForwardAuth` + `JWT / API Key / OIDC` | forte | homologacao seria ainda pendente |
| MFA sensivel | `legal_report`, `ROS/COAF`, `block lift` | medio/forte | trilho serio exige homologacao externa |
| Auditoria | `audit_logs` + `request_id` | forte | boa cobertura operacional |
| Evidencia regulatoria | `evidence_trail` + `SHA-256` | forte | source of truth unico e teste cruzado reduzem drift atual |
| Screening de sancoes | cache local + worker | forte | catalogo e endpoint direto convergem para `live` via cache local |
| AML/KYT live | provider-aware + runtime gate | parcial | falta homologacao com credenciais reais e evidencia recorrente |
| DD/SoF | `manual_review_required` | parcial | comportamento intencional do produto atual |
| Custodia formal DD/SoF | manifesto canônico + `package_sha256` + export auditado + selagem institucional forte | medio/forte | baseline funcional entregue com quorum `Compliance + Ops`, revogacao/supersedencia e verificacao local; pendente endurecimento com provider institucional homologado |
| ROS/COAF | workflow completo | forte | submissao final segue manual e auditada |
| Operacao seria | preflight + dossier + ownership | forte | faltam sign-offs formais recorrentes |

## Controles Validados Automaticamente

### Smoke Runtime

- `quote -> start`
- `plan lock`
- `report_generated` e `report_downloaded`
- enforcement de `legal_report`
- metadados de provider RPC no resultado final
- correlacao por `request_id`

### Playwright

- fluxos `critical-path` e `compliance-flows`
- trilho `OIDC` critico
- `legal_report` antes/depois de `2FA`
- backlog administrativo e export auditado

### Preflights e Checks Operacionais

- `preflight_oidc_serious_env.py`
- `preflight_external_integrations.py`
- `check_staging_env_placeholders.py`
- `check_staging_env_handoff.py`
- `check_compliance_provider_runtime.py`
- `run_eu_sanctions_window.py`
- `check_sanctions_sync_status.py`

## Gaps Residuais Reais

### 1. Provider `AML/KYT` em modo live

- o roteador e honesto e observavel
- o gate `check-compliance-provider-runtime` ja existe
- faltam credenciais reais, homologacao externa e evidencias recorrentes

### 2. MFA federado homologado

- o contrato serio esta implementado
- falta homologacao operacional fora do runtime local

### 4. `due_diligence` e `source_of_funds`

- continuam em `manual_review_required`
- isso deve ser tratado como gap de produto/compliance, nao como erro de documentacao

### 5. Cadeia formal de custodia

- hashes, manifestos e dossier existem
- o pacote manual DD/SoF agora possui manifesto canônico, `package_sha256` e evento auditável oficial
- o baseline funcional agora inclui sign-off formal por papel, selagem local em `JWS JSON Flattened`, revogacao, supersedencia e leitura canônica por `package_sha256`
- os gaps residuais reais passaram a ser:
  - homologacao do provider institucional definitivo (KMS/HSM)
  - trust bundle institucional versionado
  - classificacao formal de sensibilidade/aceite operacional recorrente
  - eventual evolucao para TSA/ancora externa
- a visao arquitetural de medio prazo permanece descrita em `./evidence-manual-package-strong-sealing-architecture.md`, com contrato HTTP canônico em `./api-contracts.md`

## Recomendacoes Imediatas

- homologar `AML/KYT` live com `check-compliance-provider-runtime` verde e evidencias da janela seria
- rodar a janela UE com `run-eu-sanctions-window-local` quando `EU_CONSOLIDATED` estiver no escopo
- registrar formalmente sign-off de retention/recovery e owners operacionais
- manter `manual_review_required` explicitamente documentado ate existir motor homologado para DD/SoF
- endurecer a trilha de selagem DD/SoF ja entregue, homologando o provider institucional definitivo e formalizando o trust bundle versionado
