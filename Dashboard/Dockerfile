FROM node:20-alpine AS build

WORKDIR /app

ARG NUXT_PUBLIC_API_BASE=/api/v1
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE
ENV DISABLE_NUXT_HUB=true \
    NUXT_SSR=false \
    NODE_OPTIONS=--max-old-space-size=4096

COPY package*.json ./
COPY pnpm-lock.yaml .npmrc ./
RUN corepack enable \
    && corepack prepare pnpm@9.15.2 --activate \
    && pnpm install --frozen-lockfile

COPY . .
RUN pnpm run generate

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
