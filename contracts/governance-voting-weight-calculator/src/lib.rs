#![no_std]
use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, Env, Symbol, Val, IntoVal, Vec,
    TryFromVal,
};

#[contract]
pub struct GovernanceVotingWeightCalculator;

#[contracttype]
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum StorageKey {
    Owner,
    Paused,
    RoleMask,
    SbtContract,
    MaxWeight,
}
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum WeightError {
    Internal = 0,
    InvalidArgument = 100,
    Paused = 200,
    NotAuthorized = 300,
    RoleOwnerRequired = 301,
    SbtNotConfigured = 601,
}

pub const ROLE_OWNER: u32 = 1 << 0;
pub const ROLE_PAUSER: u32 = 1 << 1;
pub const ROLE_CONFIG: u32 = 1 << 2;
pub const DEFAULT_MAX_WEIGHT: u32 = 10;

fn require_role(env: &Env, _who: &Address, mask: u32) -> Result<(), WeightError> {
    let current: u32 = env
        .storage()
        .instance()
        .get(&StorageKey::RoleMask)
        .unwrap_or(0);
    if current & mask != mask {
        return Err(match mask {
            ROLE_OWNER => WeightError::RoleOwnerRequired,
            _ => WeightError::NotAuthorized,
        });
    }
    Ok(())
}

fn require_not_paused(env: &Env) -> Result<(), WeightError> {
    if env.storage().instance().get(&StorageKey::Paused).unwrap_or(false) {
        Err(WeightError::Paused)
    } else {
        Ok(())
    }
}

#[contractimpl]
impl GovernanceVotingWeightCalculator {
    pub fn __constructor(env: Env, owner: Address, sbt_contract: Address) {
        env.storage().instance().set(&StorageKey::Owner, &owner);
        env.storage()
            .instance()
            .set(&StorageKey::RoleMask, &(ROLE_OWNER | ROLE_PAUSER | ROLE_CONFIG));
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.storage().instance().set(&StorageKey::SbtContract, &sbt_contract);
        env.storage()
            .instance()
            .set(&StorageKey::MaxWeight, &DEFAULT_MAX_WEIGHT);
    }

    pub fn pause(env: Env, from: Address) -> Result<(), WeightError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &true);
        env.events().publish((Symbol::new(&env, "paused"),), (from,));
        Ok(())
    }

    pub fn unpause(env: Env, from: Address) -> Result<(), WeightError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.events()
            .publish((Symbol::new(&env, "unpaused"),), (from,));
        Ok(())
    }

    pub fn set_max_weight(
        env: Env,
        from: Address,
        max_weight: u32,
    ) -> Result<(), WeightError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_CONFIG | ROLE_OWNER)?;
        if max_weight == 0 || max_weight > 100 {
            return Err(WeightError::InvalidArgument);
        }
        env.storage()
            .instance()
            .set(&StorageKey::MaxWeight, &max_weight);
        env.events().publish(
            (Symbol::new(&env, "max_weight_set"),),
            (from, max_weight),
        );
        Ok(())
    }

    pub fn compute_weight(env: Env, user: Address) -> Result<u32, WeightError> {
        let sbt: Address = env
            .storage()
            .instance()
            .get(&StorageKey::SbtContract)
            .ok_or(WeightError::SbtNotConfigured)?;
        let max: u32 = env
            .storage()
            .instance()
            .get(&StorageKey::MaxWeight)
            .unwrap_or(DEFAULT_MAX_WEIGHT);
        let mut args: Vec<Val> = Vec::new(&env);
        args.push_back(user.clone().into_val(&env));
        let result: Result<Val, soroban_sdk::Error> =
            env.invoke_contract::<Result<Val, soroban_sdk::Error>>(&sbt, &Symbol::new(&env, "count_badges_by_user"), args);
        let badges = match result {
            Ok(v) => <u32 as TryFromVal<Env, Val>>::try_from_val(&env, &v).unwrap_or(0),
            Err(_) => 0,
        };
        let clamped = if badges > max { max } else { badges };
        Ok(clamped)
    }
}
