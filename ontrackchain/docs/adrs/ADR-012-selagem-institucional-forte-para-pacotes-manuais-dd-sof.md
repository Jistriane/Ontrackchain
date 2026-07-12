# ADR-012: Selagem Institucional Forte para Pacotes Manuais DD/SoF

## Contexto

O Ontrackchain ja possui uma trilha manual DD/SoF com:

- pacote canonico `manual_review_package/v2`
- manifesto deterministico e `package_sha256`
- evento oficial `evidence_manual_review_package_exported`
- navegacao bidirecional entre `evidence` e `audit`

O gap residual deixou de ser geracao de artefato e passou a ser forca probatoria institucional. O pacote atual e auditavel, mas ainda nao possui assinatura institucional recorrente nem verificacao offline independente.

## Decisao

Adotar como baseline a `Opcao B`: envelope assinado off-chain com `JWS JSON Flattened`, usando uma abstracao inicial de `institutional seal service`, com:

1. quorum minimo inicial `Compliance + Ops`;
2. provider criptografico desacoplado por interface, sem binding definitivo na primeira implementacao;
3. `package_sha256` como digest principal da selagem;
4. TSA/ancora externa explicitamente fora do escopo da primeira release;
5. eventos dedicados em `audit_logs` para sign-off, selagem, revogacao e supersedencia.

## Consequencias

### Positivas

- eleva a custodia manual DD/SoF para um baseline verificavel offline
- preserva o contrato atual do pacote manual sem quebrar export, manifesto ou navegacao existente
- reduz acoplamento prematuro com `AWS KMS`, `Vault Transit` ou outro backend especifico
- cria uma trilha formal para futura expansao a dossies regulatórios mais fortes

### Negativas

- adiciona fluxo de sign-off institucional e maior disciplina operacional
- exige modelagem adicional de `seal_request`, `signoffs`, envelope e verificacao
- posterga prova temporal externa forte para uma fase posterior

## Trade-offs

- foi priorizado `baixo acoplamento + prova institucional suficiente` em vez de binding imediato a um provider especifico
- foi aceita a ausencia de TSA na primeira release para reduzir custo, irreversibilidade e dependencia externa
- foi escolhido quorum `Compliance + Ops` para equilibrar governanca e throughput operacional

## Criterios de Aceitacao

- selagem recalcula `package_sha256` no backend antes da assinatura
- somente pacotes com quorum `Compliance + Ops` completo podem ser selados
- o envelope assinado e verificavel offline com trust bundle versionado
- revogacao e supersedencia nunca sobrescrevem historico existente
- `audit_logs` registra todos os estados criticos da selagem
