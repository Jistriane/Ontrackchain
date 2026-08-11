#![no_std]
use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, Bytes, BytesN, Env, Symbol, Vec,
    Val, TryFromVal, IntoVal,
};

#[contract]
pub struct GovernanceTimelockController;

#[contracttype]
#[derive(Clone, PartialEq, Eq)]
pub enum StorageKey {
    Owner,
    Paused,
    RoleMask,
    Guardian,
    DelaySeconds,
    TxRecord(BytesN<32>),
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum TlError {
    Internal = 0,
    InvalidArgument = 100,
    AlreadyQueued = 102,
    Paused = 200,
    NotAuthorized = 300,
    RoleOwnerRequired = 301,
    RoleExecutorRequired = 304,
    NotGuardian = 306,
    NotQueued = 400,
    NotReady = 402,
    AlreadyCancelled = 403,
    AlreadyExecuted = 404,
}

pub const ROLE_OWNER: u32 = 1 << 0;
pub const ROLE_PAUSER: u32 = 1 << 1;
pub const ROLE_EXECUTOR: u32 = 1 << 2;
pub const DEFAULT_DELAY_SECONDS: u64 = 172_800;

#[contracttype]
#[derive(Clone)]
pub struct TxQueued {
    pub queued_at_ledger_time: u64,
    pub delay_seconds: u64,
    pub cancelled: bool,
    pub executed: bool,
    pub targets: Vec<Address>,
    pub calldatas: Vec<Bytes>,
    pub values: Vec<i128>,
}

fn require_role(env: &Env, _who: &Address, mask: u32) -> Result<(), TlError> {
    let current: u32 = env
        .storage()
        .instance()
        .get(&StorageKey::RoleMask)
        .unwrap_or(0);
    if current & mask != mask {
        return Err(match mask {
            ROLE_OWNER => TlError::RoleOwnerRequired,
            ROLE_EXECUTOR => TlError::RoleExecutorRequired,
            _ => TlError::NotAuthorized,
        });
    }
    Ok(())
}

fn require_not_paused(env: &Env) -> Result<(), TlError> {
    if env.storage().instance().get(&StorageKey::Paused).unwrap_or(false) {
        Err(TlError::Paused)
    } else {
        Ok(())
    }
}

fn hash_tx(
    env: &Env,
    nonce: u64,
    targets: &Vec<Address>,
    calldatas: &Vec<Bytes>,
    values: &Vec<i128>,
) -> BytesN<32> {
    let mut buf = [0u8; 8 + 8];
    buf[0..8].copy_from_slice(&nonce.to_le_bytes());
    let parts_len = (targets.len() as u64).to_le_bytes();
    buf[8..16].copy_from_slice(&parts_len);
    let mut combined = Bytes::from_array(env, &buf);
    for (i, t) in targets.iter().enumerate() {
        let t_val = t.into_val(env);
        let t_bytes = <Bytes as TryFromVal<Env, Val>>::try_from_val(env, &t_val)
            .unwrap_or(Bytes::new(env));
        combined.append(&t_bytes);
        let cd_b = calldatas.get(i as u32).unwrap_or(Bytes::new(env));
        combined.append(&cd_b);
        let v_bytes = (values.get(i as u32).unwrap_or(0)).to_le_bytes();
        combined.append(&Bytes::from_array(env, &v_bytes));
    }
    env.crypto().sha256(&combined).into()
}

#[contractimpl]
impl GovernanceTimelockController {
    pub fn __constructor(env: Env, owner: Address, guardian: Address, delay_seconds: u64) {
        env.storage().instance().set(&StorageKey::Owner, &owner);
        env.storage()
            .instance()
            .set(&StorageKey::RoleMask, &(ROLE_OWNER | ROLE_PAUSER | ROLE_EXECUTOR));
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.storage().instance().set(&StorageKey::Guardian, &guardian);
        env.storage()
            .instance()
            .set(&StorageKey::DelaySeconds, &delay_seconds.max(1));
    }

    pub fn pause(env: Env, from: Address) -> Result<(), TlError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &true);
        env.events().publish((Symbol::new(&env, "paused"),), (from,));
        Ok(())
    }

    pub fn unpause(env: Env, from: Address) -> Result<(), TlError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.events()
            .publish((Symbol::new(&env, "unpaused"),), (from,));
        Ok(())
    }

    pub fn set_delay(
        env: Env,
        from: Address,
        delay_seconds: u64,
    ) -> Result<(), TlError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_OWNER)?;
        if delay_seconds < 3_600 {
            return Err(TlError::InvalidArgument);
        }
        env.storage()
            .instance()
            .set(&StorageKey::DelaySeconds, &delay_seconds);
        env.events().publish(
            (Symbol::new(&env, "delay_set"),),
            (from, delay_seconds),
        );
        Ok(())
    }

    pub fn queue_transaction(
        env: Env,
        from: Address,
        nonce: u64,
        targets: Vec<Address>,
        calldatas: Vec<Bytes>,
        values: Vec<i128>,
    ) -> Result<BytesN<32>, TlError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_EXECUTOR)?;
        if targets.len() != calldatas.len() || targets.len() != values.len() || targets.is_empty() {
            return Err(TlError::InvalidArgument);
        }
        let id = hash_tx(&env, nonce, &targets, &calldatas, &values);
        let key = StorageKey::TxRecord(id.clone());
        if let Some(rec) = env.storage().persistent().get::<StorageKey, TxQueued>(&key) {
            if rec.cancelled || rec.executed {
                return Err(TlError::InvalidArgument);
            }
            return Err(TlError::AlreadyQueued);
        }
        let delay: u64 = env
            .storage()
            .instance()
            .get(&StorageKey::DelaySeconds)
            .unwrap_or(DEFAULT_DELAY_SECONDS);
        let rec = TxQueued {
            queued_at_ledger_time: env.ledger().timestamp(),
            delay_seconds: delay,
            cancelled: false,
            executed: false,
            targets: targets.clone(),
            calldatas: calldatas.clone(),
            values: values.clone(),
        };
        env.storage().persistent().set(&key, &rec);
        env.events().publish(
            (Symbol::new(&env, "tx_queued"),),
            (from, id.clone(), delay),
        );
        Ok(id)
    }

    pub fn cancel_transaction(
        env: Env,
        from: Address,
        tx_id: BytesN<32>,
    ) -> Result<(), TlError> {
        from.require_auth();
        let guardian: Address = env
            .storage()
            .instance()
            .get(&StorageKey::Guardian)
            .ok_or(TlError::NotGuardian)?;
        if from != guardian {
            return Err(TlError::NotGuardian);
        }
        let key = StorageKey::TxRecord(tx_id.clone());
        let mut rec: TxQueued = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(TlError::NotQueued)?;
        if rec.cancelled {
            return Err(TlError::AlreadyCancelled);
        }
        if rec.executed {
            return Err(TlError::AlreadyExecuted);
        }
        rec.cancelled = true;
        env.storage().persistent().set(&key, &rec);
        env.events().publish(
            (Symbol::new(&env, "tx_cancelled"),),
            (from, tx_id),
        );
        Ok(())
    }

    pub fn execute_transaction(
        env: Env,
        from: Address,
        tx_id: BytesN<32>,
    ) -> Result<(), TlError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_EXECUTOR)?;
        let key = StorageKey::TxRecord(tx_id.clone());
        let mut rec: TxQueued = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(TlError::NotQueued)?;
        if rec.cancelled {
            return Err(TlError::AlreadyCancelled);
        }
        if rec.executed {
            return Err(TlError::AlreadyExecuted);
        }
        let now = env.ledger().timestamp();
        if now < rec.queued_at_ledger_time.saturating_add(rec.delay_seconds) {
            return Err(TlError::NotReady);
        }
        rec.executed = true;
        env.storage().persistent().set(&key, &rec);
        env.events().publish(
            (Symbol::new(&env, "tx_executed"),),
            (from, tx_id, rec.targets.len() as u32),
        );
        Ok(())
    }

    pub fn get_tx(env: Env, tx_id: BytesN<32>) -> Option<TxQueued> {
        env.storage()
            .persistent()
            .get(&StorageKey::TxRecord(tx_id))
    }
}
