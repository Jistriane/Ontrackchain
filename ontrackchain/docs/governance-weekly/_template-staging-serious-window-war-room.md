# War Room da Janela Seria — <window_id>

## Contexto

- data:
- window_id:
- mode:
- environment_name:
- facilitador:
- objetivo da janela:
- baseline canônica: `91% / 78% / 87%`

## Leitura de Go/No-Go

- status atual: `go` | `no-go` | `go_with_exception`
- motivo principal:
- risco residual:
- proximo checkpoint:
- hora do proximo checkpoint:
- facilitador online: `<nome_owner_online>`
- canal principal do war room: `<slack_ou_teams_canal>`
- bridge de escalacao principal: `<canal_bridge_ou_incident_room>`

## Status Permitidos

- trilha: `pending` | `in_progress` | `blocked` | `ready` | `done` | `waived`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- decisao final: `go` | `no-go` | `go_with_exception`

## Trilhas do War Room

- `Platform/Operations`
  - owner primario: `<nome_owner_primario>`
  - backup/escalacao: `<nome_owner_backup>`
  - canal de contato: `<slack_ou_teams_canal>`
  - status: `pending`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - dependencia critica: `<secret_ou_gate_ativo>`
  - comando: `<comando_minimo>`
  - evidencia minima: `<evidencia_esperada>`
  - criterio de go/no-go: `<criterio_curto>`
  - observacoes: `<observacao_curta>`
- `Auth/OIDC`
  - owner primario: `<nome_owner_primario>`
  - backup/escalacao: `<nome_owner_backup>`
  - canal de contato: `<slack_ou_teams_canal>`
  - status: `pending`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - dependencia critica: `<secret_ou_gate_ativo>`
  - comando: `<comando_minimo>`
  - evidencia minima: `<evidencia_esperada>`
  - criterio de go/no-go: `<criterio_curto>`
  - observacoes: `<observacao_curta>`
- `Investigation/RPC`
  - owner primario: `<nome_owner_primario>`
  - backup/escalacao: `<nome_owner_backup>`
  - canal de contato: `<slack_ou_teams_canal>`
  - status: `pending`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - dependencia critica: `<secret_ou_gate_ativo>`
  - comando: `<comando_minimo>`
  - evidencia minima: `<evidencia_esperada>`
  - criterio de go/no-go: `<criterio_curto>`
  - observacoes: `<observacao_curta>`
- `Compliance/AML`
  - owner primario: `<nome_owner_primario>`
  - backup/escalacao: `<nome_owner_backup>`
  - canal de contato: `<slack_ou_teams_canal>`
  - status: `pending`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - dependencia critica: `<secret_ou_gate_ativo>`
  - comando: `<comando_minimo>`
  - evidencia minima: `<evidencia_esperada>`
  - criterio de go/no-go: `<criterio_curto>`
  - observacoes: `<observacao_curta>`
- `Gate Agregado da Janela`
  - owner primario: `<nome_owner_primario>`
  - backup/escalacao: `<nome_owner_backup>`
  - canal de contato: `<slack_ou_teams_canal>`
  - status: `pending`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - dependencia critica: `<secret_ou_gate_ativo>`
  - comando: `<comando_minimo>`
  - evidencia minima: `<evidencia_esperada>`
  - criterio de go/no-go: `<criterio_curto>`
  - observacoes: `<observacao_curta>`

## Bloqueadores Ativos

- ID:
  - trilha:
  - descricao: `<descricao_curta>`
  - owner da escalacao: `<nome_owner_escalacao>`
  - canal da escalacao: `<bridge_de_escalacao>`
  - tempo alvo: `<HH:MMZ ou 30 min>`
  - status: `open`

## Evidencias Revisadas

- `handoff.json`:
- `placeholders.json`:
- `preflight_oidc_serious_env.py`:
- `preflight_external_integrations.py`:
- `check-compliance-provider-runtime`:
- `<janela>-eu-sanctions-preflight.json`:
- `<janela>-eu-sanctions-sync.json`:
- `regulatory-readiness-bundle.json`:
- `regulatory-readiness-bundle.md`:
- `prepare-staging-window-output.json`:

## Decisoes

- decisao registrada:

## Proximo Passo Autorizado

- acao: `<acao_objetiva>`
- owner: `<nome_owner_online>`
- canal: `<slack_ou_teams_canal>`
- criterio para seguir: `<criterio_objetivo>`

## Resultado Final do War Room

- decisao final: `go` | `no-go` | `go_with_exception`
- justificativa:
- artefato de sign-off relacionado:
- tracking ao vivo relacionado:
