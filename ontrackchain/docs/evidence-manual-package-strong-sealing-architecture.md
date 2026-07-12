# Arquitetura de Selagem Institucional Forte do Pacote Manual DD/SoF

## Objetivo

Registrar a arquitetura vigente e a linha de endurecimento residual da trilha de selagem institucional forte do pacote manual DD/SoF, evoluindo a base de:

- manifesto canônico + hash SHA-256
- export auditado em `audit_logs`
- navegacao bidirecional `evidence <-> audit`

para um artefato institucionalmente selado, verificavel e apto a:

- sign-off formal recorrente
- verificacao criptografica offline
- correlacao com `audit_logs`, `evidence_trail` e governanca semanal
- futura extensao para dossies regulatórios oficiais

## Fase Atual

- `Fase 5 - baseline implementada e endurecimento institucional residual`

## Contexto Rapido

O pacote manual DD/SoF ja possui:

- documento canonico JSON
- manifesto deterministico `manual_review_package/v2`
- `package_sha256`, `scope_sha256`, `manual_review_sha256`, `dossier_sha256`
- evento oficial `evidence_manual_review_package_exported`
- preset auditavel e retorno contextual entre `evidence` e `audit`

O gap residual mudou de "cadeia inexistente" para "baseline funcional entregue, mas ainda sem provider institucional definitivo homologado e trust bundle corporativo versionado".

## Descobertas

### Requisitos funcionais explicitos

- anexar uma prova institucional ao pacote manual DD/SoF
- manter correlacao por `request_id`, `report_id`, `scope_id` e `manual_review_action`
- preservar o manifesto canonico ja validado
- registrar eventos auditaveis de sign-off e selagem
- permitir verificacao posterior sem depender do frontend

### Requisitos funcionais implicitos

- nao quebrar o contrato atual de export manual
- reaproveitar `package_sha256` como digest principal da selagem
- suportar pelo menos `due_diligence` e `source_of_funds`
- permitir revogacao/substituicao controlada de uma selagem
- vincular a selagem a papel institucional, nao so a usuario final

### Requisitos nao funcionais

- seguranca: assinatura com chave institucional nao exportavel
- auditabilidade: trilha completa de request, sign-off, selagem, revogacao e verificacao
- disponibilidade: falha da selagem nao pode corromper o pacote exportado
- manutenibilidade: formato de envelope versionado e extensivel
- portabilidade: verificacao offline com manifesto + envelope + cadeia de certificados

### Restricoes tecnicas

- o pacote atual e JSON canônico com manifesto `manual_review_package/v2`
- a arquitetura atual separa frontend/App Router e backend `investigation-api`
- o projeto ainda nao tem provider institucional de assinatura homologado
- custos e irreversibilidade de ancoragem on-chain exigem prudencia
- a trilha deve respeitar o baseline atual de `audit_logs` como source of truth operacional

### Criterios de sucesso mensuraveis

- `100%` dos pacotes manuais elegiveis podem gerar um envelope selado verificavel offline
- `100%` das selagens geram evento oficial em `audit_logs`
- `100%` das verificacoes recalculam e conferem `package_sha256`
- `0` dependencia de string inline ou estado local para confiar na validade da selagem
- tempo alvo de selagem sincrona `p95 <= 3s` em ambiente nominal

## Contexto do Sistema

O diagrama abaixo resume o caminho completo da selagem forte, da consulta do pacote ate a verificacao offline do envelope.

```mermaid
flowchart LR
    E[/evidence cockpit] --> AR[App Router]
    AR --> I[investigation-api]
    I --> PK[Pacote canonico e package_sha256]
    I --> SO[signoff requests e sign-offs]
    I --> V[Validacao de role, signer_role e integridade]
    V --> SR[seal request]
    SR --> SS[institutional seal service]
    SS --> K[KMS e HSM]
    SS --> ENV[Envelope assinado]
    ENV --> I
    I --> AU[audit_logs]
    I --> ET[evidence_trail sintetico]
    I --> ST[estado sealed, revoked ou superseded]
    ST --> AC[/audit cockpit]
    ST --> E
    E --> OFF[verificacao offline]
    AC --> OFF
```

## Opcoes de Arquitetura

| Opcao | Descricao | Vantagens | Desvantagens | Complexidade | Manutencao | Escalabilidade |
| --- | --- | --- | --- | --- | --- | --- |
| A | Sign-off somente em banco, sem assinatura criptografica | simples, barata, rapida | baixa forca probatoria, nao resolve verificacao offline, fraca contra adulteracao institucional | baixa | baixa | alta |
| B | Envelope assinado off-chain com JWS/COSE usando KMS/HSM institucional | bom equilibrio entre seguranca, custo e auditabilidade; verificacao offline; revogacao controlada | requer modelagem de sign-off, KMS e cadeia de certificados | media | media | alta |
| C | Envelope assinado + TSA externa e/ou ancoragem on-chain | prova temporal/externa mais forte, boa para cenarios litigiosos | custo maior, operacao mais complexa, maior irreversibilidade e dependencia externa | alta | alta | media |

## Recomendacao

### Opcao recomendada

- `Opcao B - Envelope assinado off-chain com KMS/HSM institucional`

### Por que esta e a melhor opcao agora

- fecha o gap real atual: falta de selagem institucional recorrente
- reaproveita o `package_sha256` e o manifesto existentes
- preserva reversibilidade arquitetural antes de assumir custo de TSA ou blockchain
- cabe no desenho atual de `audit_logs` e `investigation-api`
- pode ser estendida depois para `Opcao C` sem invalidar o envelope base

### Trade-offs aceitos

- a prova temporal forte continuara institucional, nao publica, na primeira fase
- o binding final do provider KMS/HSM ficara desacoplado atras de uma abstracao inicial
- o fluxo exigira politica clara de revogacao e supersedencia

### Decisoes agora confirmadas

- quorum minimo inicial: `Compliance + Ops`
- estrategia de provider: `abstracao inicial sem binding definitivo`
- timestamp externo/TSA: adiado para fase posterior

## Arquitetura Recomendada

### Componentes principais

#### 1. `evidence` / App Router

Responsabilidade:

- iniciar `seal request`
- exibir estado `pending_signoff`, `ready_to_seal`, `sealed`, `revoked`, `superseded`
- permitir download do envelope de selagem e do pacote canonico

Input:

- `request_id`, `report_id`, `scope_id`, `manual_review_action`

Output:

- solicitacao de sign-off
- solicitacao de selagem
- visualizacao do envelope e do status

Casos de erro:

- pacote inexistente
- sign-off incompleto
- artefato supersedido
- selagem falhou no provider institucional

#### 2. `investigation-api`

Responsabilidade:

- validar elegibilidade da selagem
- recomputar o pacote canonico e o `package_sha256`
- persistir `seal_request`, `signoffs` e `seal_envelope`
- registrar eventos oficiais em `audit_logs`

Input:

- requisicoes autenticadas do frontend/App Router
- contexto institucional do tenant/org

Output:

- envelope assinado
- status de selagem
- metadados auditaveis

Casos de erro:

- digest divergente
- sign-off insuficiente
- chave institucional indisponivel
- politica de classificacao invalida

#### 3. `institutional seal service`

Responsabilidade:

- encapsular o provider KMS/HSM
- assinar apenas o digest/envelope minimo
- devolver assinatura, `key_id`, algoritmo e fingerprint do certificado

Dependencias:

- KMS/HSM institucional
- cadeia de certificados ou trust bundle versionado

Casos de erro:

- timeout no KMS
- chave desabilitada
- rotacao sem trust bundle correspondente

#### 4. `audit`

Responsabilidade:

- exibir estado da selagem e eventos relacionados
- tratar `package_sha256` como digest principal e correlacionar `seal_id`, `ticket_ref`, `reason`, trust bundle e governanca pos-selagem
- navegar de volta ao evento-fonte DD/SoF

#### 5. Governanca semanal / sign-off institucional

Responsabilidade:

- anexar ticket, aprovadores, decisao e evidencia operacional
- prover origem formal para o ciclo de aceite

## Modelo de Dados Recomendado

### Tabela `evidence_package_seals`

Campos sugeridos:

- `id` UUID
- `organization_id` UUID
- `package_kind` texto (`manual_review_package`)
- `request_id` texto
- `report_id` texto nullable
- `scope_id` texto
- `manual_review_action` texto
- `package_sha256` texto
- `manifest_schema_version` texto
- `classification` texto
- `signoff_mode` texto
- `seal_status` texto (`pending_signoff`, `ready_to_seal`, `sealed`, `revoked`, `superseded`, `failed`)
- `seal_format` texto (`jws_json_flattened` recomendado)
- `signature_algorithm` texto
- `kms_key_ref` texto
- `certificate_fingerprint_sha256` texto
- `certificate_bundle_ref` texto
- `policy_version` texto
- `sealed_at` timestamptz nullable
- `sealed_by_user_id` UUID nullable
- `revoked_at` timestamptz nullable
- `superseded_by_seal_id` UUID nullable
- `seal_envelope` JSONB
- `verification_summary` JSONB
- `created_at` timestamptz
- `updated_at` timestamptz

Indices sugeridos:

- `(organization_id, request_id, manual_review_action, created_at desc)`
- `(organization_id, package_sha256)`
- `(organization_id, seal_status, created_at desc)`

### Tabela `evidence_package_signoffs`

Campos sugeridos:

- `id` UUID
- `seal_id` UUID FK
- `organization_id` UUID
- `signer_role` texto (`compliance_owner`, `ops_owner`, `legal_owner_optional`)
- `signer_user_id` UUID nullable
- `signer_display_name` texto
- `decision` texto (`approved`, `rejected`)
- `signoff_method` texto (`platform_authenticated_2fa`, `governance_ticket`)
- `ticket_ref` texto nullable
- `notes` texto nullable
- `signed_at` timestamptz
- `metadata` JSONB

Indices sugeridos:

- `(seal_id, signer_role)`
- `(organization_id, signed_at desc)`

## Contratos de API Canonicos

- a referencia HTTP canônica desta trilha agora e `./api-contracts.md`
- o frontend privilegia leitura por digest via `GET /api/app/evidence/manual-package/seal?package_sha256=...`
- o backend expõe como contratos primarios:
  - `POST /api/v1/evidence/manual-package/signoff-requests`
  - `POST /api/v1/evidence/manual-package/seals/{seal_id}/signoffs`
  - `POST /api/v1/evidence/manual-package/seals/{seal_id}/finalize`
  - `POST /api/v1/evidence/manual-package/seals/{seal_id}/revoke`
  - `POST /api/v1/evidence/manual-package/seals/{seal_id}/supersede`
  - `GET /api/v1/evidence/manual-package/seals/by-digest`
- `GET /api/v1/evidence/manual-package/seals/{seal_id}` permanece suportado como contrato administrativo/secundario
- qualquer mudanca futura de request/response deve ser atualizada primeiro em `./api-contracts.md`

## Envelope Criptografico Recomendado

### Formato

- `JWS JSON Flattened` como baseline inicial

### Payload canonico do envelope

- `package_sha256`
- `manifest_schema_version`
- `request_id`
- `report_id`
- `scope_id`
- `manual_review_action`
- `classification`
- `signoff_mode`
- `signoff_snapshot_sha256`
- `issued_at`
- `issuer`
- `tenant_id`
- `certificate_fingerprint_sha256`

### Motivo

- amplamente verificavel
- bom suporte em bibliotecas
- desacoplado do pacote original
- facilita migracao futura para TSA ou ancora externa

## Eventos de Auditoria Implementados

- `evidence_manual_review_package_signoff_requested`
- `evidence_manual_review_package_signoff_recorded`
- `evidence_manual_review_package_sealed`
- `evidence_manual_review_package_seal_revoked`
- `evidence_manual_review_package_seal_superseded`

Campos obrigatorios em `metadata`:

- `seal_id`
- `package_sha256`
- `request_id`
- `report_id` quando existir
- `scope_id`
- `manual_review_action`
- `signer_role` quando aplicavel
- `certificate_fingerprint_sha256` quando aplicavel
- `policy_version`

## Seguranca

- assinar somente com chave nao exportavel em KMS/HSM
- exigir autenticacao forte para `signoff_method=platform_authenticated_2fa`
- baseline materializada: `local_totp` com `X-2FA=ok` ou `external_provider` homologado com `X-MFA-Provider-Homologated=true`
- usar RBAC por papel institucional, nao apenas por permissao generica
- recalcular `package_sha256` no backend antes de qualquer assinatura
- tratar revogacao e supersedencia como eventos formais, nunca como update silencioso
- nunca sobrescrever envelopes antigos; manter historico imutavel

## Observabilidade e Resiliencia

- correlation id por requisicao de selagem
- logs estruturados com `seal_id`, `request_id`, `package_sha256`
- violacoes de MFA em `platform_authenticated_2fa` devem gerar evento auditavel dedicado e metricas `last_hour` com breakdown por tipo
- quando houver violacao `last_hour`, o stack operacional promove `warning` no Prometheus e o cockpit de monitoramento exibe o KPI agregado para triagem
- o card operacional de MFA no cockpit expõe atalho direto para o preset `/audit?preset=manual-package-mfa`, preservando filtros `action=evidence_manual_review_package_mfa_violation` e `resource_type=evidence_package_seal` para reduzir o tempo de triagem sem abrir nova API dedicada
- o preset de auditoria para MFA agrupa familias navegaveis por `request_id` e `seal_id`, permitindo drill-down operacional sem nova consulta especializada no backend
- as familias MFA no preset sao ordenadas por recorrencia (`totalEvents`), depois por criticidade operacional (`mfa_not_homologated_for_oidc` antes de `2fa_required`) e por fim por recencia
- existe cobertura E2E especifica para desempate entre familias com mesmo volume, garantindo que a criticidade operacional prevaleça sobre a recencia
- o preset de auditoria para MFA resume a distribuicao por tipo de violacao (`2fa_required`, `mfa_not_homologated_for_oidc` e residuais), acelerando a identificacao da falha dominante no recorte
- existe cobertura E2E especifica para familias MFA residuais, garantindo classificacao em `Outros tipos` e realce visual neutro quando nao houver `2fa_required` nem `mfa_not_homologated_for_oidc`
- o preset de auditoria para MFA resume recorrencia por `auth_role` e `signer_role`, acelerando triagem institucional sem exigir agregacao adicional no backend
- cada familia MFA recebe realce visual pelo tipo dominante da falha: `danger` para `provider not homologated`, `warning` para `2FA missing` e neutro para residuais
- a jornada `monitoring -> /audit?preset=manual-package-mfa -> familia -> detalhe` possui cobertura E2E focalizada para validar o handoff operacional completo
- timeout curto no provider institucional com retry controlado e backoff
- idempotencia por `(organization_id, package_sha256, policy_version)`
- fila assíncrona opcional se `p95` ultrapassar o SLA

## Proximos Endurecimentos Recomendados

### Trilha residual imediata

- homologar provider institucional definitivo atras da abstracao atual (`KMS/HSM` ou equivalente)
- formalizar trust bundle institucional versionado
- amarrar aceite operacional recorrente em janela seria

### Trilha residual de medio prazo

- avaliar TSA externa ou ancora complementar para casos de litigio/regulatorio forte
- reaplicar o padrao aos dossies oficiais ROS/COAF
- automatizar verificacao offline recorrente como checker operacional

## Riscos Tecnicos

| Risco | Probabilidade | Impacto | Mitigacao |
| --- | --- | --- | --- |
| provider KMS/HSM definitivo nao homologado retardar o endurecimento final | media | alta | manter a abstracao atual e separar claramente baseline funcional de binding final |
| envelope sem politica clara de revogacao gerar ambiguidade | media | alta | modelar `revoked` e `superseded` desde o inicio |
| sign-off por usuario sem papel institucional reduzir valor probatorio | media | alta | exigir roles institucionais e opcao de ticket formal |
| rotacao de certificados quebrar verificacao retroativa | baixa | alta | guardar `certificate_fingerprint_sha256` e `certificate_bundle_ref` versionados |
| querer ancora on-chain cedo demais elevar custo e acoplamento | media | media | manter on-chain como fase posterior |

## Assuncoes Explicitas

- o hash principal do pacote continuara sendo `package_sha256`
- a primeira versao forte sera off-chain
- `investigation-api` e o melhor bounded context para persistir a selagem
- DD e SoF compartilham o mesmo modelo de selagem, variando apenas `manual_review_action` e politica

## Confianca Atual

- `96%`

### Por que subiu

- a baseline arquitetural recomendada foi efetivamente implementada em backend, frontend, audit e E2E
- a ambiguidade contratual foi reduzida ao mover a fonte HTTP canônica para `./api-contracts.md`
- os gaps remanescentes agora sao de endurecimento institucional, nao de ausencia da trilha funcional

## Perguntas Pendentes

1. O provedor final de producao sera `AWS KMS`, `Cloud HSM`, `Vault Transit` ou outro backend plugavel atras da abstracao?
2. O trust bundle sera emitido por AC corporativa, bundle interno versionado ou integracao hibrida?
3. Em qual milestone a organizacao quer introduzir TSA/ancora externa complementar?

## Proximos Passos

1. homologar provider institucional definitivo e trust bundle versionado
2. anexar evidencias recorrentes dessa trilha a janela seria/governanca semanal
3. avaliar TSA/ancora externa apenas como endurecimento posterior
4. reaplicar o padrao aos dossies oficiais quando a cadeia DD/SoF estiver institucionalmente fechada

## Decisao

- `✅ PRONTO PARA IMPLEMENTACAO`
- a arquitetura baseline esta aprovada com `Opcao B`, quorum `Compliance + Ops`, provider inicialmente abstraido e sem TSA na primeira release
