FROM node:18-slim as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM ubuntu:22.04

# Install nginx-extras
RUN apt-get update && apt-get install -y nginx-extras && rm -rf /var/lib/apt/lists/*

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create symbolic link to enable the site
RUN ln -s /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/

# Remove default nginx config
RUN rm /etc/nginx/sites-enabled/default

# Expose port
EXPOSE 7779

# Start nginx
CMD ["nginx", "-g", "daemon off;"]