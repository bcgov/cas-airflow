#!/bin/bash

### Script meant for shipit to set the appropriate environment variables,
### and deploy the helm chart with the required values.
set -euo pipefail

git_sha1=$(git rev-parse HEAD)

helm dep up ./helm/cas-airflow
helm upgrade --install --timeout 900s \
  --namespace "$AIRFLOW_NAMESPACE_PREFIX-$ENVIRONMENT" \
  -f ./helm/cas-airflow/values.yaml \
  -f "./helm/cas-airflow/values-$ENVIRONMENT.yaml" \
  --set namespaces.airflow="$AIRFLOW_NAMESPACE_PREFIX-$ENVIRONMENT" \
  --set namespaces.ggircs="$GGIRCS_NAMESPACE_PREFIX-$ENVIRONMENT" \
  --set namespaces.ciip="$CIIP_NAMESPACE_PREFIX-$ENVIRONMENT" \
  --set airflow.defaultAirflowTag="$git_sha1" \
  cas-airflow ./helm/cas-airflow


