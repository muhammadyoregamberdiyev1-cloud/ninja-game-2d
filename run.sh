#!/usr/bin/env sh
# Serve Shadow Ninja locally (default http://localhost:8000)
cd "$(dirname "$0")"
exec python3 -m http.server "${PORT:-8000}"
