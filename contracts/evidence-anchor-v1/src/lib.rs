#![no_std]

use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, Bytes, BytesN, Env, Symbol,
    Vec,
};

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum StorageKey {
    Admin,
    Paused,
    Role(Address, u32),
    SingleAnchor(BytesN<32>),
    BatchAnchor(u64),
    EternalStorageAddress,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SingleAnchoredRecord {
    pub evidence_hash: BytesN<32>,
    pub salt: BytesN<16>,
    pub anchored_by: Address,
    pub anchored_at: u64,
    pub block_height: u32,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BatchAnchoredRecord {
    pub merkle_root: BytesN<32>,
    pub count_leaves: u32,
    pub salt_batch: BytesN<16>,
    pub anchored_by: Address,
    pub anchored_at: u64,
    pub block_height: u32,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum EvidenceAnchorError {
    Internal = 0,
    InvalidArgument = 100,
    AlreadyAnchored = 102,
    Paused = 200,
    NotAuthorized = 300,
    RoleRequiredOwner = 301,
    RoleRequiredWriter = 302,
    RoleRequiredPauser = 303,
    RoleRequiredUpgrader = 304,
    UpgradeFailed = 400,
    InvalidMerkleProof = 500,
    EternalStorageNotConfigured = 600,
    NotAnchored = 700,
}

pub const ROLE_OWNER: u32 = 1;
pub const ROLE_UPGRADER: u32 = 2;
pub const ROLE_PAUSER: u32 = 4;
pub const ROLE_WRITER: u32 = 8;

#[contract]
pub struct EvidenceAnchorV1;

#[contractimpl]
impl EvidenceAnchorV1 {
    pub fn __constructor(env: Env, owner: Address) {
        owner.require_auth();
        env.storage()
            .instance()
            .set(&StorageKey::Admin, &owner);
        Self::set_role(&env, &owner, ROLE_OWNER, true);
        Self::set_role(&env, &owner, ROLE_WRITER, true);
        Self::set_role(&env, &owner, ROLE_PAUSER, true);
        Self::set_role(&env, &owner, ROLE_UPGRADER, true);
        env.storage().instance().set(&StorageKey::Paused, &false);
    }

    pub fn upgrade(
        env: Env,
        from: Address,
        new_wasm_hash: BytesN<32>,
    ) -> Result<(), EvidenceAnchorError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_UPGRADER)
            .map_err(|_| EvidenceAnchorError::RoleRequiredUpgrader)?;
        Self::require_not_paused(&env)?;

        env.deployer()
            .update_current_contract_wasm(new_wasm_hash.clone());

        env.events().publish(
            (Symbol::new(&env, "upgraded"),),
            (from.clone(), new_wasm_hash),
        );
        Ok(())
    }

    pub fn pause(env: Env, from: Address) -> Result<(), EvidenceAnchorError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_PAUSER)
            .map_err(|_| EvidenceAnchorError::RoleRequiredPauser)?;
        env.storage().instance().set(&StorageKey::Paused, &true);
        env.events()
            .publish((Symbol::new(&env, "paused"),), (from,));
        Ok(())
    }

    pub fn unpause(env: Env, from: Address) -> Result<(), EvidenceAnchorError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_PAUSER)
            .map_err(|_| EvidenceAnchorError::RoleRequiredPauser)?;
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.events()
            .publish((Symbol::new(&env, "unpaused"),), (from,));
        Ok(())
    }

    pub fn is_paused(env: Env) -> bool {
        env.storage()
            .instance()
            .get::<_, bool>(&StorageKey::Paused)
            .unwrap_or(false)
    }

    pub fn grant_role(
        env: Env,
        from: Address,
        target: Address,
        role_mask: u32,
    ) -> Result<(), EvidenceAnchorError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_OWNER)
            .map_err(|_| EvidenceAnchorError::RoleRequiredOwner)?;
        Self::require_not_paused(&env)?;
        Self::set_role(&env, &target, role_mask, true);
        env.events().publish(
            (Symbol::new(&env, "role_granted"),),
            (from, target, role_mask),
        );
        Ok(())
    }

    pub fn revoke_role(
        env: Env,
        from: Address,
        target: Address,
        role_mask: u32,
    ) -> Result<(), EvidenceAnchorError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_OWNER)
            .map_err(|_| EvidenceAnchorError::RoleRequiredOwner)?;
        Self::require_not_paused(&env)?;
        Self::set_role(&env, &target, role_mask, false);
        env.events().publish(
            (Symbol::new(&env, "role_revoked"),),
            (from, target, role_mask),
        );
        Ok(())
    }

    pub fn has_role(env: Env, target: Address, role_mask: u32) -> bool {
        let key = StorageKey::Role(target, role_mask);
        env.storage()
            .persistent()
            .get::<_, bool>(&key)
            .unwrap_or(false)
    }

    pub fn anchor_single(
        env: Env,
        from: Address,
        case_id: BytesN<32>,
        evidence_hash: BytesN<32>,
        salt: BytesN<16>,
    ) -> Result<(), EvidenceAnchorError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_WRITER)
            .map_err(|_| EvidenceAnchorError::RoleRequiredWriter)?;
        Self::require_not_paused(&env)?;

        let key = StorageKey::SingleAnchor(case_id.clone());
        if env.storage().persistent().has(&key) {
            return Err(EvidenceAnchorError::AlreadyAnchored);
        }

        let record = SingleAnchoredRecord {
            evidence_hash: evidence_hash.clone(),
            salt: salt.clone(),
            anchored_by: from.clone(),
            anchored_at: env.ledger().timestamp(),
            block_height: env.ledger().sequence(),
        };
        env.storage().persistent().set(&key, &record);

        env.events().publish(
            (Symbol::new(&env, "evidence_anchored"),),
            (
                0u32,
                case_id,
                evidence_hash,
                salt,
                from,
            ),
        );
        Ok(())
    }

    pub fn anchor_merkle_root(
        env: Env,
        from: Address,
        batch_id: u64,
        merkle_root: BytesN<32>,
        count_leaves: u32,
        salt_batch: BytesN<16>,
    ) -> Result<(), EvidenceAnchorError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_WRITER)
            .map_err(|_| EvidenceAnchorError::RoleRequiredWriter)?;
        Self::require_not_paused(&env)?;
        if count_leaves == 0 {
            return Err(EvidenceAnchorError::InvalidArgument);
        }

        let key = StorageKey::BatchAnchor(batch_id);
        if env.storage().persistent().has(&key) {
            return Err(EvidenceAnchorError::AlreadyAnchored);
        }

        let record = BatchAnchoredRecord {
            merkle_root: merkle_root.clone(),
            count_leaves,
            salt_batch: salt_batch.clone(),
            anchored_by: from.clone(),
            anchored_at: env.ledger().timestamp(),
            block_height: env.ledger().sequence(),
        };
        env.storage().persistent().set(&key, &record);

        env.events().publish(
            (Symbol::new(&env, "batch_anchored"),),
            (
                1u32,
                batch_id,
                merkle_root,
                count_leaves,
                salt_batch,
                from,
            ),
        );
        Ok(())
    }

    pub fn get_single_anchor(
        env: Env,
        case_id: BytesN<32>,
    ) -> Result<SingleAnchoredRecord, EvidenceAnchorError> {
        let key = StorageKey::SingleAnchor(case_id);
        env.storage()
            .persistent()
            .get::<_, SingleAnchoredRecord>(&key)
            .ok_or(EvidenceAnchorError::NotAnchored)
    }

    pub fn get_batch_anchor(
        env: Env,
        batch_id: u64,
    ) -> Result<BatchAnchoredRecord, EvidenceAnchorError> {
        let key = StorageKey::BatchAnchor(batch_id);
        env.storage()
            .persistent()
            .get::<_, BatchAnchoredRecord>(&key)
            .ok_or(EvidenceAnchorError::NotAnchored)
    }

    pub fn verify_single(
        env: Env,
        case_id: BytesN<32>,
        alleged_hash: BytesN<32>,
        alleged_salt: BytesN<16>,
    ) -> Result<bool, EvidenceAnchorError> {
        let stored = Self::get_single_anchor(env, case_id)?;
        Ok(stored.evidence_hash == alleged_hash && stored.salt == alleged_salt)
    }

    pub fn verify_merkle_proof(
        env: Env,
        batch_id: u64,
        leaf_hash: BytesN<32>,
        proof: Vec<BytesN<32>>,
        leaf_index: u32,
    ) -> Result<bool, EvidenceAnchorError> {
        let stored = Self::get_batch_anchor(env.clone(), batch_id)?;
        let mut computed = leaf_hash;
        let mut index = leaf_index;

        for sibling in proof.iter() {
            let (left, right) = if index & 1 == 0 {
                (computed.clone(), sibling.clone())
            } else {
                (sibling.clone(), computed.clone())
            };
            computed = hash_pair(&env, &left, &right);
            index >>= 1;
        }

        Ok(computed == stored.merkle_root)
    }
}

impl EvidenceAnchorV1 {
    fn require_not_paused(env: &Env) -> Result<(), EvidenceAnchorError> {
        if Self::is_paused(env.clone()) {
            Err(EvidenceAnchorError::Paused)
        } else {
            Ok(())
        }
    }

    fn require_role(env: &Env, who: &Address, role_mask: u32) -> Result<(), ()> {
        if Self::has_role(env.clone(), who.clone(), role_mask) {
            Ok(())
        } else {
            Err(())
        }
    }

    fn set_role(env: &Env, target: &Address, role_mask: u32, granted: bool) {
        let key = StorageKey::Role(target.clone(), role_mask);
        if granted {
            env.storage().persistent().set(&key, &true);
        } else {
            env.storage().persistent().remove(&key);
        }
    }
}

pub fn hash_pair(env: &Env, a: &BytesN<32>, b: &BytesN<32>) -> BytesN<32> {
    let a_bytes: [u8; 32] = a.into();
    let b_bytes: [u8; 32] = b.into();
    let mut buf = [0u8; 64];
    buf[0..32].copy_from_slice(&a_bytes);
    buf[32..64].copy_from_slice(&b_bytes);
    let combined: Bytes = Bytes::from_array(env, &buf);
    env.crypto().sha256(&combined).into()
}
