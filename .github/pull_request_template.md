# Resumo
- 

# Escopo
- 

# Risco & Rollback
- **Risco principal**: 
- **Rollback**: reverter o squash commit deste PR.

# Validações (obrigatório)
- [ ] Não há secrets no diff (sem `.env*`, tokens, chaves)
- [ ] CI passou (incluindo **Gate P0-01 — OIDC Mock** quando o PR afetar auth/traefik/frontend/compose/gates)

# Validações (marque as aplicáveis)
- [ ] **Frontend**: `cd ontrackchain/apps/frontend && npm ci && npm run typecheck`
- [ ] **Gate OIDC mock (quando aplicável)**: `bash ontrackchain/scripts/run_p0_01_oidc_mock_gate.sh ontrackchain/.env.oidc-mock http://localhost:8080`
- [ ] **AI approve smoke**: validar `missing_x_user_id` (400) e idempotência (200+200)
- [ ] **Shared unit tests**: `PYTHONPATH=ontrackchain/packages/shared/src PYTHONPYCACHEPREFIX=/tmp/ontrackchain_pycache python3 -m unittest discover -s ontrackchain/packages/shared/tests -p 'test_*.py' -q`
- [ ] **Docs**: links portáveis (sem `file:///`) e coerentes com scripts/env vars
