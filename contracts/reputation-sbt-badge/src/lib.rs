#![no_std]
use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, BytesN, Env, Symbol, Vec,
};

#[contract]
pub struct ReputationSbtBadge;

#[contracttype]
#[derive(Clone, PartialEq, Eq)]
pub enum StorageKey {
    Owner,
    Paused,
    RoleMask,
    LevelThresholds,
    MintedByCase(BytesN<32>),
    BadgeById(u64),
    UserBadges(Address),
    NextBadgeId,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum SbtError {
    Internal = 0,
    InvalidArgument = 100,
    AlreadyMinted = 102,
    Paused = 200,
    NotAuthorized = 300,
    RoleOwnerRequired = 301,
    RoleMinterRequired = 302,
    NotFound = 700,
}

pub const ROLE_OWNER: u32 = 1 << 0;
pub const ROLE_PAUSER: u32 = 1 << 1;
pub const ROLE_MINTER: u32 = 1 << 2;

pub const LEVEL_BRONZE: u32 = 1;
pub const LEVEL_PRATA: u32 = 2;
pub const LEVEL_OURO: u32 = 3;

#[contracttype]
#[derive(Clone)]
pub struct SbtBadgeRecord {
    pub badge_id: u64,
    pub recipient: Address,
    pub case_id: BytesN<32>,
    pub score: u32,
    pub level: u32,
    pub minted_ledger: u32,
    pub minter: Address,
}

fn require_role(env: &Env, _who: &Address, mask: u32) -> Result<(), SbtError> {
    let current: u32 = env
        .storage()
        .instance()
        .get(&StorageKey::RoleMask)
        .unwrap_or(0);
    if current & mask != mask {
        return Err(match mask {
            ROLE_OWNER => SbtError::RoleOwnerRequired,
            ROLE_MINTER => SbtError::RoleMinterRequired,
            _ => SbtError::NotAuthorized,
        });
    }
    Ok(())
}

fn require_not_paused(env: &Env) -> Result<(), SbtError> {
    if env.storage().instance().get(&StorageKey::Paused).unwrap_or(false) {
        Err(SbtError::Paused)
    } else {
        Ok(())
    }
}

fn level_for_score(score: u32) -> u32 {
    if score >= 90 {
        LEVEL_OURO
    } else if score >= 75 {
        LEVEL_PRATA
    } else if score >= 50 {
        LEVEL_BRONZE
    } else {
        0
    }
}

#[contractimpl]
impl ReputationSbtBadge {
    pub fn __constructor(env: Env, owner: Address) {
        env.storage().instance().set(&StorageKey::Owner, &owner);
        env.storage()
            .instance()
            .set(&StorageKey::RoleMask, &(ROLE_OWNER | ROLE_PAUSER | ROLE_MINTER));
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.storage().instance().set(&StorageKey::NextBadgeId, &1u64);
    }

    pub fn grant_role(env: Env, from: Address, target: Address, role_mask: u32) -> Result<(), SbtError> {
        from.require_auth();
        require_role(&env, &from, ROLE_OWNER)?;
        let current: u32 = env
            .storage()
            .instance()
            .get(&StorageKey::RoleMask)
            .unwrap_or(0);
        let merged = current | role_mask;
        env.storage().instance().set(&StorageKey::RoleMask, &merged);
        let _ = target;
        env.events().publish(
            (Symbol::new(&env, "role_granted"),),
            (from, role_mask, target),
        );
        Ok(())
    }

    pub fn pause(env: Env, from: Address) -> Result<(), SbtError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &true);
        env.events().publish((Symbol::new(&env, "paused"),), (from,));
        Ok(())
    }

    pub fn unpause(env: Env, from: Address) -> Result<(), SbtError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.events()
            .publish((Symbol::new(&env, "unpaused"),), (from,));
        Ok(())
    }

    pub fn mint_for_case(
        env: Env,
        from: Address,
        recipient: Address,
        case_id: BytesN<32>,
        score: u32,
    ) -> Result<u64, SbtError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_MINTER)?;
        if score > 100 {
            return Err(SbtError::InvalidArgument);
        }
        let level = level_for_score(score);
        if level == 0 {
            return Err(SbtError::InvalidArgument);
        }
        if env
            .storage()
            .persistent()
            .has(&StorageKey::MintedByCase(case_id.clone()))
        {
            return Err(SbtError::AlreadyMinted);
        }
        let next_id: u64 = env
            .storage()
            .instance()
            .get(&StorageKey::NextBadgeId)
            .unwrap_or(1);
        let ledger = env.ledger().sequence();
        let record = SbtBadgeRecord {
            badge_id: next_id,
            recipient: recipient.clone(),
            case_id: case_id.clone(),
            score,
            level,
            minted_ledger: ledger,
            minter: from.clone(),
        };
        env.storage()
            .persistent()
            .set(&StorageKey::MintedByCase(case_id.clone()), &next_id);
        env.storage()
            .persistent()
            .set(&StorageKey::BadgeById(next_id), &record);
        let key_usr = StorageKey::UserBadges(recipient.clone());
        let mut user_list: Vec<u64> =
            env.storage().persistent().get(&key_usr).unwrap_or(Vec::new(&env));
        user_list.push_back(next_id);
        env.storage().persistent().set(&key_usr, &user_list);
        env.storage()
            .instance()
            .set(&StorageKey::NextBadgeId, &(next_id + 1));
        env.events().publish(
            (Symbol::new(&env, "badge_minted"),),
            (from, recipient, case_id, score, level, next_id),
        );
        Ok(next_id)
    }

    pub fn count_badges_by_user(env: Env, user: Address) -> u32 {
        let key = StorageKey::UserBadges(user);
        let v: Vec<u64> = env.storage().persistent().get(&key).unwrap_or(Vec::new(&env));
        v.len() as u32
    }

    pub fn get_badge(env: Env, badge_id: u64) -> Result<SbtBadgeRecord, SbtError> {
        env.storage()
            .persistent()
            .get(&StorageKey::BadgeById(badge_id))
            .ok_or(SbtError::NotFound)
    }

    pub fn is_case_minted(env: Env, case_id: BytesN<32>) -> bool {
        env.storage()
            .persistent()
            .has(&StorageKey::MintedByCase(case_id))
    }
}
