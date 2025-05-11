# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with exact versions
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Add non-root user and install curl for healthcheck
RUN apk add --no-cache curl && \
    adduser -D -u 1000 appuser && \
    mkdir -p /var/cache/nginx && \
    chown -R appuser:appuser /var/cache/nginx

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Set proper permissions
RUN chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /etc/nginx/conf.d

# Switch to non-root user
USER appuser

EXPOSE 7779

CMD ["nginx", "-g", "daemon off;"]