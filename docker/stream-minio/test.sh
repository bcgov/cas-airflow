#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <bucket_name>"
    exit 0
fi

node remove-bucket-minio --ssl --bucket="$1"

./bin/wget-spider.sh >.list
COUNT1=$(cat .list | wc -l)
COUNT2=$(./init.sh "$1" .list | grep -c uploading)
COUNT3=$(./init.sh "$1" .list | grep -c skipping)
rm .list

node remove-bucket-minio --ssl --bucket="$1"

if [ "$COUNT1" -ne "$COUNT2" ]; then
    echo "failed"
    exit 1
fi
if [ "$COUNT1" -ne "$COUNT3" ]; then
    echo "failed"
    exit 1
fi
exit 1
echo "passed"
