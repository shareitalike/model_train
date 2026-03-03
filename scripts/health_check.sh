#!/bin/bash
# Kaithi OCR System — Health Check Script
set -e
BASE_URL="${API_URL:-http://localhost}"
FAILED=0

check() {
    local name=$1
    local url=$2
    if curl -sf --max-time 10 "$url" > /dev/null 2>&1; then
        echo "✓ $name"
    else
        echo "✗ $name — FAILED ($url)"
        FAILED=1
    fi
}

echo "═══ Kaithi OCR Health Check ═══"
check "API Health"     "$BASE_URL/api/v1/health"
check "API Docs"       "$BASE_URL/api/docs"
check "Frontend"       "$BASE_URL/"
check "MinIO Console"  "http://localhost:9001"
check "Flower Monitor" "http://localhost:5555"

# PostgreSQL
if docker compose exec -T postgres pg_isready -U kaithi -d kaithi_db > /dev/null 2>&1; then
    echo "✓ PostgreSQL"
else
    echo "✗ PostgreSQL — FAILED"
    FAILED=1
fi

# Redis
if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "✓ Redis"
else
    echo "✗ Redis — FAILED"
    FAILED=1
fi

echo "═══════════════════════════════"
if [ $FAILED -eq 0 ]; then
    echo "All systems operational ✓"
    exit 0
else
    echo "Some services are DOWN"
    exit 1
fi
