#![no_std]

use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, Env, Symbol,
};

pub const ROLE_OWNER: u32 = 1;
pub const ROLE_UPGRADER: u32 = 2;
pub const ROLE_PAUSER: u32 = 4;
pub const ROLE_WRITER: u32 = 8;

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ACKey {
    Admin,
    Role(Address, u32),
    Threshold(u32),
}

#[contracterror]
#[repr(u32)]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
pub enum ACError {
    NotAuthorized = 300,
    InvalidThreshold = 100,
}

#[contract]
pub struct AccessControlMultisig;

#[contractimpl]
impl AccessControlMultisig {
    pub fn __constructor(env: Env, owner: Address, threshold_writers: u32) {
        owner.require_auth();
        if threshold_writers < 1 {
            panic!("invalid threshold");
        }
        env.storage()
            .instance()
            .set(&ACKey::Admin, &owner);
        Self::set_role(&env, &owner, ROLE_OWNER, true);
        env.storage()
            .instance()
            .set(&ACKey::Threshold(ROLE_WRITER), &threshold_writers);
    }

    pub fn grant(
        env: Env,
        from: Address,
        target: Address,
        role_mask: u32,
    ) -> Result<(), ACError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_OWNER)?;
        Self::set_role(&env, &target, role_mask, true);
        env.events().publish(
            (Symbol::new(&env, "grant"),),
            (from, target, role_mask),
        );
        Ok(())
    }

    pub fn revoke(
        env: Env,
        from: Address,
        target: Address,
        role_mask: u32,
    ) -> Result<(), ACError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_OWNER)?;
        Self::set_role(&env, &target, role_mask, false);
        env.events().publish(
            (Symbol::new(&env, "revoke"),),
            (from, target, role_mask),
        );
        Ok(())
    }

    pub fn has(env: Env, target: Address, role_mask: u32) -> bool {
        let k = ACKey::Role(target, role_mask);
        env.storage()
            .persistent()
            .get::<_, bool>(&k)
            .unwrap_or(false)
    }

    pub fn set_threshold(
        env: Env,
        from: Address,
        role_mask: u32,
        threshold: u32,
    ) -> Result<(), ACError> {
        from.require_auth();
        Self::require_role(&env, &from, ROLE_OWNER)?;
        if threshold == 0 {
            return Err(ACError::InvalidThreshold);
        }
        env.storage()
            .instance()
            .set(&ACKey::Threshold(role_mask), &threshold);
        Ok(())
    }
}

impl AccessControlMultisig {
    fn require_role(env: &Env, who: &Address, role_mask: u32) -> Result<(), ACError> {
        if Self::has(env.clone(), who.clone(), role_mask) {
            Ok(())
        } else {
            Err(ACError::NotAuthorized)
        }
    }

    fn set_role(env: &Env, target: &Address, role_mask: u32, granted: bool) {
        let k = ACKey::Role(target.clone(), role_mask);
        if granted {
            env.storage().persistent().set(&k, &true);
        } else {
            env.storage().persistent().remove(&k);
        }
    }
}
