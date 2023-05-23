# Downgrading Airflow Version
Sometimes after deploying a newer version of Airflow, we need to revert back to an older version. Simply changing the version in our helm charts and deploy scripts is not enough because Airflow uses Alembic as a database migration tool. Alembic keeps track of IDs that track the changes to the schema for each version. When trying to downgrade versions, the migration will fail because it's expecting an ID after the current migration ID. This can cause the downgrade to fail because the database can't get its schema back into the desired state and will throw an error like `no revision found with id 123456`

## Steps to downgrade
- Update the Airflow version to the target version in:
  -  Dockerfile
  -  run_local.sh
  -  Chart.yaml
  -  values.yaml
- Before deploying the changes to openshift:
  - From the webserver pod's terminal run: `airflow db downgrade --to-version=<target version>`
  - This will revert the database schema to align with the target downgraded version of airflow
- Deploy the changes
