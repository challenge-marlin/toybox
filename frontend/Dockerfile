FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
ENV PORT=3000
# healthcheck 用に curl を追加
RUN apk add --no-cache curl
EXPOSE 3000
CMD ["npm", "run", "start"]
