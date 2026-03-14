#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL=${API_BASE_URL:-${1:-}}
if [ -z "$API_BASE_URL" ]; then
  echo "Usage: API_BASE_URL=https://api.example.com $0"
  exit 1
fi

TOKEN=${SMOKE_BEARER_TOKEN:-}
AUTH_HEADER=()
if [ -n "$TOKEN" ]; then
  AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
fi

echo "== ServantX backend smoke =="
echo "API: $API_BASE_URL"

echo "-- /health"
curl -fsS "$API_BASE_URL/health" | tee /tmp/servantx-health.json

echo
if [ -n "$TOKEN" ]; then
  echo "-- /projects/ensure-default"
  curl -fsS -X POST "${AUTH_HEADER[@]}" "$API_BASE_URL/projects/ensure-default" | tee /tmp/servantx-project.json
  echo
else
  echo "Skipping authenticated project smoke (set SMOKE_BEARER_TOKEN to enable)"
fi

echo "Backend smoke completed"
