# ROPD OTK-0001 — Onboarding Estrutural Triagem LGPD RIPD Art.15

| # | Campo LGPD Art.37 | Valor |
|---|---|---|
| 1 | **ID Operação** | `OTK-ROP-0001-v1.0` (hash SHA-256 do arquivo = preencher em sign-off DPO) |
| 2 | **Nome Operação** | Triagem estrutural onboarding investigação (LGPD RIPD Due Diligence Art.15) |
| 3 | **Categoria Titulares** | Pessoas Físicas investigadas (Investidos) + Pessoas Expostas Politicamente (PEPs) + Familiares / Conjuge / Sócios (vínculo 1º/2º grau) |
| 4 | **Categorias Dados Pessoais** | CPF, Nome completo, Data de nascimento, RG, Nº documento estrangeiro (passaporte para não-brasileiros), Email, Telefone celular, Endereço residencial, Foto facial pública (redes sociais), Nome da mãe, Nome do pai, Ocupação, Redes sociais (LinkedIn/Twitter/X públicos), Escolaridade, Órgãos / empresas em que trabalhou (10 anos retro) |
| 5 | **Dados Sensíveis (Art.5 LGPD)? Quais?** | SIM. Origem racial/étnica (auto-declaração cadastrada opcionalmente), Dados sobre saúde (casos suspeitos na investigação - Art.10 inciso IV), Dados financeiros (renda mensal declarada, bens imóveis/móveis tabelionatos) |
| 6 | **Base Legal Art.7 LGPD** | **Art.7 Inciso III** — Cumprimento de obrigação legal ou regulatória pelo controlador (BACEN Circular Nº 3.978/2020 Art.12; BACEN Circular Nº 3.949/2019 PLD/CFT). Art.7 V — Legítimo Interesse prevenção fraude (ANPD CD-005 Art.11 §3º) |
| 7 | **Finalidade do Tratamento** | 1) Cumprir obrigação de Due Diligence regulatória exigida pelo BACEN na abertura e manutenção de conta PJ em clientes sujeitos à Circular 3.978. 2) Prevenir lavagem de dinheiro e financiamento do terrorismo (PLD/CFT). 3) Mitigar risco de reputação à Ontrackchain antes de processar investigações envolvendo o titular. 4) Gerar relatório RIPD Due Diligence com data e hash, válido como prova judicial e administrativa. |
| 8 | **Compartilhamento / Transferência Internacional?** | SIM. Dados **parciais** (CPF criptografado AES-256) compartilhados com 2 feeds PEP públicos externos: (a) Lista PEP da Controladoria-Geral da União (CGU) — hospedada no Brasil, NÃO transferência internacional; (b) OFAC SDN List (US Treasury) — EUA (transferência internacional Art.32 LGPD — garantias adequadas Cláusulas Padrão Contratuais (CPCs) vigentes). NENHUM dado sensível (raça, saúde, biométrico) é enviado fora do Brasil. AML/KYT Provider externo (Chainalysis/TRM/Elliptic) — apenas hashes de transações, não CPF/dados sensíveis. |
| 9 | **Retenção Máxima (meses)** | 60 meses (5 anos, contados a partir da data de encerramento da investigação) — alinhado com BACEN 3.978 Art.34 prazo guarda documentos. |
| 10 | **Destruição Após Retenção** | Procedimento: `soft delete` em banco PG (campo `deleted_at` + Policy RLS impossibilita leitura); após 90 dias do soft delete → `pgcrypto` apaga linhas definitivamente; backup AWS S3 KMS CMK apagado (chave rotacionada); evidência hash SHA-256 de destruição armazenada em `docs/compliance-ropd/destruicoes/` por 180 meses extras (15a mínimo LGPD Art.46). |
| 11 | **Medidas Segurança Téc./Admin. Art.32 LGPD** | (1) Cifra em repouso PG AES-256 GCM (pgcrypto) + AWS S3 SSE-KMS CMK; (2) Cifra trânsito TLS 1.3 A+ SSL Labs; (3) Cloudflare WAF Managed Ruleset anti-injeção anti-DDoS; (4) MFA WebAuthn Obrigatório para roles OTK_ADMIN / OTK_COMPLIANCE_OFFICER (investigation-api); (5) RBAC OTK_* least privilege 5 roles; (6) Row Level Security (RLS) por organização; (7) Auditoria SIEM Splunk 180 dias (todos logs access); (8) Backups criptografados com KMS CMK, RPO ≤ 6h RTO ≤ 2h. |
| 12 | **DPO Contato (Art.41)** | Dr(a). [NOME A SER PREENCHIDO APÓS CONTRATO], DPO Ontrackchain. Email LGPD: dpo@ontrackchain.com.br. Telefone: +55 (11) 9XXXX-XXXX. Formulário online titular: https://ontrackchain.com.br/lgpd. Link política de privacidade: https://ontrackchain.com.br/privacidade. Endereço sede: Rua XXX, nº YYY, Bairro ZZZ, São Paulo/SP, CEP 0XXXX-000, Brasil. |

---

### Sign-off Aprovação ROPD (Obrigatório ANPD)
| Cargo | Nome (assinar) | Data (dd/mm/aaaa) | Hash SHA-256 do arquivo no momento do sign |
|---|---|---|---|
| Controlador (CEO Ontrackchain) | | | |
| DPO | | | |
| Jurídico Compliance LGPD | | | |
| Arquiteto Chefe | | | |

Documento pode ser atualizado sem novo sign-off APENAS para correções de typo. Qualquer alteração nos campos 3→11 = nova versão (v1.1, v1.2...) + novo sign-off.
