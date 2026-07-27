# Frontend Dockerfile — Ephemeral Intent Synthesis System
# Multi-stage build: node builder → nginx runtime

# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

# Accept VITE_ build-time env vars from docker-compose args
ARG VITE_BACKEND_HOST=localhost
ARG VITE_BACKEND_PORT=8000
ARG VITE_BACKEND_PROTOCOL=http
ARG VITE_WS_PROTOCOL=ws
ENV VITE_BACKEND_HOST=$VITE_BACKEND_HOST \
    VITE_BACKEND_PORT=$VITE_BACKEND_PORT \
    VITE_BACKEND_PROTOCOL=$VITE_BACKEND_PROTOCOL \
    VITE_WS_PROTOCOL=$VITE_WS_PROTOCOL

# Install dependencies first (better layer caching)
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Made with Bob
