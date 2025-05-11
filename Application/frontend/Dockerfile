FROM node:18.19-alpine3.18 AS build

WORKDIR /app

# Add necessary build tools
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./

# Clean install dependencies
RUN npm ci

# Copy application files
COPY . .

# Build application
RUN NODE_ENV=production CI=true npm run build

# Production stage
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 7779

CMD ["nginx", "-g", "daemon off;"]