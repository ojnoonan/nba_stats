FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --production=false

# Copy source files
COPY . .

# Set environment variable
ENV VITE_API_URL=http://backend:7778

# Run build with detailed logging
RUN set -x && \
    echo "Starting build process..." && \
    npm run build --verbose || { \
        echo "Build failed!" && \
        echo "Node version: $(node -v)" && \
        echo "NPM version: $(npm -v)" && \
        echo "Directory listing:" && \
        ls -la && \
        echo "Build logs:" && \
        find . -name "*.log" -exec cat {} \; && \
        exit 1; \
    }

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 7779
CMD ["nginx", "-g", "daemon off;"]