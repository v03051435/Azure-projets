#!/bin/sh
set -e

# API_BASE_URL 必须存在
if [ -z "$API_BASE_URL" ]; then
  echo "ERROR: API_BASE_URL env var is not set"
  exit 1
fi

CONFIG_PATH="/usr/share/nginx/html/config/config.json"

# Use envsubst to replace placeholders for both variables in one pass
export API_BASE_URL
export VITE_ENV
envsubst '${API_BASE_URL} ${VITE_ENV}' < "$CONFIG_PATH" > "${CONFIG_PATH}.tmp"
mv "${CONFIG_PATH}.tmp" "$CONFIG_PATH"

echo "Runtime config injected: API_BASE_URL=$API_BASE_URL"
echo "Runtime config injected: VITE_ENV=$VITE_ENV (may be empty)"

exec nginx -g "daemon off;"
