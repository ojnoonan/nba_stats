# Build stage
FROM node:18-alpine

WORKDIR /app

# Install essential build tools
RUN apk add --no-cache python3 make g++ gcc

# Copy only package files first
COPY package.json ./

# Clear npm cache and install dependencies with minimal configuration
RUN npm cache clean --force && \
    npm install --production=false

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 7779

CMD ["nginx", "-g", "daemon off;"]