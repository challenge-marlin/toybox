FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG NEXT_PUBLIC_API_BASE
ARG BACKEND_INTERNAL_URL
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
ENV BACKEND_INTERNAL_URL=$BACKEND_INTERNAL_URL
RUN npm run build
ENV PORT=3000
# healthcheck 用に curl を追加
RUN apk add --no-cache curl
EXPOSE 3000
CMD ["npm", "run", "start"]
