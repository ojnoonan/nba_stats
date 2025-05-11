FROM node:18-alpine AS build

WORKDIR /app

# Add necessary build tools
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./

# Install dependencies with clean npm cache
RUN npm cache clean --force && \
    npm ci

# Copy rest of the app
COPY . .

# Set environment variables for build
ENV NODE_ENV=production
ENV VITE_API_URL=http://backend:7778

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 7779

CMD ["nginx", "-g", "daemon off;"]