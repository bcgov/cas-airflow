#!/usr/bin/env bash

dir_path=$(dirname "$(realpath "$0")")

if [ -z "$ENVIRONMENT" ]; then
  echo "The ENVIRONMENT variable is not defined. Exiting."
  exit 1;
fi

if [ -z "$REVISION" ]; then
  echo "The REVISION variable is not defined. Exiting."
  exit 1;
fi

# TODO: get these values from the openshift command line
declare -A uids=( ["wksv3k-dev"]="1009900000" ["wksv3k-test"]="1009960000" ["wksv3k-prod"]="1009930000")

sed -i "s/\(namespace: &namespace\) .*/\1 $ENVIRONMENT/" "$dir_path/values.yaml"
sed -i "s/\(namespace-uid: &namespace-uid\) .*/\1 '${uids[$ENVIRONMENT]}'/" "$dir_path/values.yaml"
sed -i "s/\(gcs-folder: &gcs-folder\) .*/\1 gs:\/\/$ENVIRONMENT-cas-airflow/" "$dir_path/values.yaml"
sed -i "s/\(airflow-tag: &airflow-tag\) .*/\1 $REVISION/" "$dir_path/values.yaml"
