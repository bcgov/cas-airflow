#!/bin/bash

### Script meant for shipit to set the appropriate environment variables,
### and deploy the helm chart with the required values.
set -euo pipefail

git submodule update --init --quiet
GIT_SHA1=$(git rev-parse HEAD)
export GIT_SHA1

helm dep up ./helm/cas-airflow
helm upgrade --install --timeout 900s \
  --namespace "$AIRFLOW_NAMESPACE_PREFIX-$ENVIRONMENT" \
  -f ./helm/cas-airflow/values.yaml \
  -f "./helm/cas-airflow/values-$ENVIRONMENT.yaml" \
  --set namespaces.airflow="$AIRFLOW_NAMESPACE_PREFIX-$ENVIRONMENT" \
  --set namespaces.ggircs="$GGIRCS_NAMESPACE_PREFIX-$ENVIRONMENT" \
  --set namespaces.ciip="$CIIP_NAMESPACE_PREFIX-$ENVIRONMENT" \
  --set airflow.defaultAirflowTag="$GIT_SHA1" \
  cas-airflow ./helm/cas-airflow


