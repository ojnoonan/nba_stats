FROM node:18-alpine AS build

WORKDIR /app

# Add build essentials and git (needed for some npm packages)
RUN apk add --no-cache python3 make g++ gcc git

# Copy package files
COPY package*.json ./

# Clean install dependencies with legacy peer deps
RUN npm clean-install --legacy-peer-deps

# Copy the rest of the application
COPY . .

# Set production environment
ENV NODE_ENV=production

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 7779

CMD ["nginx", "-g", "daemon off;"]