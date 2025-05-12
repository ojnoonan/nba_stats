FROM node:18-alpine AS build

# Install curl for healthchecks and other tools
RUN apk add --no-cache curl

WORKDIR /app

# Copy only package files first to leverage caching
COPY package.json package-lock.json ./

# Install dependencies with verbose logging
RUN npm install --verbose && \
    # List installed packages for debugging
    npm list || true

# Copy source files
COPY . .

# Set environment variable and build with detailed logging
ENV VITE_API_URL=http://backend:7778 \
    NODE_ENV=production \
    # Enable more verbose Vite logging
    VITE_LOG_LEVEL=info

# Run build with detailed error output
RUN npm run build || (echo "Build failed. Diagnostic information:" && \
    echo "Node version: $(node -v)" && \
    echo "NPM version: $(npm -v)" && \
    echo "Directory contents:" && \
    ls -la && \
    echo "Package.json contents:" && \
    cat package.json && \
    echo "Error logs:" && \
    cat npm-debug.log* 2>/dev/null || true && \
    exit 1)

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 7779
CMD ["nginx", "-g", "daemon off;"]