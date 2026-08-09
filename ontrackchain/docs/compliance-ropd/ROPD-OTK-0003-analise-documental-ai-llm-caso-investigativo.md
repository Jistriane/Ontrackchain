# ROPD OTK-0003 — Análise Documental AI LLM Caso Investigativo

| # | Campo LGPD Art.37 | Valor |
|---|---|---|
| 1 | ID Operação | `OTK-ROP-0003-v1.0` |
| 2 | Nome Operação | Análise documental AI LLM Caso Investigativo |
| 3 | Categoria Titulares | Pessoas investigadas (Investidos) |
| 4 | Categorias Dados Pessoais | Documentos PDF do caso (contratos, extratos bancários mascarados), Nomes, CPFs mascarados (últimos 4 dígitos visíveis dentro do LLM context), históricos email mascarados, notas textuais do analista sobre dados pessoais do titular |
| 5 | Dados Sensíveis? | SIM. Dados sobre saúde (quando menciona internações/atestados) + origem racial (ocasionalmente em investigação de perfil discriminatório). |
| 6 | Base Legal | Art.7 Inciso V (Legítimo interesse prevenção à fraude). Art.7 Inciso III (BACEN Circular 3.978 obrigação). |
| 7 | Finalidade | Gerar resumo inteligível pelo analista, extração entidades, sumarização de 500+ páginas de documentos. |
| 8 | Compartilhamento? | SIM (Transferência internacional EUA se LLM provider = AWS Bedrock / OpenAI). Aplicam-se Standard Contractual Clauses (SCCs) da Comissão Europeia + LGPD Art.32 §2. Dados sensíveis = NÃO ENVIADOS A MODELOS FORA DO BRASIL. Opção padrão: LLM local (self-hosted Llama 3.1 70B em servidores AWS sa-east-1 São Paulo) NÃO tem transferência internacional. |
| 9 | Retenção | 120 meses (10 anos, BACEN 3.949 Art.34 retenção mínima). |
| 10 | Destruição | 10 anos + 90d soft/hard. Exclusão de vetores pgvector (embeddings). |
| 11 | Medidas Segurança | Embeddings criptografados AES-256 at-rest, RLS por organização, contextos criptografados trânsito. |
| 12 | DPO Contato | Ver ROPD-0001. |
