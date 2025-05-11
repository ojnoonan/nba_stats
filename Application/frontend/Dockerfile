FROM node:18-alpine

WORKDIR /app

# Install build essentials
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./

# Install dependencies with verbose logging
RUN npm install --verbose

# Copy application files
COPY . .

# Set environment variable for more verbose logging
ENV NODE_ENV=development
ENV DEBUG=*

# Run build with max logging
RUN set -x && npm run build || (echo "Build failed with exit code $?" && ls -la && cat npm-debug.log* 2>/dev/null || true && exit 1)

# Install serve
RUN npm install -g serve

EXPOSE 7779

CMD ["serve", "-s", "dist", "-l", "7779", "--no-clipboard"]