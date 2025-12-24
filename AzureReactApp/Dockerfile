# ===== build stage =====
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
COPY vite.config.* tsconfig*.json ./
COPY index.html ./
COPY src ./src
COPY public ./public

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm install
RUN npm run build

# ===== runtime stage =====
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
