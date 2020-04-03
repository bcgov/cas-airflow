#!/bin/bash
FILE_URLS=$(sh bin/wget-spider.sh | awk '{printf "--url=\"%s\" ",$0}')
node stream-minio --ssl --bucket="$1" $FILE_URLS
