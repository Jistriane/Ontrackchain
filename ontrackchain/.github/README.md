# 📂 ontrackchain/.github/ · Mirror Compartilhado Configurações de Colaboração

## ⚠️ STATUS: **MIRROR PARA COLABORAÇÃO (NÃO É SSOT CI/CD! WORKFLOWS AQUI NÃO EXECUTAM AUTOMATICAMENTE NO GITHUB)**

Este diretório `.github/` dentro da subpasta `ontrackchain/` **NÃO É LIDO PELO GITHUB** para CI/CD nem configurações de repositório. Ele é usado apenas como **local centralizado de configurações colaborativas compartilhadas** que podem ser copiadas periodicamente para o `.github/` NA RAIZ do repositório (SSOT).

---

## 📋 O que este diretório contém (somente artefatos colaboração não-CI):

| Artefato | Propósito | Pode usar diretamente? |
|---|---|---|
| **`ISSUE_TEMPLATE/`** | 3 templates oficiais de Issue: (1) `01-bug-report.yml`, (2) `02-feature-request.yml`, (3) `03-config.yml`. **Apenas estes templates estão no monorepo.** | ✅ Sim — mas para aparecer no GitHub automaticamente PRECISA estar em `.github/ISSUE_TEMPLATE/` NA RAIZ. Mantemos aqui como SSOT de templates e copiamos para raiz quando atualizamos. |
| **`CODEOWNERS`** | Mapa de ownership por arquivo/diretório para revisões obrigatórias em PRs. | ⚠️ Mesmo caso: para funcionar no GitHub, deve estar em `.github/CODEOWNERS` (raiz). Este aqui é o arquivo mestre. |
| **`dependabot.yml`** | Configuração do Dependabot (atualizações automáticas de dependências). | ⚠️ Dependabot só lê o arquivo em `.github/dependabot.yml` na RAIZ. Este é o SSOT local de configuração. |
| **`PULL_REQUEST_TEMPLATE.md`** | Template PR uppercase versão. | ⚠️ A versão usada pelo GitHub é a da raiz `pull_request_template.md` lowercase. |
| **`workflows/` (10 arquivos YAML LEGADOS)** | Workflows antigos (ci.yml, deploy-production.yml etc). | 🚫 **NÃO USAR — NÃO EXECUTAM no GitHub Actions!** Estão aqui como referência histórica. Quem executa são os 20 workflows da `/.github/workflows/` NA RAIZ. |
| **`settings.yml` (subpasta)** | Cópia antiga de settings. | 🚫 **PROIBIDO USAR COMO SSOT.** O SSOT HC-3 é `/.github/settings.yml` NA RAIZ (G8 valida esse, não este). Alterar este aqui NÃO tem impacto em nada. |

---

## 🚨 AVISO NÃO NEGOCIÁVEL (MESMO DA RAIZ):

> **GITHUB ACTIONS SÓ EXECUTA WORKFLOWS EM: `<REPO_ROOT>/.github/workflows/*.yml`**
>
> Qualquer arquivo de workflow colocado aqui em `ontrackchain/.github/workflows/` **NÃO SERÁ ENCONTRADO**. Isso não é um bug — é comportamento padrão documentado do GitHub. Não perca tempo debugando workflows aqui.
>
> - SSOT CI/CD de workflows → `.github/workflows/` na RAIZ do projeto.
> - SSOT settings HC-3 → `.github/settings.yml` na RAIZ do projeto (validado G8).

---

## 🔍 Fluxo de atualização recomendado:

1. **Edite PRIMEIRO os templates/CODEOWNERS/dependabot aqui** (este diretório é o SSOT colaboração).
2. **Após aprovação, abra sprint dedicada para copiar as versões aprovadas para `.github/` NA RAIZ do repo** — só então as mudanças terão efeito.
3. **NUNCA edite a versão da RAIZ sem passar primeiro por aqui** — evita divergência silenciosa entre SSOT local e SSOT de execução.

---

## 📚 Documentação relacionada:

- Mapa Tiers da Documentação: [`/README.md # Mapa Completo 7 Tiers`](../../README.md#mapa-completo-da-documentação--7-tiers-hierárquicos-sprint-s2867-p4)
- .github/ RAIZ SSOT: [`/.github/README.md`](../../.github/README.md) (diretório real de execução)
- Diretório LEGADO Arquivado: [`/github_main/.github/README.md`](../../github_main/.github/README.md) — NÃO USAR de jeito nenhum.
