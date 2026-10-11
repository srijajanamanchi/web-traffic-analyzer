# syntax=docker/dockerfile:1
# --- Build Stage ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- Runtime Stage ---
FROM nginx:1.25-alpine AS runner

RUN apk add --no-cache curl

RUN rm -rf /etc/nginx/conf.d/* /usr/share/nginx/html/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html

RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/healthz || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
