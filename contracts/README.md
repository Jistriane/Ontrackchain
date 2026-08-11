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

## 📦 Crates do Workspace

| Crate | Caminho | Responsabilidade Única | `#[contract]` |
|---|---|---|---|
| `evidence-anchor-v1` | [`evidence-anchor-v1/src/lib.rs`](evidence-anchor-v1/src/lib.rs) | **CORE**: Âncora de hashes individuais + raízes Merkle. Access control RBAC, Pausable, Upgradeable. Verificação off-chain Merkle proof. | ✅ Principal. |
| `access-control-multisig` | [`access-control-multisig/src/lib.rs`](access-control-multisig/src/lib.rs) | Papéis (OWNER / UPGRADER / PAUSER / WRITER) + threshold por papel (ex: 2/3 multisig para UPGRADER/PAUSER). | ✅ Separado de lógica. |
| `eternal-storage` | [`eternal-storage/src/lib.rs`](eternal-storage/src/lib.rs) | Armazenamento append-only KV separado de lógica. Preserva hashes mesmo que EvidenceAnchorV1 → V2 upgrade. Escreve APENAS por address whitelistado (EvidenceAnchor*). | ✅ Whitelist de lógicas. |

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

### Build Wasm otimizado (profile.release LTO = opt-level=z):
```bash
cd contracts
cargo build --target wasm32-unknown-unknown --release -p evidence-anchor-v1 \
                            -p access-control-multisig \
                            -p eternal-storage
ls -la target/wasm32-unknown-unknown/release/*.wasm
```

### Deploy em 3 passos (ordem crítica: ES → AC → Anchor):
```bash
# 1. Eternal Storage (dados)
soroban contract deploy --wasm target/wasm32-unknown-unknown/release/eternal_stadium.wasm --source-account $DEPLOYER_SECRET_KEY
# 2. Access Control Multisig (roles + threshold)
soroban contract deploy --wasm .../access_control_multisig.wasm --source ...
# 3. Evidence Anchor V1 (lógica)
soroban contract deploy --wasm .../evidence_anchor_v1.wasm --source ...
# 4. Config ONE SHOT post deploy:
#   a) EternalStorage.whitelist_logic(anchor_address)
#   b) Anchor.grant_role(writer_backend_instance_A, WRITER=8)
#   c) Anchor.set_role_threshold(UPGRADER=2, threshold=2/3 multisig)
```

## 🗃️ PostgreSQL Migration Complementar (já criado 0010)

Arquivo: [ontrackchain/infra/postgres/migrations/0010_evidence_soroban_meta.sql](../ontrackchain/infra/postgres/migrations/0010_evidence_soroban_meta.sql)

Colunas novas em `evidence_trail`:
- `soroban_contract_address VARCHAR(56) NULL` (endereço contrato EvidenceAnchor)
- `soroban_merkle_batch_id BIGINT NULL` (NULL se ancoração individual)
- `soroban_salt_environment BYTEA NOT NULL DEFAULT gen_random_bytes(16)` (LGPD — salta antes de hash publicar)

## 🧪 Cobertura Mínima Obrigatória (Antes de Deploy Mainnet)

| Caminho | O que cobrir |
|---|---|
| `evidence-anchor-v1/tests/` | (1) anchor_single OK / NotAuthorized / AlreadyAnchored · (2) Pause/Unpause ⇒ pausado blocka anchor · (3) upgrade só UPGRADER · (4) verify_merkle_proof: válido / folha errada / sibling errado → false · (5) eventos publicados. |
| `access-control-multisig/tests/` | grant/revoke OWNER only · threshold ≥ 1. |
| `eternal-storage/tests/` | whitelist_logic só ADMIN · store só whitelisted · load público. |

## 🚩 Não Implementado Ainda (P1-B / P1-C Não Aprovados Ainda)

Escopo creep bloqueado no design (apenas P1-A aprovado default):
- ❌ Reputação on-chain de endereços / PEP público → Risco LGPD Art. 37. Requer ZKP.
- ❌ Pagamento SAC USDC on-chain por relatório → Superfície ataque fundos. Requer 2 auditorias externas obrigatórias.
- ❌ Governança DAO / token de governança → Fase 5 2028+.

## 🔗 Referências Tier1 (Arquitetura)

- Comentário roadmap L10-L11: [evidence_trail.py](../../ontrackchain/packages/agents/src/ontrackchain_agents/evidence_trail.py#L10-L11)
- Diagrama arquitetura geral + ADRs 001-029: [ontrackchain/docs/architecture.md](../../ontrackchain/docs/architecture.md)
- Tabela 8 Gates G1-G8 validações fail-closed: [TECHNICAL_APPENDIX.md](../../ontrackchain/docs/TECHNICAL_APPENDIX.md)
- Ciclo 6 passos canônicos sprint: [EXECUTION_CHECKLIST_TO_95_PERCENT.md](../../ontrackchain/docs/EXECUTION_CHECKLIST_TO_95_PERCENT.md)
