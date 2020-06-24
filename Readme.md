# CAS Airflow

Configuration of [Apache Airflow](https://airflow.apache.org/) for the Climate Action Secretariat projects.

This repository contains the docker images, helm charts, and DAGs required to automate various workflows for the CAS team.

## DAGs

The dags directory contains the various workflows (Directed Acyclic Graphs)

### Running tasks using the Kubernetes executor and KubernetesPodOperator

- The Kubernetes Executor allows us to run tasks on Kubernetes as Pods.
  - It gives us benefits to run one script inside one container within its own quota, and to schedule to the least-congested node in the cluster.
- The KubernetesPodOperator allows us to create Pods on Kubernetes.
  - It gives us the freedom to run the command in any arbitrary image, sandboxing the job run inside a docker container.
- [`Airflow Kubernetes`](https://airflow.apache.org/docs/stable/kubernetes.html 'Airflow Kubernetes')

## CI/CD

The docker images are built on CircleCI for every commit, and pushed to this repository's GitHub registry if the build occurs on the `develop` or `master` branch, or if the commit is tagged.

Deployement is done with Shipit, using the helm charts defined in the `helm` folder

There are a couple manual steps required for installation (the first deployment) at the moment:

1. Prior to deploying, the namespace where airflow is deployed should have a "github-registry" secret, containing the pull secrets to the docker registry

1. Deploy with shipit

1. The admin user should be created manually, by opening a terminal in the cas-airflow-web pod, and running the following commands:

`export AIRFLOW__CORE__SQL_ALCHEMY_CONN="postgresql+psycopg2://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"`

In a Python terminal:

```python
import airflow
from airflow import models, settings
from airflow.contrib.auth.backends.password_auth import PasswordUser
user = PasswordUser(models.User())
user.username = 'cas-airflow-admin'
user.email = 'new_user_email@example.com'
user.password = '<password stored in button vault>'
user.superuser = True
session = settings.Session()
session.add(user)
session.commit()
session.close()
exit()

```

1. The connections required in the various dags need to be manually created

## TODO

- [ ] stream-minio should be replaced to use gcs client
- [ ] the docker images should be imported in the cluster instead of pulling from GH every time we spin up a pod
- [ ] authentication should be done with GitHub (allowing members of https://github.com/orgs/bcgov/teams/cas-developers)
- [ ] automate the creation of connections on installation


## Contributing
### Cloning

It's important that this repository be cloned to the default airflow home folder of `~/airflow`.

```bash
git clone git@github.com:bcgov/cas-airflow.git ~/airflow && cd $_
```

### Getting started

Use [asdf](https://asdf-vm.com/#/core-manage-asdf-vm) to install the correct version of python.

```bash
asdf install
```

Use [pip](https://pip.pypa.io/en/stable/user_guide/) to install the correct version of airflow.

```bash
pip install -r requirements.txt
```

Then reshim asdf to ensure the correct version of airflow is in your path.

```bash
asdf reshim
```

Be sure to set the `$AIRFLOW_HOME` environment variably if you cloned this repo to a path other than `~/airflow`.

```bash
airflow initdb
```

Start airflow locally (optional).

```bash
airflow webserver --daemon
airflow scheduler --daemon
```

### Writing

Run a specific task in a specific dag.

```
airflow test hello_world_dag hello_task $(date -u +"%Y-%m-%dT%H:%M:%SZ")
```
