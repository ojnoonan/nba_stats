FROM node:18-alpine as dependencies

WORKDIR /app
COPY package*.json ./
RUN npm install --prefer-offline --no-audit

FROM node:18-alpine as builder

WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:18-alpine as runner

WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist

EXPOSE 7779
CMD ["serve", "-s", "dist", "-l", "7779", "--no-clipboard"]