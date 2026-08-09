# ROPD OTK-0004 — Autenticação OIDC + MFA WebAuthn YubiKey

| # | Campo LGPD Art.37 | Valor |
|---|---|---|
| 1 | ID Operação | `OTK-ROP-0004-v1.0` |
| 2 | Nome Operação | Autenticação OIDC Keycloak v25 + MFA WebAuthn/YubiKey Nível 2 BACEN |
| 3 | Categoria Titulares | Pessoas Físicas usuários da plataforma (funcionários da Ontrackchain; colaboradores clientes B2B PF) |
| 4 | Categorias Dados Pessoais | Username, Email profissional, Nome completo, Cargo, Credencial OIDC sub claim, Session ID criptografado, WebAuthn credential id (public key COSE ES256/RS256), Logs data/hora login + falha login, IP origem, país geolocalização login |
| 5 | Dados Sensíveis? | SIM. **Dado biométrico / dado de autenticação forte**: impressão digital da impressão digital do YubiKey (credential public key = dado biométrico equivalente LGPD Art.5 §XIII). |
| 6 | Base Legal | Art.7 Inciso III (BACEN Circular 3.978 Art.12 Controles de Acesso Nível 2). Art.7 Inciso VI (Execução de contrato de trabalho / prestação de serviço colaborador). |
| 7 | Finalidade | Garantir autenticação forte de colaboradores conforme regulamentação BACEN. |
| 8 | Compartilhamento? | NÃO. Todas credenciais armazenadas Keycloak SGBD PG dedicado (cluster patroni SEPARADO do investigation-api). SAML enterprise federation = credenciais NÃO saem; cliente IdP gerencia. |
| 9 | Retenção | 36 meses (3 anos após desligamento do usuário / encerramento contrato cliente). |
| 10 | Destruição | Revoke de credenciais WebAuthn em Keycloak → exclusão física após 3 anos. Logs SIEM mantidos 180d. |
| 11 | Medidas Segurança | Istio mTLS STRICT; MFA obrigatório 3 roles admin; Cloudflare WAF auth protection (Handbook P0-01 Q3-07 Playwright). |
| 12 | DPO Contato | Ver ROPD-0001. |
