# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Add build essentials
RUN apk add --no-cache python3 make g++ gcc

# Copy package files and install dependencies
COPY package*.json ./
COPY postcss.config.cjs ./
COPY tailwind.config.js ./

# Install all dependencies
RUN npm install postcss postcss-import tailwindcss autoprefixer --save-dev && \
    npm install

# Copy the rest of the application
COPY . .

# Set environment for build
ENV NODE_ENV=production
ENV VITE_API_URL=http://backend:7778

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