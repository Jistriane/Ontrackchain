#![no_std]
use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, BytesN, Env, Symbol, Val,
    Vec, IntoVal,
};

#[contract]
pub struct PaymentEscrowV1;

#[contracttype]
#[derive(Clone, PartialEq, Eq)]
pub enum StorageKey {
    Owner,
    Paused,
    RoleMask,
    EvidenceContract,
    FeeDistributorContract,
    BaseFeeStroops,
    Payment(BytesN<32>),
    NextNonce,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum EscrowError {
    Internal = 0,
    InvalidArgument = 100,
    AlreadyPaid = 103,
    Paused = 200,
    NotAuthorized = 300,
    RoleOwnerRequired = 301,
    RoleWriterRequired = 302,
    EvidenceNotAnchored = 500,
    NotPaid = 501,
    AlreadyReleased = 502,
    ConfigMissing = 600,
}

pub const ROLE_OWNER: u32 = 1 << 0;
pub const ROLE_PAUSER: u32 = 1 << 1;
pub const ROLE_WRITER: u32 = 1 << 2;

#[contracttype]
#[derive(Clone)]
pub struct EscrowPayment {
    pub case_id: BytesN<32>,
    pub payer: Address,
    pub amount_stroops: i128,
    pub created_ledger: u32,
    pub released: bool,
}

fn require_role(env: &Env, _who: &Address, mask: u32) -> Result<(), EscrowError> {
    let current: u32 = env
        .storage()
        .instance()
        .get(&StorageKey::RoleMask)
        .unwrap_or(0);
    if current & mask != mask {
        return Err(match mask {
            ROLE_OWNER => EscrowError::RoleOwnerRequired,
            ROLE_WRITER => EscrowError::RoleWriterRequired,
            _ => EscrowError::NotAuthorized,
        });
    }
    Ok(())
}

fn require_not_paused(env: &Env) -> Result<(), EscrowError> {
    if env.storage().instance().get(&StorageKey::Paused).unwrap_or(false) {
        Err(EscrowError::Paused)
    } else {
        Ok(())
    }
}

#[contractimpl]
impl PaymentEscrowV1 {
    pub fn __constructor(
        env: Env,
        owner: Address,
        evidence_contract: Address,
        fee_distributor: Address,
        base_fee_stroops: i128,
    ) {
        env.storage().instance().set(&StorageKey::Owner, &owner);
        env.storage()
            .instance()
            .set(&StorageKey::RoleMask, &(ROLE_OWNER | ROLE_PAUSER | ROLE_WRITER));
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.storage()
            .instance()
            .set(&StorageKey::EvidenceContract, &evidence_contract);
        env.storage()
            .instance()
            .set(&StorageKey::FeeDistributorContract, &fee_distributor);
        env.storage()
            .instance()
            .set(&StorageKey::BaseFeeStroops, &base_fee_stroops.max(1));
        env.storage().instance().set(&StorageKey::NextNonce, &1u64);
    }

    pub fn pause(env: Env, from: Address) -> Result<(), EscrowError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &true);
        env.events().publish((Symbol::new(&env, "paused"),), (from,));
        Ok(())
    }

    pub fn unpause(env: Env, from: Address) -> Result<(), EscrowError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.events()
            .publish((Symbol::new(&env, "unpaused"),), (from,));
        Ok(())
    }

    pub fn set_base_fee(
        env: Env,
        from: Address,
        base_fee_stroops: i128,
    ) -> Result<(), EscrowError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_OWNER)?;
        if base_fee_stroops < 0 {
            return Err(EscrowError::InvalidArgument);
        }
        env.storage()
            .instance()
            .set(&StorageKey::BaseFeeStroops, &base_fee_stroops);
        env.events().publish(
            (Symbol::new(&env, "base_fee_set"),),
            (from, base_fee_stroops),
        );
        Ok(())
    }

    pub fn get_base_fee(env: Env) -> i128 {
        env.storage()
            .instance()
            .get(&StorageKey::BaseFeeStroops)
            .unwrap_or(0)
    }

    pub fn deposit_for_case(
        env: Env,
        from: Address,
        case_id: BytesN<32>,
        amount_stroops: i128,
    ) -> Result<(), EscrowError> {
        from.require_auth();
        require_not_paused(&env)?;
        if amount_stroops <= 0 {
            return Err(EscrowError::InvalidArgument);
        }
        let base_fee = Self::get_base_fee(env.clone());
        if base_fee > 0 && amount_stroops < base_fee {
            return Err(EscrowError::InvalidArgument);
        }
        let key = StorageKey::Payment(case_id.clone());
        if env.storage().persistent().has(&key) {
            return Err(EscrowError::AlreadyPaid);
        }
        let ledger = env.ledger().sequence();
        let rec = EscrowPayment {
            case_id: case_id.clone(),
            payer: from.clone(),
            amount_stroops,
            created_ledger: ledger,
            released: false,
        };
        env.storage().persistent().set(&key, &rec);
        env.events().publish(
            (Symbol::new(&env, "payment_deposited"),),
            (from, case_id, amount_stroops, ledger),
        );
        Ok(())
    }

    pub fn release_after_anchor(
        env: Env,
        from: Address,
        case_id: BytesN<32>,
    ) -> Result<(), EscrowError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_WRITER)?;
        let evidence: Address = env
            .storage()
            .instance()
            .get(&StorageKey::EvidenceContract)
            .ok_or(EscrowError::ConfigMissing)?;
        let mut args_check: Vec<Val> = Vec::new(&env);
        args_check.push_back(case_id.clone().into_val(&env));
        let is_anchored_call: Result<Val, soroban_sdk::Error> = env.invoke_contract::<Result<Val, soroban_sdk::Error>>(
            &evidence,
            &Symbol::new(&env, "get_single_anchor"),
            args_check,
        );
        if is_anchored_call.is_err() {
            return Err(EscrowError::EvidenceNotAnchored);
        }
        let key = StorageKey::Payment(case_id.clone());
        let mut rec: EscrowPayment = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(EscrowError::NotPaid)?;
        if rec.released {
            return Err(EscrowError::AlreadyReleased);
        }
        rec.released = true;
        env.storage().persistent().set(&key, &rec);
        env.events().publish(
            (Symbol::new(&env, "payment_released"),),
            (from, case_id, rec.amount_stroops),
        );
        Ok(())
    }

    pub fn get_payment(env: Env, case_id: BytesN<32>) -> Option<EscrowPayment> {
        env.storage()
            .persistent()
            .get(&StorageKey::Payment(case_id))
    }
}
