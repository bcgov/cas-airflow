# Airflow DAG trigger chart

This chart creates a job that allows the user to trigger a DAG on a remote Airflow instance, with a set of parameters.

## Parameters

The following table lists the configurable parameters of the DAG trigger chart and their default values.

| Parameter               | Description                                                  | Default                                                |     |
| :---------------------- | :----------------------------------------------------------- | :----------------------------------------------------- | :-- |
| `airflowEndpoint`       | Endpoint (URL) of the airflow instance to use                | `https://cas-airflow-dev.apps.silver.devops.gov.bc.ca` |     |
| `dagId`                 | The ID of the DAG to run, must exist on the airflow instance | `null`                                                 |     |
| `dagConfiguration`      | Extra configuration for the dag run, in JSON format          | `"{}"`                                                 |     |
| `helm.hook`             | Helm hook setting for the DAG run job                        | `pre-upgrade,pre-install`                              |     |
| `helm.hookWeight`       | Helm hook weight setting for the DAG run job                 | `0`                                                    |     |
| `airflowSecret.name`    | Name of the secret containing the airflow password           | `airflow-default-user-password`                        |     |
| `airflowSecret.key`     | Key of the secret containing the airflow password            | `default-user-pass`                                    |     |
| `image.repository`      | Repository for the image containing the job                  | `artifacts.developer.gov.bc.ca/google-docker-remote/ggl-cas-storage/cas-airflow-dag-trigger`       |     |
| `image.tag`             | Tag for the image containing the job                         | `0.0.1`                                                |     |
| `image.pullPolicy`      | Pull Policy for the image containing the job                 | `Always`                                               |     |
| `activeDeadlineSeconds` | Pull Policy for the image containing the job                 | `1200`                                                 |     |
