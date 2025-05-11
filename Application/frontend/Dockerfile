FROM node:16-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Install serve to serve the static files
RUN npm install -g serve

EXPOSE 7779

CMD ["serve", "-s", "dist", "-l", "7779"]