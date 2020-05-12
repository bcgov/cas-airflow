#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <bucket_name>"
    exit 0
fi

echo "download jq for test result assertions"
wget -O jq https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64
chmod +x ./jq

node remove-bucket-minio --ssl --bucket="$1"

./bin/wget-spider.sh >.list
cat .list

num_files=$(wc -l < .list)
./init.sh "$1" .list
echo '/airflow/xcom/return.json'
cat /airflow/xcom/return.json
num_files_uploaded=$(./jq '.uploadedObjects | length' /airflow/xcom/return.json)
echo "$num_files_uploaded"
./init.sh "$1" .list
echo '/airflow/xcom/return.json'
cat /airflow/xcom/return.json
num_files_skipped=$(./jq '.skippedUrls | length' /airflow/xcom/return.json)
echo "$num_files_skipped"
rm .list
rm /airflow/xcom/return.json
node remove-bucket-minio --ssl --bucket="$1"


if [ "$num_files" -ne "$num_files_uploaded" ]; then
    echo "failed"
    exit 1
fi
if [ "$num_files" -ne "$num_files_skipped" ]; then
    echo "failed"
    exit 1
fi
echo "passed"
