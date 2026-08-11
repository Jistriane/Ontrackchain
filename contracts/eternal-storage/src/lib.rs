#![no_std]

use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, Bytes, BytesN, Env, Symbol,
};

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ESKey {
    Admin,
    LogicWhitelist(Address),
    Value(BytesN<64>),
}

#[contracterror]
#[repr(u32)]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
pub enum EternalStorageError {
    Internal = 0,
    NotAuthorized = 300,
    NotWhitelisted = 301,
}

#[contract]
pub struct EternalStorage;

#[contractimpl]
impl EternalStorage {
    pub fn __constructor(env: Env, admin: Address) {
        admin.require_auth();
        env.storage()
            .instance()
            .set(&ESKey::Admin, &admin);
    }

    pub fn whitelist_logic(
        env: Env,
        from: Address,
        logic_address: Address,
    ) -> Result<(), EternalStorageError> {
        from.require_auth();
        Self::require_admin(&env, &from)?;
        let key = ESKey::LogicWhitelist(logic_address.clone());
        env.storage().persistent().set(&key, &true);
        env.events().publish(
            (Symbol::new(&env, "logic_whitelisted"),),
            (from, logic_address),
        );
        Ok(())
    }

    pub fn remove_whitelist(
        env: Env,
        from: Address,
        logic_address: Address,
    ) -> Result<(), EternalStorageError> {
        from.require_auth();
        Self::require_admin(&env, &from)?;
        let key = ESKey::LogicWhitelist(logic_address);
        env.storage().persistent().remove(&key);
        Ok(())
    }

    pub fn store(
        env: Env,
        from: Address,
        key: BytesN<64>,
        value: Bytes,
    ) -> Result<(), EternalStorageError> {
        from.require_auth();
        if !Self::is_whitelisted(&env, &from) {
            return Err(EternalStorageError::NotWhitelisted);
        }
        let k = ESKey::Value(key.clone());
        env.storage().persistent().set(&k, &value);
        env.events().publish(
            (Symbol::new(&env, "stored"),),
            (from, key, value.len() as u64),
        );
        Ok(())
    }

    pub fn load(_env: Env, key: BytesN<64>) -> Option<Bytes> {
        let k = ESKey::Value(key);
        _env.storage().persistent().get::<_, Bytes>(&k)
    }
}

impl EternalStorage {
    fn require_admin(env: &Env, who: &Address) -> Result<(), EternalStorageError> {
        let admin: Option<Address> = env
            .storage()
            .instance()
            .get::<_, Address>(&ESKey::Admin);
        match admin {
            Some(a) if a == *who => Ok(()),
            _ => Err(EternalStorageError::NotAuthorized),
        }
    }

    fn is_whitelisted(env: &Env, logic: &Address) -> bool {
        let key = ESKey::LogicWhitelist(logic.clone());
        env.storage()
            .persistent()
            .get::<_, bool>(&key)
            .unwrap_or(false)
    }
}
