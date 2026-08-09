# TEMPLATE-RIPD-POR-CLIENTE-B2B — Relatório de Impacto à Proteção de Dados (LGPD Art.15) [CLIENTE_RAZAO_SOCIAL] [CLI-ID: CLIENTE_ID_UNICO]

*INSTRUÇÃO DE USO (PREENCHER E REMOVER ESTE BLOCO ANTES DE ASSINAR):*
1. *Duplicar este arquivo como:* `RIPD-OTK-CLI-0001-NOME-CURTO-CLIENTE-v1.0.md`
2. *Substituir TODOS os placeholders:* `CLIENTE_*` → dados reais do cliente.
3. *Preencher* Seção 17 (Específica Cliente — NÃO existe no mestre).
4. *Sign-off*: 4 assinaturas obrigatórias no final. Válido 12 meses após assinatura.
5. *Hash*: Gerar `sha256sum RIPD-OTK-CLI-XXXX-v1.0.md > hashes/SHA256-RIPD-OTK-CLI-XXXX.sha256` e commitar.

| # | Campo RIPD Art.15 LGPD | Resposta (CLIENTE ESPECÍFICO - preencher) |
|---|---|---|
| 1 | **ID RIPD Único + Versão + Data Criação** | `RIPD-OTK-CLI-0001-CLIENTE_NOME-v1.0` criado CLIENTE_DATA_CRIACAO. Atualizações SemVer. |
| 2 | **Nome da Organização CONTROLADORA CLIENTE (Art.5 VI)** | CLIENTE_RAZAO_SOCIAL_COMPLETA. CNPJ CLIENTE_CNPJ_FORMATADO. Endereço CLIENTE_ENDERECO_COMPLETO. Representante Legal: CLIENTE_REPRESENTANTE_LEGAL (CPF + Cargo). |
| 3 | **Nome da Processadora (Ontrackchain — Contrato CLT / Terceirizado Art.48 LGPD)** | Ontrackchain Soluções em Tecnologia S.A. CNPJ já cadastrado. Contrato B2B Nº CONTRATO_NUMERO, vigência CONTRATO_DATA_INICIO → CONTRATO_DATA_FIM. Base legal processamento subcontratada: Art.7 V (execução contrato Ontrackchain × Cliente). |
| 4 | **Encarregado LGPD (DPO cliente + DPO Ontrackchain 2 DPOs envolvidos)** | a) DPO CLIENTE: Nome ______ CRP/CRC ______ E-mail ______ Telefone ______; b) DPO Ontrackchain: Dr. Carlos Alberto Mendes - dpo@ontrackchain.com.br (já registrado mestre). Comunicação ANPD deve incluir ambos. |
| 5 | **Natureza das Operações CLIENTE ESPECÍFICA** | CLIENTE_NATUREZA_OPERACOES_ESPECIFICAS. Exemplos: 1) Onboarding due diligence PF/PJ sob contrato; 2) Consulta API v2 B2B HMAC screening entidades; 3) Análise documental AI LLM assistida; 4) Relatórios ROS/COAF. |
| 6 | **Finalidade do Tratamento CLIENTE ESPECÍFICA (Art.9 finalidade obrigatória)** | CLIENTE_FINALIDADES_ESPECIFICAS. Deve ser ESPECÍFICA, NÃO GENÉRICA. Máximo 5 finalidades. "Due diligence PLD/CFT conforme BACEN Circular 3.978" é exemplo válido. |
| 7 | **Categorias de Titulares CLIENTE ESPECÍFICO** | CLIENTE_CATEGORIAS_TITULARES. Ex: "Funcionários PF do cliente (500); Clientes PF do cliente (12.000); Clientes PJ do cliente (800); Fornecedores PF/PJ (450)". |
| 8 | **Categorias de Dados Pessoais CLIENTE ESPECÍFICO** | CLIENTE_CATEGORIAS_DADOS. Ex: "Dados PF (CPF, RG, Nome, Data Nasc, Endereço, Celular, Email); Dados PJ (CNPJ, Razão Social, IE, Quadro Societário); Dados Financeiros (Receita mensal origem, Extratos bancários 3 últimos meses - confidencial)". |
| 9 | **Dados Sensíveis Art.5 XIII CLIENTE ESPECÍFICO (SIM/NÃO + base legal)** | CLIENTE_DADOS_SENSIVEIS_FLAG. Se SIM: especificar ART.7 BASE LEGAL (NUNCA usar legítimo interesse para sensível). Ex: "SIM, dado saúde 3% titulares. Base legal: Art.7 II consentimento explícito por escrito". NÃO é padrão. |
| 10 | **Destinatários Compartilhamento CLIENTE ESPECÍFICO + Partilha Extra** | a) Ontrackchain (destinatários internos já listados mestre RIPD OTK); b) CLIENTE_DESTINATARIOS_EXTRAS. Ex: "Cliente sistema ERP via webhook mTLS autenticado — NÃO partilha dados sensíveis; Regulador BACEN se notificação COAF obrigatória lei". |
| 11 | **Transferência Internacional CLIENTE ESPECÍFICA (SIM/NÃO + País + SCCs)** | CLIENTE_TRANSF_INTERNACIONAL_FLAG. Ex: "SIM — AML KYT provider Chainalysis EUA (Nova York). SCCs Decisão UE 2021/914 + ANPD CD-002/2024. Cliente tem direito de OP-OUT: escolher Local Llama 3.1 sem transferência AI. AML KYT NÃO tem OP-OUT por obrigação BACEN." |
| 12 | **Base Legal Art.7 LGPD CLIENTE ESPECÍFICO (percentuais devem somar 100%)** | CLIENTE_BASE_LEGAL_PERCENTUAIS. Ex: "Art.7 III (obrig. BACEN): 80%; Art.7 V (contrato): 15%; Art.7 II (consentimento sensíveis): 5%". Total 100%. |
| 13 | **Medidas Técnicas Específicas Cliente (Além do mestre, se tiver exigências)** | CLIENTE_MEDIDAS_TECNICAS_EXTRA. Ex: "Cliente exige criptografia AES-256-HSM GCP KMS por chave por cliente (não por tenant). Implementado via KMS wraparound coluna pg_crypto extra no investigation-api". Se não houver, escrever "Nenhuma extra, segue mestre RIPD-OTK-MASTER Art.32". |
| 14 | **Prazo de Retenção Máxima CLIENTE ESPECÍFICO (meses)** | CLIENTE_RETENCAO_MESES. Ex: "Contrato BACEN exige 10 anos (120 meses) caso fechado, 5 anos (60 meses) contrato ativo. Retenção mínima obrigatória lei. Cliente pode pedir extensão mas NÃO redução por ser menor que a lei." |
| 15 | **Destruição Final + Certificado CLIENTE ESPECÍFICO** | CLIENTE_DESTRUICAO_METODO. Ex: "Segue RIPD mestre (soft delete 30 dias + hard delete + VACUUM FULL). Extra: Cliente recebe e-mail confirmação destruição após processo, com anexo PDF certificado SHA-256 hash 2 assinaturas". |
| 16 | **Assinaturas DPO CLIENTE + Jurídico CLIENTE + DPO OTK + CEO OTK (MÍNIMO 4 assinaturas)** | 1) DPO CLIENTE: Nome ______ Data ______ Assinatura ______ Email ______; 2) Jurídico/CLO CLIENTE: Nome ______ Data ______ Assinatura ______ Email ______; 3) DPO Ontrackchain: ______ Assinado MESTRE; 4) Diretor Contrato Ontrackchain (CRO): Nome ______ Data ______ Assinatura ______. |

---

## 17. Seção ESPECÍFICA CLIENTE (NÃO existe no mestre. OBRIGATÓRIO preencher)

| Item Específico Cliente | Resposta |
|---|---|
| 17.1 **Setor de Atividade** | CLIENTE_SETOR: (Financeiro / Jurídico / Varejo / Saúde / Governo / Outros) |
| 17.2 **Volume esperado titulares por ano** | CLIENTE_VOLUME_TITULARES (Ex: 50.000 PF + 5.000 PJ por ano) |
| 17.3 **Contrato tem dados biométricos?** | CLIENTE_FLAG_BIOMETRIA (SIM / NÃO). Se SIM → Art.22 LGPD consentimento explícito obrigatório. |
| 17.4 **Critério Risco Nível Final (baixo / médio / alto / muito alto)** | CLIENTE_NIVEL_RISCO (Art.15 §2 LGPD). Muito alto = obrigatório realizar Avaliação de Risco DPIA adicional ANPD. |
| 17.5 **Fluxos partilha extra cliente (webhooks, integrações)** | CLIENTE_FLUXOS_PARTILHA. Ex: "Cliente ERP envia webhook POST /webhook/cliente-x/dd-resultado após due diligence — autenticação mTLS cliente, IP allowlist 203.0.113.0/24, rate limit 60 req/min". Se nenhum, escrever Nenhum. |
| 17.6 **Data início vigência contrato B2B** | CLIENTE_DATA_VIGENCIA_INICIO. (Relacionar com retenção meses Art.14) |
| 17.7 **ID contrato + anexos** | CLIENTE_ID_CONTRATO: ______; Anexo LGPD (Sim/Não): ______; Anexo DPA SCCs transf internacional (Sim/Não): ______. |
| 17.8 **Data próxima revisão obrigatória RIPD (máximo 12 meses)** | CLIENTE_DATA_REVISAO_RIPD: ______ (no máximo 12 meses após criação, Art.15 §LGPD ANPD). |

---

### Observações adicionais cliente:

CLIENTE_OBSERVACOES_LIVRES (se necessário). Exemplo: "Cliente exige SIEM Splunk dashboard dedicado por cliente (multi-tenant separado). Retenção logs 360 dias."
