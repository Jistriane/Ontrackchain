# ROPD OTK-0006 — Feed PEP OFAC Interpol UE Tokenizado (Read Only)

| # | Campo LGPD Art.37 | Valor |
|---|---|---|
| 1 | ID Operação | `OTK-ROP-0006-v1.0` |
| 2 | Nome Operação | Consumo diário de listas públicas PEP OFAC SDN + Interpol Vermelho + UE Sanctions (Tokenizados) |
| 3 | Categoria Titulares | Pessoas constantes em listas OFAC SDN, Interpol Notificações (PF investigadas), Lista PEP CGU Brasil (servidores públicos 3º escalão acima + familiares). Todos dados são PÚBLICOS. |
| 4 | Categorias Dados Pessoais | Nome completo, data nascimento, nacionalidade, país emissão passaporte, descrição do delito (Interpol), cargo PEP, lista de sancionado OFAC, IDs de identificação conhecidos (parciais). |
| 5 | Dados Sensíveis? | NÃO. Dados públicos = exceção LGPD Art.4º Inciso VI (dados pessoais tornados públicos pelo titular) e Art.7º IX (consumo de fonte pública). |
| 6 | Base Legal | Art.7 Inciso III (Obrigação legal BACEN Circular Nº 3.949/2019 Art.13: consulta obrigatória de listas de pessoas sancionadas / PEPs). |
| 7 | Finalidade | Bloqueio automático ou alertas de risco elevado em investigações e cadastros de novos clientes. |
| 8 | Compartilhamento? | NÃO (operamos read-only). Fontes são públicas (não enviamos dados de volta). |
| 9 | Retenção | 120 meses (10 anos, BACEN 3.949). |
| 10 | Destruição | Apagamos feeds vencidos quando a entidade é removida da lista pública OFAC/Interpol. Mantemos hash para prova histórica. |
| 11 | Medidas Segurança | Tokenização hash SHA-256 para busca (não armazenamos CPF se a lista NÃO tem; apenas hashes para comparação). |
| 12 | DPO Contato | Ver ROPD-0001. |
