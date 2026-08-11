#![no_std]
use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, Env, Symbol, Vec,
};

#[contract]
pub struct FeeDistributionMultisig;

#[contracttype]
#[derive(Clone, PartialEq, Eq)]
pub enum StorageKey {
    Owner,
    Paused,
    RoleMask,
    Threshold,
    Recipients,
    Approved(Address, u64),
    WithdrawalId,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum FdError {
    Internal = 0,
    InvalidArgument = 100,
    InvalidThreshold = 101,
    AlreadyApproved = 102,
    Paused = 200,
    NotAuthorized = 300,
    RoleOwnerRequired = 301,
    NotRecipient = 305,
    ThresholdNotMet = 401,
    NoRecipients = 600,
}

pub const ROLE_OWNER: u32 = 1 << 0;
pub const ROLE_PAUSER: u32 = 1 << 1;
pub const ROLE_RECIPIENT: u32 = 1 << 2;

fn require_role(env: &Env, _who: &Address, mask: u32) -> Result<(), FdError> {
    let current: u32 = env
        .storage()
        .instance()
        .get(&StorageKey::RoleMask)
        .unwrap_or(0);
    if current & mask != mask {
        return Err(match mask {
            ROLE_OWNER => FdError::RoleOwnerRequired,
            ROLE_RECIPIENT => FdError::NotRecipient,
            _ => FdError::NotAuthorized,
        });
    }
    Ok(())
}

fn require_not_paused(env: &Env) -> Result<(), FdError> {
    if env.storage().instance().get(&StorageKey::Paused).unwrap_or(false) {
        Err(FdError::Paused)
    } else {
        Ok(())
    }
}

#[contracttype]
#[derive(Clone)]
pub struct WithdrawalRecord {
    pub id: u64,
    pub amount_each: i128,
    pub asset_native: bool,
    pub created_at_ledger: u64,
    pub approvals: u32,
    pub executed: bool,
}

#[contractimpl]
impl FeeDistributionMultisig {
    pub fn __constructor(
        env: Env,
        owner: Address,
        recipients: Vec<Address>,
        threshold: u32,
    ) -> Result<(), FdError> {
        if recipients.is_empty() {
            return Err(FdError::NoRecipients);
        }
        if threshold == 0 || threshold > recipients.len() {
            return Err(FdError::InvalidThreshold);
        }
        env.storage().instance().set(&StorageKey::Owner, &owner);
        env.storage()
            .instance()
            .set(&StorageKey::RoleMask, &(ROLE_OWNER | ROLE_PAUSER | ROLE_RECIPIENT));
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.storage().instance().set(&StorageKey::Threshold, &threshold);
        env.storage().instance().set(&StorageKey::Recipients, &recipients);
        env.storage().instance().set(&StorageKey::WithdrawalId, &1u64);
        Ok(())
    }

    pub fn pause(env: Env, from: Address) -> Result<(), FdError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &true);
        env.events().publish((Symbol::new(&env, "paused"),), (from,));
        Ok(())
    }

    pub fn unpause(env: Env, from: Address) -> Result<(), FdError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.events()
            .publish((Symbol::new(&env, "unpaused"),), (from,));
        Ok(())
    }

    pub fn set_threshold(env: Env, from: Address, threshold: u32) -> Result<(), FdError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_OWNER)?;
        let recipients: Vec<Address> = env
            .storage()
            .instance()
            .get(&StorageKey::Recipients)
            .unwrap_or(Vec::new(&env));
        if threshold == 0 || threshold > recipients.len() {
            return Err(FdError::InvalidThreshold);
        }
        env.storage().instance().set(&StorageKey::Threshold, &threshold);
        env.events().publish(
            (Symbol::new(&env, "threshold_set"),),
            (from, threshold),
        );
        Ok(())
    }

    pub fn is_recipient(env: Env, who: Address) -> bool {
        let recipients: Vec<Address> = env
            .storage()
            .instance()
            .get(&StorageKey::Recipients)
            .unwrap_or(Vec::new(&env));
        recipients.contains(&who)
    }

    pub fn approve_withdrawal(
        env: Env,
        from: Address,
        withdrawal_id: u64,
    ) -> Result<u32, FdError> {
        from.require_auth();
        require_not_paused(&env)?;
        if !Self::is_recipient(env.clone(), from.clone()) {
            return Err(FdError::NotRecipient);
        }
        let key = StorageKey::Approved(from.clone(), withdrawal_id);
        if env.storage().persistent().has(&key) {
            return Err(FdError::AlreadyApproved);
        }
        env.storage().persistent().set(&key, &true);
        let threshold: u32 = env
            .storage()
            .instance()
            .get(&StorageKey::Threshold)
            .unwrap_or(1);
        let recipients: Vec<Address> = env
            .storage()
            .instance()
            .get(&StorageKey::Recipients)
            .unwrap_or(Vec::new(&env));
        let mut approvals = 0u32;
        for r in recipients.iter() {
            let k = StorageKey::Approved(r, withdrawal_id);
            if env.storage().persistent().has(&k) {
                approvals += 1;
            }
        }
        env.events().publish(
            (Symbol::new(&env, "withdrawal_approved"),),
            (from, withdrawal_id, approvals, threshold),
        );
        Ok(approvals)
    }
}
