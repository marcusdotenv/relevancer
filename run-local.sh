#!/bin/bash
# Starts the whole stack locally and leaves it ready to be queried:
#   1. builds and starts the containers
#   2. waits for the term file to be loaded into the localstack bucket
#   3. waits for the api to answer
#   4. runs the pipeline, which builds the suggestions of every prefix from the term file and loads them into redis
set -euo pipefail

cd "$(dirname "$0")"

API_URL="http://localhost:8000"
API_LOG="/var/log/api-python.log"
PIPELINE_DONE_MESSAGE="loaded on suggestion cache"

show_api_log_and_exit() {
    echo "ERROR: $1"
    echo "--- last lines of the api log ---"
    docker compose exec -T api tail -n 40 "$API_LOG" || docker compose logs --tail 40 api
    exit 1
}

count_pipeline_runs() {
    docker compose exec -T api grep -c "$PIPELINE_DONE_MESSAGE" "$API_LOG" || true
}

echo "==> Building and starting containers"
docker compose up -d --build

echo "==> Waiting for the term file to be loaded into localstack"
if ! docker compose wait localstack-infra-starter > /dev/null; then
    docker compose logs --tail 40 localstack-infra-starter
    echo "ERROR: could not load the term file into localstack"
    exit 1
fi

echo "==> Waiting for the api"
for attempt in $(seq 1 60); do
    if curl -sf -o /dev/null "$API_URL/docs"; then
        break
    fi
    if [ "$attempt" -eq 60 ]; then
        show_api_log_and_exit "api did not answer on $API_URL"
    fi
    sleep 2
done

echo "==> Running the pipeline to load the suggestions into redis"
runs_before=$(count_pipeline_runs)
curl -sf -o /dev/null -X POST "$API_URL/pipeline" || show_api_log_and_exit "POST /pipeline failed"

for attempt in $(seq 1 90); do
    if [ "$(count_pipeline_runs)" -gt "$runs_before" ]; then
        break
    fi
    if [ "$attempt" -eq 90 ]; then
        show_api_log_and_exit "pipeline did not finish"
    fi
    sleep 2
done

echo
echo "Ready. Prefixes in redis: $(docker compose exec -T cache redis-cli hlen suggestions)"
echo
echo "Try it:"
echo "  curl '$API_URL/auto-complete?term=cas&amount=5'"
echo "  curl -X POST '$API_URL/auto-complete/select' -H 'Content-Type: application/json' -d '{\"term\": \"casa\"}'"
echo "  docs:    $API_URL/docs"
echo "  grafana: http://localhost:3000 (dev/dev)"
echo "  stop:    docker compose down"
