# ROPD OTK-0005 — Billing Stripe Cadastro Cliente + Invoice Faturamento

| # | Campo LGPD Art.37 | Valor |
|---|---|---|
| 1 | ID Operação | `OTK-ROP-0005-v1.0` |
| 2 | Nome Operação | Billing Stripe Multi-Tenant 3 moedas BRL/USD/EUR Cadastro + Invoice + Portal cliente |
| 3 | Categoria Titulares | Cliente PJ B2B (pessoa jurídica) + responsável legal PF |
| 4 | Categorias Dados Pessoais | Razão social, CNPJ, Nome responsável legal PF, CPF do responsável legal (para antifraud Stripe Radar), Email faturamento, Endereço sede (logradouro, CEP, cidade, estado/UF), País (para cálculo de imposto ISS/IRRF/IOF), Dados bancários mascarados crédito/deb (últimos 4), Invoice Stripe id |
| 5 | Dados Sensíveis? | NÃO. Apenas dados cadastrais PF do responsável legal (dado comum). |
| 6 | Base Legal | Art.7 Inciso II (Contrato prestação serviços B2B celebrado com o cliente — faturamento é obrigação contratual). Art.7 Inciso III (Obrigação tributária acessória federal/receita). |
| 7 | Finalidade | Faturar serviços de investigation API, emitir NF-e/NFS-e, controle de assinatura tier (startup/business/enterprise), cobrança recorrente cartão crédito/débito. |
| 8 | Compartilhamento? | SIM — Stripe Payments Inc. (EUA / Irlanda). Cláusulas Contratuais Padrão UE (SCCs) + LGPD Art.35 Transferência Internacional. Dados compartilhados são apenas essenciais: CPF CNPJ responsável, endereço, valor invoice. |
| 9 | Retenção | 60 meses (5 anos — BACEN 3.949 Art.34 + Lei 5.172/66 Código Tributário Nacional retenção mínima 5 anos de documentos fiscais). |
| 10 | Destruição | 5 anos → exclusão lógica → física. |
| 11 | Medidas Segurança | Webhook HMAC SHA-256 (ADR-024). Idempotência event_id. PCI DSS SAQ-A compliant (Stripe hospeda cartões). |
| 12 | **DPO Contato (Art.41)** | Dr(a). [NOME A SER PREENCHIDO APÓS CONTRATO], DPO Ontrackchain. Email LGPD: dpo@ontrackchain.com.br. Telefone: +55 (11) 9XXXX-XXXX. Formulário online titular: https://ontrackchain.com.br/lgpd. Link política de privacidade: https://ontrackchain.com.br/privacidade. Endereço sede: Rua XXX, nº YYY, Bairro ZZZ, São Paulo/SP, CEP 0XXXX-000, Brasil. |
