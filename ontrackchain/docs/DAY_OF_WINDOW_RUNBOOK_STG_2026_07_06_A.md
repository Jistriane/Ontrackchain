# Roteiro Operacional do Dia da Janela `stg-2026-07-06-a`

## Objetivo

Condensar em uma única sequência o que precisa acontecer no dia da janela `stg-2026-07-06-a`, da abertura do war room até a decisão final de `go/no-go`.

## Pré-condições

- `.env.staging.private` disponível no canal seguro correto
- facilitador do war room definido
- owners online por trilha definidos
- documentos vivos já abertos:
  - [War Room da Janela `stg-2026-07-06-a`](./governance-weekly/2026-07-06-staging-serious-window-war-room.md)
  - [Tracking ao Vivo da Janela `stg-2026-07-06-a`](./governance-weekly/2026-07-06-staging-serious-window-live-tracking.md)
  - [Folha de Preenchimento Manual `stg-2026-07-06-a`](./governance-weekly/2026-07-06-staging-serious-window-manual-fill-sheet.md)
  - [Ata ao Vivo da Governança — 2026-07-06](./governance-weekly/2026-07-06-governance-live-minutes.md)

## Sequência do Dia

### 1. Abrir war room

- preencher facilitador online
- preencher canal principal
- preencher bridge principal de escalacao
- preencher hora do próximo checkpoint

Saída esperada:

- war room deixa de ter placeholders transversais

### 2. Validar `Platform/Operations`

- rodar `check_staging_env_handoff.py`
- rodar `check_staging_env_placeholders.py`
- confirmar segredos base fora de placeholder

Saída esperada:

- domínio `Platform/Operations` deixa de bloquear as demais trilhas

### 3. Validar `Auth/OIDC`

- confirmar secrets reais do domínio
- rodar `preflight_oidc_serious_env.py`
- se aplicável, gerar bundle OIDC

Saída esperada:

- preflight OIDC verde
- bundle OIDC gerado quando `P0-01` estiver no escopo

### 4. Validar `Investigation/RPC`

- confirmar URLs reais de RPC primário e fallback
- rodar `preflight_external_integrations.py`

Saída esperada:

- preflight externo coerente com o modo esperado

### 5. Validar `Compliance/AML`

- confirmar credenciais reais do provider `AML/KYT`
- confirmar URL tokenizada do feed UE, quando no escopo
- rodar `check-compliance-provider-runtime`
- rodar a janela UE, quando aplicável

Saída esperada:

- checker AML/KYT verde
- JSONs de preflight/sync UE gerados quando aplicável

### 6. Rodar gate agregado

Executar:

```bash
python scripts/prepare_staging_window.py --window-id stg-2026-07-06-a --mode baseline --private-env-file .env.staging.private --validate --preflight
```

Saída esperada:

- `status=ok`

### 7. Decidir `go/no-go`

Se o gate agregado ficar verde:

- permitir execução de `run_staging_window.py`
- atualizar war room, tracking e ata ao vivo

Se o gate agregado não ficar verde:

- manter `no-go`
- registrar bloqueadores restantes e responsáveis

### 8. Executar a janela, se houver `go`

Executar:

```bash
python scripts/run_staging_window.py --window-id stg-2026-07-06-a --private-env-file .env.staging.private
```

Saída esperada:

- checks em `artifacts/staging/checks/`
- homologação em `artifacts/homologation/`
- dossier em `artifacts/staging/dossiers/`

### 9. Fechar documentação viva

- atualizar war room com decisão final
- atualizar tracking ao vivo com último checkpoint
- atualizar ata ao vivo com evidências e status
- preencher sign-off com artefatos finais

## Critérios de `no-go` Imediato

- placeholder crítico ainda aberto
- `handoff` ainda com `pending`
- `P0-01` sem preflight OIDC verde quando estiver no escopo
- `P0-02` sem checker AML/KYT verde quando estiver no escopo
- `P0-03` sem JSONs UE válidos quando estiver no escopo
- gate agregado sem `status=ok`

## Artefatos Finais Esperados

- `window packet`
- JSONs de checks/preflights
- bundles OIDC/regulatório, quando aplicáveis
- dossier final
- sign-off preenchido
- ata ao vivo atualizada
