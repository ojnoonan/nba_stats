FROM node:18-alpine AS build

WORKDIR /app

# Copy only package files first to leverage caching
COPY package.json package-lock.json ./

# Install dependencies without the legacy flag since it worked locally
RUN npm install

# Copy source files
COPY . .

# Set environment variable and build
ENV VITE_API_URL=http://backend:7778
RUN npm run build || (echo "Build failed. Error log:" && ls -la && cat npm-debug.log* 2>/dev/null)

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 7779
CMD ["nginx", "-g", "daemon off;"]