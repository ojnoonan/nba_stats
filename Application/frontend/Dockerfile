# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Set npm configuration for more reliability and better error reporting
ENV NODE_ENV=production
ENV NPM_CONFIG_LOGLEVEL=verbose

# Copy package files
COPY package*.json ./

# Install dependencies with clean slate and increased memory
RUN npm config set registry https://registry.npmjs.org/ && \
    npm cache clean --force && \
    npm install --no-audit --no-fund --verbose

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 7779

CMD ["nginx", "-g", "daemon off;"]