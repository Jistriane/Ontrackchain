FROM node:20-alpine AS base

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

FROM base AS deps

COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json

RUN npm ci --include=dev --no-audit --no-fund

FROM deps AS source

COPY tsconfig.json /app/tsconfig.json
COPY next-env.d.ts /app/next-env.d.ts
COPY global.d.ts /app/global.d.ts
COPY app /app/app
COPY components /app/components
COPY public /app/public

FROM source AS dev

EXPOSE 3000

CMD ["npm", "run", "dev"]

FROM source AS builder

RUN npm run build

FROM base AS runtime-deps

COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json

RUN npm ci --omit=dev --no-audit --no-fund

FROM base AS runtime

ENV NODE_ENV=production

COPY --from=runtime-deps /app/node_modules /app/node_modules
COPY --from=builder /app/.next /app/.next
COPY --from=builder /app/public /app/public
COPY --from=builder /app/package.json /app/package.json

EXPOSE 3000

CMD ["npm", "run", "start"]
