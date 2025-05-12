FROM node:18-alpine AS build

WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install all dependencies including dev dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Build the application
RUN NODE_ENV=production npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 7779
CMD ["nginx", "-g", "daemon off;"]