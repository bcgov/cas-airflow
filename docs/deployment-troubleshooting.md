# Airflow upgrade deployment troubleshooting

If DAG tasks are failing for no apparent reason or are giving 401/403 or authentication errors, it may be due to the `cas-airflow-admin` user not updating correctly. You can attempt to fix this by cycling the Airflow pods, or by deleting the `cas-airflow-admin` user and recreating it.

## Cycling the Airflow pods

To cycle the Airflow pods, you can use the following command (replace `airflow-dev` with the namespace you are using):

```bash
oc -n airflow-dev rollout restart deployment cas-airflow-api-server
oc -n airflow-dev rollout restart deployment cas-airflow-dag-processor
oc -n airflow-dev rollout restart deployment cas-airflow-scheduler
```

This will restart the Airflow pods, which may resolve the issue. If not, delete and recreate the `cas-airflow-admin` user as below.

## Recreating the `cas-airflow-admin` user

### Delete the `cas-airflow-admin` user

To delete the `cas-airflow-admin` user, connect to the terminal of one of the airflow pods' (ie. `cas-airflow-api-server-yyyyy-zzzzz`) and run the following command:

```bash
airflow users delete --username "cas-airflow-admin"
```

### Create a new `cas-airflow-admin` user

To recreate the `cas-airflow-admin` user, you can use the following command:

```bash
airflow users create --username "cas-airflow-admin" --firstname admin --lastname user --role Admin --email admin@example.com
```

After this you will be prompted to enter a password for the `cas-airflow-admin` user. Use the password set in the `airflow-default-user-password` secret.
