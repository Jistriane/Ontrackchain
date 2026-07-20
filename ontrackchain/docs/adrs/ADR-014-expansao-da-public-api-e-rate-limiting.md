# ADR-014: Expansão da Public API e Rate Limiting por IP com Cache CDN

## Contexto

A plataforma Ontrackchain necessita expor dados públicos de redes blockchain suportadas (`/public/chains/supported`) e permitir triagem rápida de sanções (`/public/sanctions/check/{address}`) sem exigir autenticação por token privado nem expor a infraestrutura de auditoria interna de tenants.

Para proteger os serviços internos contra degradação por volume excessivo e otimizar latência global, era necessário definir padrões arquiteturais claros de rate-limiting, cinto de segurança por IP e cabeçalhos de borda (CDN).

## Decisão

1. **Isolamento sob Namespace `/public/*`**:
   - Endpoints sob `/public/*` operam em modo somente leitura e sem dependência de headers de tenant (`X-Organization-Id` ou JWT).
2. **Rate Limiting em Camada Redis (`rl:public:<ip>`)**:
   - Cada IP de origem possui limite estrito configurável (padrão: 10 requisições por hora sem credencial).
   - Tentativas acima do limite retornam `429 Too Many Requests` com cabeçalho `Retry-After`.
3. **Otimização de Borda (CDN Cache Control)**:
   - Respostas de leitura pública contêm `Cache-Control: public, max-age=300` e `CDN-Cache-Control: max-age=300`, instruindo provedores de borda (Cloudflare/Fastly/AWS CloudFront) a responderem diretamente da borda para chamadas idênticas.
4. **Degradação Honesta e Fonte de Sanções**:
   - O endpoint `/public/sanctions/check/{address}` consome o cache local sincronizado de sanções (`sanctions_lists_cache`), retornando `provider_status: live` sem acionar chamadas externas síncronas de terceiros.

## Consequências

### Positivas

- Redução drástica da carga em microsserviços internos para consultas públicas recorrentes.
- Proteção contra ataques de negação de serviço (DDoS) através de rate-limiting por IP em nível de middleware.
- Resposta instantânea e previsível para integrações externas pré-onboarding.

### Negativas

- Clientes que compartilham o mesmo IP público (NAT/proxies corporativos) compartilham a mesma cota de rate-limit no plano gratuito/não-autenticado.

## Status

Aprovado e Implementado.
