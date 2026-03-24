#!/usr/bin/env bash
# Launch backend (FastAPI) and frontend (Vite) in parallel

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting backend..."
(cd "$ROOT/backend" && uvicorn main:app --reload) &
BACK_PID=$!

echo "Starting frontend..."
(cd "$ROOT/frontend" && npm run dev) &
FRONT_PID=$!

echo "Backend PID: $BACK_PID | Frontend PID: $FRONT_PID"
echo "Press Ctrl+C to stop both."

# Stop both on Ctrl+C
trap "kill $BACK_PID $FRONT_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
