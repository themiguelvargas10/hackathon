#!/usr/bin/env sh
cd "$(dirname "$0")" || exit 1
if command -v python3.12 >/dev/null 2>&1; then
  exec python3.12 server.py
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' || exit 1
exec python3 server.py
