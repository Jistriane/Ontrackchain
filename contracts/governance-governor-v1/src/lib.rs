#![no_std]
use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, Address, Bytes, BytesN, Env, Symbol, Val,
    Vec, TryFromVal, IntoVal,
};

#[contract]
pub struct GovernanceGovernorV1;

#[contracttype]
#[derive(Clone, PartialEq, Eq)]
pub enum StorageKey {
    Owner,
    Paused,
    RoleMask,
    WeightCalc,
    Timelock,
    Proposal(BytesN<32>),
    VoteReceipt(BytesN<32>, Address),
    NextProposalId,
    VoteDurationSecs,
    MinQuorumWeight,
    MinProposerWeight,
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum GovError {
    Internal = 0,
    InvalidArgument = 100,
    AlreadyVoted = 104,
    Paused = 200,
    NotAuthorized = 300,
    RoleOwnerRequired = 301,
    WeightTooLowProposer = 307,
    ProposalNotFound = 400,
    NotActive = 405,
    FinishedNoQuorum = 406,
    ProposalRejected = 407,
    AlreadyQueued = 408,
    NotEnoughWeight = 409,
    NotConfigured = 600,
}

pub const ROLE_OWNER: u32 = 1 << 0;
pub const ROLE_PAUSER: u32 = 1 << 1;
pub const ROLE_EXECUTOR: u32 = 1 << 2;
pub const SUPPORT_AGAINST: u32 = 0;
pub const SUPPORT_FOR: u32 = 1;
pub const SUPPORT_ABSTAIN: u32 = 2;
pub const DEFAULT_VOTE_DURATION_SECS: u64 = 259_200;
pub const DEFAULT_MIN_QUORUM_WEIGHT: u32 = 10;
pub const DEFAULT_MIN_PROPOSER_WEIGHT: u32 = 1;

#[contracttype]
#[derive(Clone)]
pub struct ProposalRecord {
    pub id: BytesN<32>,
    pub proposer: Address,
    pub targets: Vec<Address>,
    pub calldatas: Vec<Bytes>,
    pub values: Vec<i128>,
    pub description_hash: BytesN<32>,
    pub start_ts: u64,
    pub end_ts: u64,
    pub for_weight: u32,
    pub against_weight: u32,
    pub abstain_weight: u32,
    pub queued: bool,
    pub executed: bool,
    pub nonce: u64,
}

fn require_role(env: &Env, _who: &Address, mask: u32) -> Result<(), GovError> {
    let current: u32 = env
        .storage()
        .instance()
        .get(&StorageKey::RoleMask)
        .unwrap_or(0);
    if current & mask != mask {
        return Err(match mask {
            ROLE_OWNER => GovError::RoleOwnerRequired,
            _ => GovError::NotAuthorized,
        });
    }
    Ok(())
}

fn require_not_paused(env: &Env) -> Result<(), GovError> {
    if env.storage().instance().get(&StorageKey::Paused).unwrap_or(false) {
        Err(GovError::Paused)
    } else {
        Ok(())
    }
}

fn hash_proposal(
    env: &Env,
    proposer: &Address,
    nonce: u64,
    description_hash: &BytesN<32>,
) -> BytesN<32> {
    let mut buf = [0u8; 8];
    buf.copy_from_slice(&nonce.to_le_bytes());
    let mut combined = Bytes::from_array(env, &buf);
    let dh_b: Bytes = description_hash.clone().into();
    combined.append(&dh_b);
    let pv = proposer.clone().into_val(env);
    let p_b = <Bytes as TryFromVal<Env, Val>>::try_from_val(env, &pv).unwrap_or(Bytes::new(env));
    combined.append(&p_b);
    env.crypto().sha256(&combined).into()
}

fn weight_of(env: &Env, weight_contract: &Address, who: &Address) -> u32 {
    let mut args: Vec<Val> = Vec::new(env);
    args.push_back(who.clone().into_val(env));
    let res: Result<Val, soroban_sdk::Error> = env.invoke_contract::<Result<Val, soroban_sdk::Error>>(
        weight_contract,
        &Symbol::new(env, "compute_weight"),
        args,
    );
    match res {
        Ok(v) => <u32 as TryFromVal<Env, Val>>::try_from_val(env, &v).unwrap_or(0),
        Err(_) => 0,
    }
}

#[contractimpl]
impl GovernanceGovernorV1 {
    pub fn __constructor(
        env: Env,
        owner: Address,
        weight_calculator: Address,
        timelock: Address,
        vote_duration_secs: u64,
        min_quorum_weight: u32,
        min_proposer_weight: u32,
    ) {
        env.storage().instance().set(&StorageKey::Owner, &owner);
        env.storage()
            .instance()
            .set(&StorageKey::RoleMask, &(ROLE_OWNER | ROLE_PAUSER | ROLE_EXECUTOR));
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.storage()
            .instance()
            .set(&StorageKey::WeightCalc, &weight_calculator);
        env.storage()
            .instance()
            .set(&StorageKey::Timelock, &timelock);
        env.storage().instance().set(
            &StorageKey::VoteDurationSecs,
            &vote_duration_secs.max(600),
        );
        env.storage()
            .instance()
            .set(&StorageKey::MinQuorumWeight, &min_quorum_weight.max(1));
        env.storage().instance().set(
            &StorageKey::MinProposerWeight,
            &min_proposer_weight.max(0),
        );
        env.storage().instance().set(&StorageKey::NextProposalId, &1u64);
    }

    pub fn pause(env: Env, from: Address) -> Result<(), GovError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &true);
        env.events().publish((Symbol::new(&env, "paused"),), (from,));
        Ok(())
    }

    pub fn unpause(env: Env, from: Address) -> Result<(), GovError> {
        from.require_auth();
        require_role(&env, &from, ROLE_PAUSER)?;
        env.storage().instance().set(&StorageKey::Paused, &false);
        env.events()
            .publish((Symbol::new(&env, "unpaused"),), (from,));
        Ok(())
    }

    pub fn create_proposal(
        env: Env,
        from: Address,
        targets: Vec<Address>,
        calldatas: Vec<Bytes>,
        values: Vec<i128>,
        description_hash: BytesN<32>,
    ) -> Result<BytesN<32>, GovError> {
        from.require_auth();
        require_not_paused(&env)?;
        if targets.is_empty() || targets.len() != calldatas.len() || targets.len() != values.len() {
            return Err(GovError::InvalidArgument);
        }
        let wc: Address = env
            .storage()
            .instance()
            .get(&StorageKey::WeightCalc)
            .ok_or(GovError::NotConfigured)?;
        let proposer_weight = weight_of(&env, &wc, &from);
        let min_prop: u32 = env
            .storage()
            .instance()
            .get(&StorageKey::MinProposerWeight)
            .unwrap_or(DEFAULT_MIN_PROPOSER_WEIGHT);
        if proposer_weight < min_prop {
            return Err(GovError::WeightTooLowProposer);
        }
        let nonce: u64 = env
            .storage()
            .instance()
            .get(&StorageKey::NextProposalId)
            .unwrap_or(1);
        let id = hash_proposal(&env, &from, nonce, &description_hash);
        let duration: u64 = env
            .storage()
            .instance()
            .get(&StorageKey::VoteDurationSecs)
            .unwrap_or(DEFAULT_VOTE_DURATION_SECS);
        let now = env.ledger().timestamp();
        let record = ProposalRecord {
            id: id.clone(),
            proposer: from.clone(),
            targets: targets.clone(),
            calldatas: calldatas.clone(),
            values: values.clone(),
            description_hash: description_hash.clone(),
            start_ts: now + 60,
            end_ts: now + 60 + duration,
            for_weight: 0,
            against_weight: 0,
            abstain_weight: 0,
            queued: false,
            executed: false,
            nonce,
        };
        env.storage()
            .persistent()
            .set(&StorageKey::Proposal(id.clone()), &record);
        env.storage()
            .instance()
            .set(&StorageKey::NextProposalId, &(nonce + 1));
        env.events().publish(
            (Symbol::new(&env, "proposal_created"),),
            (from, id.clone(), nonce, proposer_weight),
        );
        Ok(id)
    }

    pub fn cast_vote(
        env: Env,
        from: Address,
        proposal_id: BytesN<32>,
        support: u32,
    ) -> Result<u32, GovError> {
        from.require_auth();
        require_not_paused(&env)?;
        if support > 2 {
            return Err(GovError::InvalidArgument);
        }
        let wc: Address = env
            .storage()
            .instance()
            .get(&StorageKey::WeightCalc)
            .ok_or(GovError::NotConfigured)?;
        let key = StorageKey::Proposal(proposal_id.clone());
        let mut prop: ProposalRecord = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(GovError::ProposalNotFound)?;
        let now = env.ledger().timestamp();
        if now < prop.start_ts || now > prop.end_ts {
            return Err(GovError::NotActive);
        }
        let vkey = StorageKey::VoteReceipt(proposal_id.clone(), from.clone());
        if env.storage().persistent().has(&vkey) {
            return Err(GovError::AlreadyVoted);
        }
        let w = weight_of(&env, &wc, &from);
        env.storage().persistent().set(&vkey, &support);
        match support {
            SUPPORT_FOR => prop.for_weight = prop.for_weight.saturating_add(w),
            SUPPORT_AGAINST => prop.against_weight = prop.against_weight.saturating_add(w),
            _ => prop.abstain_weight = prop.abstain_weight.saturating_add(w),
        }
        env.storage().persistent().set(&key, &prop);
        env.events().publish(
            (Symbol::new(&env, "vote_cast"),),
            (from, proposal_id, support, w),
        );
        Ok(w)
    }

    pub fn queue(
        env: Env,
        from: Address,
        proposal_id: BytesN<32>,
        nonce: u64,
    ) -> Result<BytesN<32>, GovError> {
        from.require_auth();
        require_not_paused(&env)?;
        require_role(&env, &from, ROLE_EXECUTOR)?;
        let timelock: Address = env
            .storage()
            .instance()
            .get(&StorageKey::Timelock)
            .ok_or(GovError::NotConfigured)?;
        let key = StorageKey::Proposal(proposal_id.clone());
        let mut prop: ProposalRecord = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(GovError::ProposalNotFound)?;
        if prop.queued {
            return Err(GovError::AlreadyQueued);
        }
        let now = env.ledger().timestamp();
        if now < prop.end_ts {
            return Err(GovError::NotActive);
        }
        let quorum: u32 = env
            .storage()
            .instance()
            .get(&StorageKey::MinQuorumWeight)
            .unwrap_or(DEFAULT_MIN_QUORUM_WEIGHT);
        let total = prop
            .for_weight
            .saturating_add(prop.against_weight)
            .saturating_add(prop.abstain_weight);
        if total < quorum {
            return Err(GovError::FinishedNoQuorum);
        }
        if prop.for_weight <= prop.against_weight {
            return Err(GovError::ProposalRejected);
        }
        prop.queued = true;
        env.storage().persistent().set(&key, &prop);
        let mut queue_args: Vec<Val> = Vec::new(&env);
        queue_args.push_back(from.clone().into_val(&env));
        queue_args.push_back(nonce.into_val(&env));
        queue_args.push_back(prop.targets.clone().into_val(&env));
        queue_args.push_back(prop.calldatas.clone().into_val(&env));
        queue_args.push_back(prop.values.clone().into_val(&env));
        let queued: Result<Val, soroban_sdk::Error> = env.invoke_contract::<Result<Val, soroban_sdk::Error>>(
            &timelock,
            &Symbol::new(&env, "queue_transaction"),
            queue_args,
        );
        let tx_id = match queued {
            Ok(v) => <BytesN<32> as TryFromVal<Env, Val>>::try_from_val(&env, &v)
                .unwrap_or_else(|_| BytesN::from_array(&env, &[0u8; 32])),
            Err(_) => BytesN::from_array(&env, &[0u8; 32]),
        };
        env.events().publish(
            (Symbol::new(&env, "proposal_queued"),),
            (from, proposal_id, tx_id.clone()),
        );
        Ok(tx_id)
    }

    pub fn get_proposal(env: Env, proposal_id: BytesN<32>) -> Option<ProposalRecord> {
        env.storage()
            .persistent()
            .get(&StorageKey::Proposal(proposal_id))
    }
}
