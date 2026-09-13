FROM node:26.8.2-alpine@sha256:ef24c5053d50fdc3e4e56eb4e7ddb7861874ab0fdc797046ba897581deb8e868 AS base
# corepack ya no se distribuye con Node en esta imagen; instalamos pnpm
# directamente con la versión fijada.
RUN npm install --global pnpm@11.1.3
WORKDIR /workspace

FROM base AS dependencies
COPY .npmrc package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/shared/package.json ./packages/shared/package.json
RUN pnpm install --frozen-lockfile

FROM base AS builder
COPY --from=dependencies /workspace/node_modules ./node_modules
COPY .npmrc package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web ./apps/web
COPY packages/shared ./packages/shared
RUN pnpm --filter @motorscope/web build

FROM node:26.8.2-alpine@sha256:ef24c5053d50fdc3e4e56eb4e7ddb7861874ab0fdc797046ba897581deb8e868 AS runtime
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000
WORKDIR /app
COPY --from=builder --chown=node:node /workspace/apps/web/.next/standalone ./
COPY --from=builder --chown=node:node /workspace/apps/web/.next/static ./apps/web/.next/static
# El runtime ejecuta node apps/web/server.js desde el bundle standalone; npm
# y corepack del sistema no se usan y arrastran dependencias vendorizadas
# (tar, ip-address, brace-expansion) que dispara Trivy.
RUN rm -rf /usr/local/lib/node_modules/npm \
    /usr/local/bin/npm \
    /usr/local/bin/npx \
    /usr/local/bin/corepack
USER node
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
