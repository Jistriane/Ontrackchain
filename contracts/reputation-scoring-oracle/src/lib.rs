#![no_std]
use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, BytesN, Env, Symbol, Val,
    IntoVal, Vec,
};

#[contract]
pub struct ReputationScoringOracle;

#[contracttype]
#[derive(Clone, PartialEq, Eq)]
pub enum StorageKey {
    Owner,
    Paused,
    RoleMask,
    SbtContract,
    ScoreByCase(BytesN<32>),
    CaseRecipient(BytesN<32>),
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum ScoreError {
    Internal = 0,
    InvalidArgument = 100,
    AlreadyScored = 102,
    Paused = 200,
    NotAuthorized = 300,
    RoleOwnerRequired = 301,
    RoleScorerRequired = 303,
    SbtNotConfigured = 601,
}

pub const ROLE_OWNER: u32 = 1 << 0;
pub const ROLE_PAUSER: u32 = 1 << 1;
pub const ROLE_SCORER: u32 = 1 << 2;

fn require_role(env: &Env, _who: &Address, mask: u32) -> Result<(), ScoreError> {
    let current: u32 = env
        .storage()
        .instance()
        .get(&StorageKey::RoleMask)
        .unwrap_or(0);
    if current & mask != mask {
        return Err(match mask {
            ROLE_OWNER => ScoreError::RoleOwnerRequired,
            ROLE_SCORER => ScoreError::RoleScorerRequired,
            _ => ScoreError::NotAuthorized,
        });
    }
    Ok(())
}

fn require_not_paused(env: &Env) -> Result<(), ScoreError> {
    if env.storage().instance().get(&StorageKey::Paused).unwrap_or(false) {
        Err(ScoreError::Paused)
    } else {
        Ok(())
    }
}

#[contractimpl]
impl ReputationScoringOracle {
    pub fn __constructor(env: Env, owner: Address, sbt_contract: Address) {
        env.storage().instance().set(&StorageKey::Owner, &owner);
        env.storage()
            .instance()
            .set(&StorageKey::RoleMask, &(ROLE_OWNER | ROLE_PAUSER | ROLE_SCORER));
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.storage().instance().set(&StorageKey::SbtContract, &sbt_contract);
    }

    pub fn pause(env: Env, from: Address) -> Result<(), ScoreError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &true);
        env.events().publish((Symbol::new(&env, "paused"),), (from,));
        Ok(())
    }

    pub fn unpause(env: Env, from: Address) -> Result<(), ScoreError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.events()
            .publish((Symbol::new(&env, "unpaused"),), (from,));
        Ok(())
    }

    pub fn set_sbt_contract(
        env: Env,
        from: Address,
        sbt_contract: Address,
    ) -> Result<(), ScoreError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_OWNER)?;
        env.storage()
            .instance()
            .set(&StorageKey::SbtContract, &sbt_contract);
        env.events().publish(
            (Symbol::new(&env, "sbt_contract_set"),),
            (from, sbt_contract),
        );
        Ok(())
    }

    pub fn set_score(
        env: Env,
        from: Address,
        recipient: Address,
        case_id: BytesN<32>,
        score: u32,
    ) -> Result<(), ScoreError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_SCORER)?;
        if score > 100 {
            return Err(ScoreError::InvalidArgument);
        }
        let key = StorageKey::ScoreByCase(case_id.clone());
        if env.storage().persistent().has(&key) {
            return Err(ScoreError::AlreadyScored);
        }
        let sbt: Address = env
            .storage()
            .instance()
            .get(&StorageKey::SbtContract)
            .ok_or(ScoreError::SbtNotConfigured)?;
        env.storage().persistent().set(&key, &score);
        env.storage()
            .persistent()
            .set(&StorageKey::CaseRecipient(case_id.clone()), &recipient);
        if score >= 50 {
            let mut args: Vec<Val> = Vec::new(&env);
            args.push_back(from.clone().into_val(&env));
            args.push_back(recipient.clone().into_val(&env));
            args.push_back(case_id.clone().into_val(&env));
            args.push_back(score.into_val(&env));
            let _minted_id: Result<Val, soroban_sdk::Error> = env.invoke_contract::<Result<Val, soroban_sdk::Error>>(
                &sbt,
                &Symbol::new(&env, "mint_for_case"),
                args,
            );
        }
        env.events().publish(
            (Symbol::new(&env, "score_set"),),
            (from, recipient, case_id, score),
        );
        Ok(())
    }

    pub fn get_score(env: Env, case_id: BytesN<32>) -> Option<u32> {
        env.storage()
            .persistent()
            .get(&StorageKey::ScoreByCase(case_id))
    }
}
