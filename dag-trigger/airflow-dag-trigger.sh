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

$0 <Dag ID> <Dag JSON configuration>

Triggers a run of an Airflow DAG.

  Dag ID (required):
    dag_id of an Airflow job (ex. ggircs_cert_renewal)
  Dag JSON configuration:
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

dag_id=$1
dag_config=${2:-'{}'}

echo "Fetching state for DAG $dag_id"

dag_url="$AIRFLOW_ENDPOINT/api/v1/dags/${dag_id}"
is_paused=$(curl -sSf -u "$AIRFLOW_USERNAME":"$AIRFLOW_PASSWORD" $dag_url | jq .is_paused)

if [ "$is_paused" == "true" ]; then
  echo "DAG $dag_id is paused and cannot be run at this time."
  exit 1
fi

dag_run_url="$dag_url/dagRuns"
echo "Triggering DAG run on airflow API at: $dag_run_url"

run_json=$(curl -sSf -u "$AIRFLOW_USERNAME":"$AIRFLOW_PASSWORD" -X POST \
  "$dag_run_url" \
  -H 'Cache-Control: no-cache' \
  -H 'Content-Type: application/json' \
  -d "{\"conf\": $dag_config}")
dag_run_id=$(echo "$run_json" | jq -r .dag_run_id)

echo "Started dag run ID: $dag_run_id"

function get_run_state() {
  dag_state_url="$dag_url/dagRuns/${dag_run_id}"
  curl -sSf -u "$AIRFLOW_USERNAME":"$AIRFLOW_PASSWORD" -X GET \
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
    'running' )
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
