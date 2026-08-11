# `contracts/` — Smart Contracts Soroban (Stellar) · Ontrackchain Camada 2

> **Status**: MVP implementado · Compilado WASM `release` · Rede alvo: **Stellar Futurenet primeiro → Mainnet depois**.
> **Convenção Linguagem Dual**: Código/contratos Rust = **EN (inglês)**. Este README Tier6 de uso = **pt-BR**.

## ⚠️ Hard Constraints NÃO NEGOCIÁVEIS (HERDADAS GOVERNANÇA)

| HC | Regra | Como cumprimos aqui |
|---|---|---|
| **HC-1** | NÃO alterar `SIGNOFF-M5.md` | 0 toque no arquivo. |
| **HC-2** | Nenhum segredo hardcoded | 0 chaves privadas, 0 `sk_`, `private`, seed em nenhum arquivo. Todos deploy `soroban contract deploy --source-account $STELLAR_SECRET_KEY` via `.env-futurenet.example` placeholder. |
| **HC-3** | Não adicionar jobs `sonarcloud-*` nos contexts do `.github/settings.yml` | Workflows de CI Soroban ficam em `contracts/.github/workflows-templates/` COMO REFERÊNCIA NÃO EXECUTÁVEL (como arquitetura Tier5). Para ativar, move manualmente para `<repo_root>/.github/workflows/` RAIZ e valida `make settings-dry-run`. |
| **HC-4** | Sprints governança/devX NÃO tocam `apps/**/src` / `packages/**/src` | **Tudo aqui é diretório NOVO `contracts/` nível 1.** 0 alteração em código Python/TS existente. |
| **HC-5** | Dotfiles + Trindade Docs ativos | EditorConfig LF EOL ativo nos `.rs` / `.toml`. Alvo Makefile `make readme` inclui este arquivo no Tier6. |

## 🔭 Objetivo do Lote (Contrato Core — P1-A Default Aprovado)

> Implementar a **Camada 2 descrita em [evidence_trail.py](../../ontrackchain/packages/agents/src/ontrackchain_agents/evidence_trail.py#L10-L11)**:
> "Camada 2 (Fase 3, 2027): Âncora pública Stellar/Soroban para relatórios finais"
>
> Regra LGPD Art. 38 / Res. BCB 520: **NENHUM dado pessoal on-chain**. Apenas hashes SHA-256 cegos + salt 16B off-chain (PostgreSQL `soroban_salt_environment`, migration `0010_*.sql`).

## 📦 Crates do Workspace (11 Total · P1 Completo)

| # | Crate | Caminho | Responsabilidade Única | Papéis Críticos | `#[contract]` |
|---|---|---|---|---|---|
| 1 | `evidence-anchor-v1` | [`evidence-anchor-v1/src/lib.rs`](evidence-anchor-v1/src/lib.rs) | **CORE L1**: Âncora de hashes individuais + raízes Merkle. Verificação off-chain Merkle proof. Idempotente (AlreadyAnchored). | OWNER · UPGRADER · PAUSER · WRITER | ✅ Principal. |
| 2 | `access-control-multisig` | [`access-control-multisig/src/lib.rs`](access-control-multisig/src/lib.rs) | Papéis (OWNER / UPGRADER / PAUSER / WRITER) + threshold por papel (ex: 2/3 multisig para UPGRADER/PAUSER). | OWNER | ✅ Separado de lógica. |
| 3 | `eternal-storage` | [`eternal-storage/src/lib.rs`](eternal-storage/src/lib.rs) | Armazenamento append-only KV separado de lógica. Preserva hashes mesmo que EvidenceAnchorV1 → V2 upgrade. Escreve APENAS por address whitelistado. | OWNER (whitelist) | ✅ Whitelist de lógicas. |
| 4 | `protocol-address-book` | [`protocol-address-book/src/lib.rs`](protocol-address-book/src/lib.rs) | **Registry P1**: 10 slots padronizados (SLOT_*) com endereços on-chain de todos os outros 10 contratos. Facilita upgrade sem tocar múltiplos contratos. | OWNER · CONFIG | ✅ Registry SSOT. |
| 5 | `reputation-sbt-badge` | [`reputation-sbt-badge/src/lib.rs`](reputation-sbt-badge/src/lib.rs) | **P1-B Reputação**: Soulbound Token (SBT) non-transfer, 3 níveis (Bronze ≥50 · Prata ≥75 · Ouro ≥90). Idempotente por case_id (AlreadyMinted). Expõe `count_badges_by_user` para DAO. | OWNER · PAUSER · MINTER | ✅ SBT real (0 transfer). |
| 6 | `reputation-scoring-oracle` | [`reputation-scoring-oracle/src/lib.rs`](reputation-scoring-oracle/src/lib.rs) | **P1-B Oracle (off→on)**: Recebe scores de validadores off-chain autorizados (ROLE_SCORER), valida idempotência (AlreadyScored) e cross-contract mint SBT se score ≥50. | OWNER · PAUSER · SCORER | ✅ Fonte scores. |
| 7 | `payment-escrow-v1` | [`payment-escrow-v1/src/lib.rs`](payment-escrow-v1/src/lib.rs) | **P1-C Pagamento (XLM Only)**: Depósito por case_id (AlreadyPaid), base fee configurável. Release APENAS após cross-contract call `get_single_anchor` confirmar evidência ancorada (ROLE_WRITER). | OWNER · PAUSER · WRITER | ✅ Escrow atrelado à evidência. |
| 8 | `fee-distribution-multisig` | [`fee-distribution-multisig/src/lib.rs`](fee-distribution-multisig/src/lib.rs) | **P1-C Fee Split**: Lista de recipients + threshold multisig (m de n) para aprovar retiradas coletivas. Idempotência por recipient+withdrawal_id (AlreadyApproved). | OWNER · PAUSER · RECIPIENT | ✅ Multisig Fee. |
| 9 | `governance-voting-weight-calculator` | [`governance-voting-weight-calculator/src/lib.rs`](governance-voting-weight-calculator/src/lib.rs) | **P1-D DAO Helper**: Cross-contract call `count_badges_by_user` → CLAMP anti-Sybil 0..=MaxWeight (default=10). MinProposerWeight default=1. | OWNER · PAUSER · CONFIG | ✅ Anti-Sybil. |
| 10 | `governance-timelock-controller` | [`governance-timelock-controller/src/lib.rs`](governance-timelock-controller/src/lib.rs) | **P1-D DAO Delay Gate**: Delay padrão 48h (172800s). Guardian pode cancelar transações queueadas. Executor (ROLE_EXECUTOR) só libera após delay + não cancelado + não executado. Min delay=1h. | OWNER · PAUSER · EXECUTOR · GUARDIAN (cancel) | ✅ 48h + Veto Guardian. |
| 11 | `governance-governor-v1` | [`governance-governor-v1/src/lib.rs`](governance-governor-v1/src/lib.rs) | **P1-D DAO Core**: create_proposal (MinProposerWeight ≥ 1), cast_vote (support Against/For/Abstain), queue (MIN_QUORUM default=10, For>Against, end_ts passado). Cross-contract com WeightCalculator (peso voto) + Timelock (queue após aprovação). | OWNER · PAUSER · EXECUTOR | ✅ Governança On-Chain. |

## 🛡️ Segurança Fail-Closed Aplicada

1.  **CEI 100% em EvidenceAnchorV1**: `anchor_single/anchor_merkle_root` → Checks (role + paused + formato) → Effects (storage `persistent().set`) → Events (publish). Nenhuma cross-contract call no meio.
2.  **Custom Errors `repr(u32)` sem strings**: Economia de gas. `100=InvalidArgument`, `200=Paused`, `300=NotAuthorized`, `400=UpgradeFailed`, `500=InvalidMerkleProof`, `700=NotAnchored`.
3.  **Pause geral Emergência**: `pause()` / `unpause()` apenas papel `PAUSER` (recomendado threshold 2/3).
4.  **Upgrade Wasm apenas UPGRADER**: método `upgrade(new_wasm_hash)` apenas papel UPGRADER. Authority controlada por deployer.
5.  **0 métodos `transfer/deposit` de XLM/USDC**: Superfície de ataque de ativos = 0.
6.  **Registro idempotente**: `AlreadyAnchored(102)` se `case_id` ou `batch_id` já existir. Impede duplo âncora.
7.  **Merkle Proof off-chain**: `verify_merkle_proof` aceita leaf + Vec<sibling> + leaf_index, recomputa root e compara com BatchAnchoredRecord salvo. 0 dependências de ZK (simples, auditável).

## 🔌 Interface Pública (Contrato EvidenceAnchorV1)

### Escrita — papéis WRITER / PAUSER / UPGRADER apenas:
```rust
fn anchor_single(env, case_id: BytesN<32>, evidence_hash: BytesN<32>, salt: BytesN<16>) -> Result<()>;
fn anchor_merkle_root(env, batch_id: u64, merkle_root: BytesN<32>, count_leaves: u32, salt_batch: BytesN<16>) -> Result<()>;
fn pause(env) -> Result<()>;
fn unpause(env) -> Result<()>;
fn upgrade(env, new_wasm_hash: BytesN<32>) -> Result<()>;
fn grant_role(env, target: Address, role_mask: u32) -> Result<()>;
fn revoke_role(env, target: Address, role_mask: u32) -> Result<()>;
```

### Leitura — sem papel exigido (0 custo call view):
```rust
fn is_paused(env) -> bool;
fn has_role(env, target: Address, role_mask: u32) -> bool;
fn get_single_anchor(env, case_id: BytesN<32>) -> Result<SingleAnchoredRecord>;
fn get_batch_anchor(env, batch_id: u64) -> Result<BatchAnchoredRecord>;
fn verify_single(env, case_id, alleged_hash, alleged_salt) -> Result<bool>;
fn verify_merkle_proof(env, batch_id, leaf_hash, proof: Vec<BytesN<32>>, leaf_index: u32) -> Result<bool>;
```

## 🏗️ Build & Deploy (Só para referência — não rodar em prod sem auditorias)

### Pré-requisitos (Futurenet / Sandbox)
```bash
# 1. Instalar soroban-cli 22.x (compatível SDK 22)
cargo install --locked soroban-cli --version 22.0.0

# 2. Configurar rede Futurenet (placeholders HC-2)
cat > .env-futurenet.example <<'EOF'
STELLAR_NETWORK=Futurenet
STELLAR_RPC_URL=https://rpc-futurenet.stellar.org:443
STELLAR_NETWORK_PASSPHRASE=Test SDF Future Network ; October 2022
DEPLOYER_SECRET_KEY=S_____REPLACE_ME_____HC2_NEVER_COMMIT_TRUE_SECRET_____
EOF
cp .env-futurenet.example .env-futurenet
```

### Build Wasm otimizado (profile.release LTO = opt-level=z, 11 crates):
```bash
cd contracts
cargo build --target wasm32-unknown-unknown --release \
    -p evidence-anchor-v1 \
    -p access-control-multisig \
    -p eternal-storage \
    -p protocol-address-book \
    -p reputation-sbt-badge \
    -p reputation-scoring-oracle \
    -p payment-escrow-v1 \
    -p fee-distribution-multisig \
    -p governance-voting-weight-calculator \
    -p governance-timelock-controller \
    -p governance-governor-v1
ls -lhS target/wasm32-unknown-unknown/release/*.wasm   # ordena por tamanho; cada um < 512KB
```

### Deploy em 11 passos (ordem CRÍTICA de dependências bottom-up):
```bash
# FASE 0 — Eternal Storage + Core Ancora (P1-A)
# 1. Eternal Storage         — preserva hashes por upgrades de lógica
soroban contract deploy --wasm .../eternal_storage.wasm --source ...
# 2. Access Control Multisig — papéis OWNER/UPGRADER/PAUSER/WRITER
soroban contract deploy --wasm .../access_control_multisig.wasm --source ...
# 3. Evidence Anchor V1      — lógica ancora hash/merkle (depende de #1 #2)
soroban contract deploy --wasm .../evidence_anchor_v1.wasm --source ...

# FASE 1 — Registry (Protocol Address Book — liga tudo)
# 4. ProtocolAddressBook     — SLOT_1..10 (cria primeiro antes dos outros P1-B/C/D)
soroban contract deploy --wasm .../protocol_address_book.wasm --source ...

# FASE 2 — P1-B Reputação
# 5. Reputation SBT Badge    — non-transfer mint_for_case (depende só de si)
soroban contract deploy --wasm .../reputation_sbt_badge.wasm --source ...
# 6. Reputation Scoring Oracle — ROLE_SCORER cross-contract mint (depende #5)
soroban contract deploy --wasm .../reputation_scoring_oracle.wasm --source ...

# FASE 3 — P1-C Pagamento
# 7. Fee Distribution Multisig — recipients + threshold (independe)
soroban contract deploy --wasm .../fee_distribution_multisig.wasm --source ...
# 8. Payment Escrow V1       — depende #3 (anchor check) + #7 (fee destino)
soroban contract deploy --wasm .../payment_escrow_v1.wasm --source ...

# FASE 4 — P1-D DAO (3 crates)
# 9. Voting Weight Calculator — depende #5 (count_badges_by_user)
soroban contract deploy --wasm .../governance_voting_weight_calculator.wasm --source ...
# 10. Timelock Controller    — 48h delay, guardian veto (independe de #9 #11)
soroban contract deploy --wasm .../governance_timelock_controller.wasm --source ...
# 11. Governance Governor V1 — cross-contract depende #9 + #10
soroban contract deploy --wasm .../governance_governor_v1.wasm --source ...

# FASE 5 — Config Post-Deploy ONE SHOT (ordem também crítica):
#   a) EternalStorage.whitelist_logic(evidence_anchor_addr)
#   b) EvidenceAnchor.grant_role(writer_instance_A, WRITER)
#   c) ProtocolAddressBook.set_address(SLOT_1..10, respectivos endereços)
#   d) ReputationScoringOracle.set_sbt_contract(sbt_addr)
#   e) PaymentEscrow.set_[evidence, fee_distributor]_contract
#   f) VotingWeightCalculator.set_sbt_contract(sbt_addr)
#   g) GovernanceGovernor.__constructor(wc_addr, timelock_addr, 259200, 10, 1)
#   h) GovernanceTimelock.__constructor(owner, guardian_addr, 172800)
#   i) Grant papéis SCORER/MINTER/WRITER/CONFIG/EXECUTOR nos endereços corretos
```

## 🗃️ PostgreSQL Migration Complementar (já criado 0010)

Arquivo: [ontrackchain/infra/postgres/migrations/0010_evidence_soroban_meta.sql](../ontrackchain/infra/postgres/migrations/0010_evidence_soroban_meta.sql)

Colunas novas em `evidence_trail`:
- `soroban_contract_address VARCHAR(56) NULL` (endereço contrato EvidenceAnchor)
- `soroban_merkle_batch_id BIGINT NULL` (NULL se ancoração individual)
- `soroban_salt_environment BYTEA NOT NULL DEFAULT gen_random_bytes(16)` (LGPD — salta antes de hash publicar)

## 🧪 Cobertura Mínima Obrigatória (Antes de Deploy Mainnet · 11 crates · Sprint S28+74 backlog P1)

| # | Caminho | Casos de teste obrigatórios |
|---|---|---|
| 1 | `evidence-anchor-v1/src/test.rs` | (1) anchor_single OK / NotAuthorized / AlreadyAnchored · (2) Pause/Unpause ⇒ pausado bloqueia anchor · (3) upgrade só UPGRADER · (4) verify_merkle_proof válido / folha errada / sibling errado → false · (5) eventos publicados. |
| 2 | `access-control-multisig/src/test.rs` | grant/revoke OWNER only · threshold ≥ 1 e ≤ recipients.len · pausa bloqueia operações. |
| 3 | `eternal-storage/src/test.rs` | whitelist_logic só ADMIN · store só por whitelisted (erro 700 caso contrário) · load público 0 papel exigido. |
| 4 | `protocol-address-book/src/test.rs` | slot=0 retorna InvalidArgument · set_address só CONFIG|OWNER · slot 1..10 set/get OK · pausa bloqueia escrita. |
| 5 | `reputation-sbt-badge/src/test.rs` | mint_for_case: score<50 Invalid · 50≤s<75 Bronze · 75≤s<90 Prata · s≥90 Ouro · AlreadyMinted duplo bloqueado · count_badges_by_user soma correta · grant_role só OWNER. |
| 6 | `reputation-scoring-oracle/src/test.rs` | set_score score>100 Invalid · AlreadyScored duplo bloqueia · score≥50 invoke_contract mint_for_case chamado (SBT configurado) · set_sbt_contract só OWNER · pausa bloqueia escrita. |
| 7 | `payment-escrow-v1/src/test.rs` | deposit_for_case amount≤0 Invalid · AlreadyPaid duplo bloqueado · release_after_anchor: sem anchor → EvidenceNotAnchored · só WRITER libera · AlreadyReleased bloqueia segundo release · base_fee_stroops>0 validado. |
| 8 | `fee-distribution-multisig/src/test.rs` | constructor recipients vazio erro · threshold 0 ou > len → InvalidThreshold · approve_withdrawal: não-recipient → NotRecipient · AlreadyApproved duplo bloqueado · threshold_set só OWNER. |
| 9 | `governance-voting-weight-calculator/src/test.rs` | compute_weight clamp 0..MaxWeight exato (ex: 11 badges → 10) · SBT não configurado → SbtNotConfigured · set_max_weight 0 ou >100 Invalid · set_sbt_contract só CONFIG|OWNER. |
| 10 | `governance-timelock-controller/src/test.rs` | queue_transaction: targets.len != calldatas → Invalid · AlreadyQueued duplo bloqueado · cancel_transaction: só Guardian · execute antes do delay → NotReady · já cancelado → AlreadyCancelled · delay mínimo <3600s no set_delay → Invalid. |
| 11 | `governance-governor-v1/src/test.rs` | create_proposal: targets vazio / mismatch len → Invalid · MinProposerWeight<limite → WeightTooLowProposer · cast_vote: fora start/end_ts → NotActive · suporte>2 → Invalid · AlreadyVoted duplo bloqueado · queue: For≤Against → ProposalRejected · quorum<limite → FinishedNoQuorum · end_ts não passado → NotActive · vote duração min ≤600s clamp. |

## 🚩 Defaults Aplicados em S28+73 (G1..G6 — Escolhas Arquiteturais Confirmadas)

| G | Default Aplicado | Por quê (trade-off) |
|---|---|---|
| **G1** | **3 níveis badge**: Bronze (≥50) · Prata (≥75) · Ouro (≥90) | Simplicidade auditável. Trade-off: sem granularidade Platinum/Diamond (fica para upgrade V2). |
| **G2** | **XLM nativo APENAS em PaymentEscrow** (0 USDC/Stable) | Minimiza superfície ataque fundos no MVP. Trade-off: sem stablecoin → volatilidade. Requer upgrade para stable em auditoria P2. |
| **G3** | **1 SBT = 1 voto CLAMP 0..10 max anti-Sybil** | Defesa em profundidade: badge sem transfer + clamp máximo = ataque Sybil caro. Trade-off: whales limitados a 10 votos máx (propósito). |
| **G4** | **ZK PULADO nesta sprint** (só Merkle Proof off-chain simples) | MVP não precisa de ZK — complexidade proibitiva vs benefício. Pós-MVP sprint S28+100+ se provar necessidade. |
| **G5** | **Peso badge NÃO cria token novo** (não há token de governança ERC20/SEP-41) | Menos um contrato auditável. Sem launchpump/speculação. Trade-off: sem liquidez para votantes (intencional). |
| **G6** | **0 alteração apps/src/** (HC-4). Sprints S28+73 tocam apenas `contracts/`. | Mantém SIGNOFF-M5 intacto e 0 regressão 850+ testes. Trade-off: integração Python fica para sprint separada (S28+74 se necessário). |

## 🏗️ Não Implementado Ainda (Próximas Fases — pós 2 auditorias externas)

- 🔜 **Token de Governança (SEP-41)**: só após quorum DAO ≥ 100 endereços únicos.
- 🔜 **USDC/Stables em PaymentEscrow (SAC)**: requer 2 auditorias + integração Stellar Asset Contract (SAC).
- 🔜 **ZK Proofs (ZK-SNARK/ZK-STARK)**: reputação PEP/sanções privadas (LGPD Art. 37). Requer crate `bellman` ou `halo2`.
- 🔜 **Arbitrum/Optimism/Solana L2 bridge**: âncora cross-chain se Stellar congestionar (LayerZero/Axelar).
- 🔜 **Unit Tests Fuzzing Echidna + Slither 85%+ cobertura 11 crates**: Sprint S28+74 (backlog P1 imediato).
- 🔜 **CI Soroban `.github/workflows/contracts-ci.yml` (Ruff + cargo test + wasm size gate < 512KB)**: mover do diretório templates para workflows raiz em sprint separado (HC-3). |

## 🔗 Referências Tier1 (Arquitetura)

- Comentário roadmap L10-L11: [evidence_trail.py](../../ontrackchain/packages/agents/src/ontrackchain_agents/evidence_trail.py#L10-L11)
- Diagrama arquitetura geral + ADRs 001-029: [ontrackchain/docs/architecture.md](../../ontrackchain/docs/architecture.md)
- Tabela 8 Gates G1-G8 validações fail-closed: [TECHNICAL_APPENDIX.md](../../ontrackchain/docs/TECHNICAL_APPENDIX.md)
- Ciclo 6 passos canônicos sprint: [EXECUTION_CHECKLIST_TO_95_PERCENT.md](../../ontrackchain/docs/EXECUTION_CHECKLIST_TO_95_PERCENT.md)
