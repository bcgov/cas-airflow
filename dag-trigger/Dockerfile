from alpine:3.21

RUN apk add --no-cache --upgrade bash jq curl

COPY ./airflow-dag-trigger.sh /

RUN chmod +x airflow-dag-trigger.sh

