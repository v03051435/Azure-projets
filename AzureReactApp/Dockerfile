# ---------- build stage ----------
FROM node:18-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

# ---------- runtime stage ----------
FROM nginx:alpine

# envsubst 在 gettext 里
RUN apk add --no-cache gettext

COPY --from=build /app/dist /usr/share/nginx/html

# Keep a template of the runtime config for envsubst (used by entrypoint and dev)
COPY --from=build /app/public/config/config.json /etc/app/config.template.json

# 确保 config 文件存在（来自 public/config/config.json）
# dist/config/config.json

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
