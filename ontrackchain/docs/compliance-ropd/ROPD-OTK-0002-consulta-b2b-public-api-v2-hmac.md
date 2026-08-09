# ROPD OTK-0002 — Consulta B2B Public API v2 HMAC

| # | Campo LGPD Art.37 | Valor |
|---|---|---|
| 1 | ID Operação | `OTK-ROP-0002-v1.0` |
| 2 | Nome Operação | Consulta B2B Public API v2 HMAC |
| 3 | Categoria Titulares | Clientes B2B PJ que contratam a API (pessoas jurídicas, seus funcionários autenticados) + Pessoas PF titular do CPF/CNPJ consultado |
| 4 | Categorias Dados Pessoais | CPF do titular da consulta, CNPJ da empresa cliente, Endereço IP do cliente (log de acesso), user-agent cliente, Data/hora consulta, Request-ID X-Correlation-ID, Resultado score Risco (0 a 100) |
| 5 | Dados Sensíveis? | NÃO (consulta não retorna saúde/raça/religião). Dados financeiros = score risco (considerado não sensível pois é operação de crédito/risk scoring, não saúde financeira pessoal em detalhe). |
| 6 | Base Legal | Art.7 Inciso II (Execução de contrato prestação de serviços B2B celebrado com o cliente). Art.7 Inciso V (Legítimo interesse anti-fraude). |
| 7 | Finalidade | Prestar serviço de triagem financeira automatizada via API B2B. |
| 8 | Compartilhamento? | NÃO. Nenhum dado pessoal processado na operação sai do ambiente Ontrackchain para terceiros nesta operação. |
| 9 | Retenção | 12 meses (365 dias, alinhado com faturamento e auditoria PLD BACEN). |
| 10 | Destruição | Exclusão lógica em 12m → física 90d depois. |
| 11 | Medidas Segurança | HMAC-SHA256 (ADR-019), TLS 1.3, rate limit k6 50VUs, RBAC API key por cliente B2B. |
| 12 | DPO Contato | Ver ROPD 0001 (mesmo DPO / endereço). |

---
### Sign-off: ver ROPD-0001. Todo arquivo individual tem sign-off consolidado no CSV final.
