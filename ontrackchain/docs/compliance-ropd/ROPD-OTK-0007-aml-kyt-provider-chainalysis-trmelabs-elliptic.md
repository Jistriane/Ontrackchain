# ROPD OTK-0007 — AML KYT Provider (Chainalysis / TRM Labs / Elliptic) Compartilhamento

| # | Campo LGPD Art.37 | Valor |
|---|---|---|
| 1 | ID Operação | `OTK-ROP-0007-v1.0` |
| 2 | Nome Operação | AML/KYT Know Your Transaction compartilhamento internacional |
| 3 | Categoria Titulares | Investido PF que tem transações cripto suspeitas (endereços blockchain analisados). |
| 4 | Categorias Dados Pessoais | Hash da transação (TXID), endereço blockchain hash160, valor da transação em USD/BRL, timestamp, risco score atribuído 0-100. **NÃO enviamos CPF/Nome ao provider**. |
| 5 | Dados Sensíveis? | NÃO. Apenas hashes pseudônimos (ANPD LGPD Art.4º V dado pseudonimizado não permite re-identificação sem chave separada guardada localmente). |
| 6 | Base Legal | Art.7 Inciso III (BACEN Circular Nº 3.949/2019 Art. 27 comunicação obrigatória ao COAF). |
| 7 | Finalidade | Identificar operações suspeitas de lavagem de dinheiro e comunicação ao COAF BACEN no prazo regulamentar. |
| 8 | Compartilhamento? | SIM. Provider internacional Chainalysis (EUA) / TRM Labs (EUA) / Elliptic (Reino Unido). Cláusulas SCCs + LGPD Art. 35 transferência internacional. |
| 9 | Retenção | 120 meses (10 anos, BACEN 3.949). |
| 10 | Destruição | 10 anos. |
| 11 | Medidas Segurança | API key do provider guardada AWS Secrets Manager (NÃO no repositório). Acesso logs envio. |
| 12 | **DPO Contato (Art.41)** | Dr(a). [NOME A SER PREENCHIDO APÓS CONTRATO], DPO Ontrackchain. Email LGPD: dpo@ontrackchain.com.br. Telefone: +55 (11) 9XXXX-XXXX. Formulário online titular: https://ontrackchain.com.br/lgpd. Link política de privacidade: https://ontrackchain.com.br/privacidade. Endereço sede: Rua XXX, nº YYY, Bairro ZZZ, São Paulo/SP, CEP 0XXXX-000, Brasil. |
