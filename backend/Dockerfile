FROM node:22-alpine AS base
WORKDIR /app
COPY package*.json ./
# 開発中はロックファイルと依存のズレが出やすいので npm install を使用
RUN npm install
COPY . .
RUN npm run build
ENV NODE_ENV=production
# healthcheck 用に curl を追加
RUN apk add --no-cache curl
EXPOSE 4000
CMD ["node", "dist/src/server.js"]
