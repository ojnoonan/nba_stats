FROM node:18-alpine AS build

WORKDIR /app

# Add build essentials and git (needed for some npm packages)
RUN apk add --no-cache python3 make g++ gcc git

# Copy package files
COPY package*.json ./

# Clear npm cache and install dependencies with specific flags
RUN npm cache clean --force && \
    npm install --no-optional --legacy-peer-deps

# Copy the rest of the application
COPY . .

# Set production environment
ENV NODE_ENV=production

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 7779

CMD ["nginx", "-g", "daemon off;"]