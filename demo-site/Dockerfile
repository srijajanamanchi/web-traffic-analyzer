# syntax=docker/dockerfile:1
FROM nginx:1.25-alpine

# Install curl for container healthcheck
RUN apk add --no-cache curl

# Remove default nginx configurations
RUN rm -rf /etc/nginx/conf.d/* /usr/share/nginx/html/*

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy demo site static files
COPY . /usr/share/nginx/html/

# Ensure correct permissions for unprivileged user
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx

# Healthcheck
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/healthz || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
