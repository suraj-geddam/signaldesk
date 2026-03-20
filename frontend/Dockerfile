FROM node:24-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM caddy:2-alpine

WORKDIR /srv

COPY --from=build /app/dist ./
COPY Caddyfile /etc/caddy/Caddyfile
