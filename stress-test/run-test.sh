#!/bin/bash
# Runs the gatling stress test against the api started by ../run-local.sh
#
# Usage: ./run-test.sh "description of the version being tested"
#
# Optional environment variables:
#   PEAK_USERS_PER_SEC   users starting per second at the end of the ramp (default 20)
#   RAMP_SECONDS         duration of the ramp (default 120)
#
# Example requests
# curl -v "http://localhost:8000/auto-complete?term=cas&amount=5"
# curl -v -XPOST -H "content-type: application/json" -d '{"term": "casa"}' "http://localhost:8000/auto-complete/select"
set -euo pipefail

cd "$(dirname "$0")"

DESCRIPTION="${1:-auto-complete}"
GATLING_IMAGE="trie-term-search-gatling"
REQUEST_TIMEOUT_MS=10000

API_CONTAINER=$(docker compose -f ../docker-compose.yml ps -q api)
if [ -z "$API_CONTAINER" ]; then
    echo "ERROR: the api is not running, start it with ../run-local.sh"
    exit 1
fi

echo "==> Building gatling image"
docker build -q -t "$GATLING_IMAGE" . > /dev/null

echo "==> Running stress test: $DESCRIPTION"
# gatling shares the network of the api container, so the api is on localhost:8000
docker run --rm \
    --network "container:$API_CONTAINER" \
    --user "$(id -u):$(id -g)" \
    -e PEAK_USERS_PER_SEC \
    -e RAMP_SECONDS \
    -e JAVA_OPTS="-Dgatling.http.requestTimeout=$REQUEST_TIMEOUT_MS" \
    -v "$PWD/user-files:/user-files" \
    "$GATLING_IMAGE" \
    -rm local -s AutoCompleteSimulation \
    -rd "$DESCRIPTION" \
    -rf /user-files/results \
    -sf /user-files/simulations \
    -rsf /user-files/resources

LAST_RESULT=$(ls -td user-files/results/*/ | head -n 1)
echo
echo "Report: $PWD/${LAST_RESULT}index.html"
