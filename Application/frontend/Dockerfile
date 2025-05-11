FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

# Build the app
RUN npm run build

# Install serve
RUN npm install -g serve

EXPOSE 7779

# Start the app
CMD ["serve", "-s", "dist", "-l", "7779"]