FROM node:18.17.1-alpine3.18

WORKDIR /app

# Copy only package files first
COPY package.json package-lock.json ./

# Install only production dependencies
RUN npm ci --only=production

# Copy source files
COPY . .

# Install dev dependencies needed for build
RUN npm install --only=dev

# Build
RUN npm run build

# Use a clean image for production
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 7779
CMD ["nginx", "-g", "daemon off;"]