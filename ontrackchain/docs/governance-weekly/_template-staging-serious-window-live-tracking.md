# Tracking ao Vivo da Janela Seria — <window_id>

## Contexto Operacional

- data:
- window_id:
- mode:
- environment_name:
- facilitador:
- status global: `pre-start` | `in_progress` | `blocked` | `completed`
- checkpoint atual:
- ultima atualizacao:
- cadencia de atualizacao recomendada: `15 min`

## Status Permitidos

- trilha: `pending` | `in_progress` | `blocked` | `ready` | `done` | `waived`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- decisao recomendada: `pending_no_go` | `pending_go_with_exception` | `pending_go` | `approved`

## Painel de Trilhas

- `Platform/Operations`
  - status atual: `pending`
  - responsavel online: `<nome_owner_online>`
  - canal de contato: `<slack_ou_teams_canal>`
  - ack do owner: `yes` | `no`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - ultimo checkpoint: `<checkpoint_anterior>`
  - proximo checkpoint: `<proximo_checkpoint>`
  - hora do proximo checkpoint: `<HH:MMZ>`
  - ETA desbloqueio: `<15 min | 30 min | 60 min | >60 min>`
  - dependencia ativa: `<secret_ou_gate_ativo>`
  - bridge de escalacao: `<canal_bridge_ou_incident_room>`
  - observacoes: `<observacao_curta>`
- `Auth/OIDC`
  - status atual: `pending`
  - responsavel online: `<nome_owner_online>`
  - canal de contato: `<slack_ou_teams_canal>`
  - ack do owner: `yes` | `no`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - ultimo checkpoint: `<checkpoint_anterior>`
  - proximo checkpoint: `<proximo_checkpoint>`
  - hora do proximo checkpoint: `<HH:MMZ>`
  - ETA desbloqueio: `<15 min | 30 min | 60 min | >60 min>`
  - dependencia ativa: `<secret_ou_gate_ativo>`
  - bridge de escalacao: `<canal_bridge_ou_incident_room>`
  - observacoes: `<observacao_curta>`
- `Investigation/RPC`
  - status atual: `pending`
  - responsavel online: `<nome_owner_online>`
  - canal de contato: `<slack_ou_teams_canal>`
  - ack do owner: `yes` | `no`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - ultimo checkpoint: `<checkpoint_anterior>`
  - proximo checkpoint: `<proximo_checkpoint>`
  - hora do proximo checkpoint: `<HH:MMZ>`
  - ETA desbloqueio: `<15 min | 30 min | 60 min | >60 min>`
  - dependencia ativa: `<secret_ou_gate_ativo>`
  - bridge de escalacao: `<canal_bridge_ou_incident_room>`
  - observacoes: `<observacao_curta>`
- `Compliance/AML`
  - status atual: `pending`
  - responsavel online: `<nome_owner_online>`
  - canal de contato: `<slack_ou_teams_canal>`
  - ack do owner: `yes` | `no`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - ultimo checkpoint: `<checkpoint_anterior>`
  - proximo checkpoint: `<proximo_checkpoint>`
  - hora do proximo checkpoint: `<HH:MMZ>`
  - ETA desbloqueio: `<15 min | 30 min | 60 min | >60 min>`
  - dependencia ativa: `<secret_ou_gate_ativo>`
  - bridge de escalacao: `<canal_bridge_ou_incident_room>`
  - observacoes: `<observacao_curta>`
- `Gate Agregado da Janela`
  - status atual: `pending`
  - responsavel online: `<nome_owner_online>`
  - canal de contato: `<slack_ou_teams_canal>`
  - ack do owner: `yes` | `no`
  - ultima atualizacao: `<YYYY-MM-DDTHH:MM:SSZ>`
  - ultimo checkpoint: `<checkpoint_anterior>`
  - proximo checkpoint: `<proximo_checkpoint>`
  - hora do proximo checkpoint: `<HH:MMZ>`
  - ETA desbloqueio: `<15 min | 30 min | 60 min | >60 min>`
  - dependencia ativa: `<secret_ou_gate_ativo>`
  - bridge de escalacao: `<canal_bridge_ou_incident_room>`
  - observacoes: `<observacao_curta>`

## Linha do Tempo

- `HH:MM`:
  - trilha:
  - evento:
  - impacto:
  - owner: `<nome_owner_online>`
  - canal: `<slack_ou_teams_canal>`

## Bloqueadores em Curso

- ID:
  - trilha:
  - status:
  - owner da escalacao: `<nome_owner_escalacao>`
  - canal da escalacao: `<bridge_de_escalacao>`
  - ETA: `<HH:MMZ ou 30 min>`
  - observacao: `<observacao_curta>`

## Decisoes Operacionais

- decisao registrada:

## Hand-off para Sign-Off

- war room:
- sign-off:
- decisao recomendada:
- owner do proximo passo: `<nome_owner_online>`
- canal do proximo passo: `<slack_ou_teams_canal>`
