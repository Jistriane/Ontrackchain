#![no_std]
use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, Env, Symbol,
};

#[contract]
pub struct ProtocolAddressBook;

#[contracttype]
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum StorageKey {
    Owner,
    Paused,
    RoleMask,
    Slot(u32),
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum PabError {
    Internal = 0,
    InvalidArgument = 100,
    Paused = 200,
    NotAuthorized = 300,
    RoleOwnerRequired = 301,
    RoleNotSet = 600,
    SlotNotConfigured = 700,
}

pub const ROLE_OWNER: u32 = 1 << 0;
pub const ROLE_PAUSER: u32 = 1 << 1;
pub const ROLE_CONFIG: u32 = 1 << 2;

pub const SLOT_EVIDENCE_ANCHOR: u32 = 1;
pub const SLOT_ACCESS_CONTROL: u32 = 2;
pub const SLOT_ETERNAL_STORAGE: u32 = 3;
pub const SLOT_REPUTATION_SBT: u32 = 4;
pub const SLOT_SCORING_ORACLE: u32 = 5;
pub const SLOT_PAYMENT_ESCROW: u32 = 6;
pub const SLOT_FEE_DISTRIBUTOR: u32 = 7;
pub const SLOT_GOVERNOR: u32 = 8;
pub const SLOT_TIMELOCK: u32 = 9;
pub const SLOT_WEIGHT_CALC: u32 = 10;

fn require_role(env: &Env, _who: &Address, mask: u32) -> Result<(), PabError> {
    let current: u32 = env
        .storage()
        .instance()
        .get(&StorageKey::RoleMask)
        .unwrap_or(0);
    if current & mask != mask {
        return Err(match mask {
            ROLE_OWNER => PabError::RoleOwnerRequired,
            _ => PabError::NotAuthorized,
        });
    }
    Ok(())
}

fn require_not_paused(env: &Env) -> Result<(), PabError> {
    if env.storage().instance().get(&StorageKey::Paused).unwrap_or(false) {
        Err(PabError::Paused)
    } else {
        Ok(())
    }
}

#[contractimpl]
impl ProtocolAddressBook {
    pub fn __constructor(env: Env, owner: Address) {
        env.storage().instance().set(&StorageKey::Owner, &owner);
        env.storage()
            .instance()
            .set(&StorageKey::RoleMask, &(ROLE_OWNER | ROLE_PAUSER | ROLE_CONFIG));
        env.storage().instance().set(&StorageKey::Paused, &false);
    }

    pub fn pause(env: Env, from: Address) -> Result<(), PabError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &true);
        env.events().publish((Symbol::new(&env, "paused"),), (from,));
        Ok(())
    }

    pub fn unpause(env: Env, from: Address) -> Result<(), PabError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.events()
            .publish((Symbol::new(&env, "unpaused"),), (from,));
        Ok(())
    }

    pub fn is_paused(env: Env) -> bool {
        env.storage().instance().get(&StorageKey::Paused).unwrap_or(false)
    }

    pub fn set_address(
        env: Env,
        from: Address,
        slot: u32,
        contract_address: Address,
    ) -> Result<(), PabError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_CONFIG | ROLE_OWNER)?;
        if slot == 0 {
            return Err(PabError::InvalidArgument);
        }
        env.storage()
            .persistent()
            .set(&StorageKey::Slot(slot), &contract_address);
        env.events().publish(
            (Symbol::new(&env, "address_set"),),
            (from, slot, contract_address),
        );
        Ok(())
    }

    pub fn get_address(env: Env, slot: u32) -> Result<Address, PabError> {
        if slot == 0 {
            return Err(PabError::InvalidArgument);
        }
        env.storage()
            .persistent()
            .get(&StorageKey::Slot(slot))
            .ok_or(PabError::SlotNotConfigured)
    }
}
