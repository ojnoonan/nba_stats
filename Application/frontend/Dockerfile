FROM node:18-alpine AS build

WORKDIR /app

# Add build essentials
RUN apk add --no-cache python3 make g++ gcc

# Copy package files
COPY package*.json ./

# Install dependencies with CI mode and verbose logging
RUN npm install --verbose

# Copy the rest of the application
COPY . .

# Build the application with verbose logging
RUN npm run build --verbose

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 7779

CMD ["nginx", "-g", "daemon off;"]