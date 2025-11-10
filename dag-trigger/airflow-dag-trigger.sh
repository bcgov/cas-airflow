#!/usr/bin/env bash

set -euo pipefail

# =============================================================================
# Usage:
# -----------------------------------------------------------------------------
usage() {
    cat << EOF

Required env variables:

AIRFLOW_ENDPOINT
AIRFLOW_USERNAME
AIRFLOW_PASSWORD

$0 <Dag ID> <Base64-encoded Dag JSON configuration>

Triggers a run of an Airflow DAG.

  Dag ID (required):
    dag_id of an Airflow job (ex. ggircs_cert_renewal)
  Base64-encoded Dag JSON configuration:
    conf object for https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/post_dag_run

  Options
    -h
      Prints this message

EOF
}

if [ "$#" -lt 1 ]; then
    echo "Passed $# parameters. Expected 1 or 2."
    usage
    echo "exiting with status 1"
    exit 1
fi

if [ "$1" = '-h' ]; then
    usage
    exit 0
fi

_curl() {
  curl --retry 5 --retry-all-errors -sSf "$@"
}

# APIv1 is depricated in Airflow 3, but the script still needs to be used in Airflow 2
function detect_api_version() {
  v2_status=$(_curl "$AIRFLOW_ENDPOINT/api/v2/version" -o /dev/null -w "%{http_code}" || echo "fail")
  if [ "$v2_status" = "200" ]; then
    echo "v2"
    return
  fi
  v1_status=$(_curl "$AIRFLOW_ENDPOINT/api/v1/version" -o /dev/null -w "%{http_code}" || echo "fail")
  if [ "$v1_status" = "200" ]; then
    echo "v1"
    return
  fi
  echo "none"
}

AIRFLOW_API_VERSION=$(detect_api_version)
if [ "$AIRFLOW_API_VERSION" = "none" ]; then
  echo "No supported Airflow API found at $AIRFLOW_ENDPOINT"
  exit 1
fi

dag_id=$1
dag_config=$(echo "${2:-'e30K'}" | base64 -d) # e30K is the base64 encoding of '{}'

echo "Detected Airflow API version: $AIRFLOW_API_VERSION"
echo "Fetching state for DAG $dag_id"

if [ "$AIRFLOW_API_VERSION" = "v2" ]; then
  dag_url="$AIRFLOW_ENDPOINT/api/v2/dags/${dag_id}"
  # Get a JWT token for the user
  jwt_token=$(curl -X POST ${AIRFLOW_ENDPOINT}/auth/token \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$AIRFLOW_USERNAME\", \"password\": \"$AIRFLOW_PASSWORD\"}" \
    | jq -r .access_token)
  auth_params=(-H "Authorization: Bearer $jwt_token")
  extra_arguments="\"logical_date\": null, "
elif [ "$AIRFLOW_API_VERSION" = "v1" ]; then
  dag_url="$AIRFLOW_ENDPOINT/api/v1/dags/${dag_id}"
  auth_params=(-u "$AIRFLOW_USERNAME:$AIRFLOW_PASSWORD")
  extra_arguments=""
fi

is_paused=$(_curl "${auth_params[@]}" "$dag_url" | jq .is_paused)

if [ "$is_paused" == "true" ]; then
  echo "DAG $dag_id is paused and cannot be run at this time."
  exit 1
fi

dag_run_url="$dag_url/dagRuns"
echo "Triggering DAG run on airflow API at: $dag_run_url"

run_json=$(_curl "${auth_params[@]}" -X POST \
  "$dag_run_url" \
  -H 'Cache-Control: no-cache' \
  -H 'Content-Type: application/json' \
  -d "{$extra_arguments\"conf\": $dag_config}")
dag_run_id=$(echo "$run_json" | jq -r .dag_run_id)

echo "Started dag run ID: $dag_run_id"

function get_run_state() {
  dag_state_url="$dag_url/dagRuns/${dag_run_id}"
  _curl "${auth_params[@]}" -X GET \
    "$dag_state_url" \
    -H 'Cache-Control: no-cache' \
    -H 'Content-Type: application/json' \
    -d '{}' \
    | jq -r .state
}

while true; do
  state=$(get_run_state)
  echo "DAG $dag_id state: $state"
  case $state in
    'success' )
      echo "DAG succeeded"
      exit 0
      ;;
    'running' | 'queued' )
      echo '...waiting 10 seconds'
      sleep 10
      ;;
    'failed' )
      echo 'DAG failed'
      exit 1
      ;;
    *error* )
      echo "$state"
      exit 1
      ;;
    * )
      echo "Bad response format:"
      echo "$state"
      exit 1
      ;;
  esac
done
