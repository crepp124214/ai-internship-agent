#!/bin/bash
# Compose health check script
# Waits for all services to become healthy before returning success

set -e

COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
TIMEOUT="${TIMEOUT:-120}"
INTERVAL="${INTERVAL:-5}"

echo "Waiting for all services to become healthy (timeout: ${TIMEOUT}s)..."

elapsed=0
while [ $elapsed -lt $TIMEOUT ]; do
    # Check if all services are healthy
    status=$(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null | \
        python3 -c "
import sys, json
services = [json.loads(line) for line in sys.stdin if line.strip()]
healthy = all(s.get('Health', '').startswith('healthy') or s.get('State') == 'running' for s in services)
print('healthy' if healthy else 'unhealthy')
" 2>/dev/null || echo "unhealthy")

    if [ "$status" = "healthy" ]; then
        echo "All services are healthy!"
        docker compose -f "$COMPOSE_FILE" ps
        exit 0
    fi

    echo "  Waiting... (${elapsed}s elapsed)"
    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))
done

echo "ERROR: Services did not become healthy within ${TIMEOUT}s"
docker compose -f "$COMPOSE_FILE" ps
docker compose -f "$COMPOSE_FILE" logs --tail=20
exit 1
