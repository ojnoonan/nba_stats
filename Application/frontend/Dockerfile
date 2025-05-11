# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Add python and build tools needed for some npm packages
RUN apk add --no-cache python3 make g++ gcc

# First copy only package files to leverage Docker cache
COPY package.json ./

# Install dependencies with clean npm install
RUN npm install --legacy-peer-deps

# Copy the rest of the application code
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