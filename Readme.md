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
  - It allows us to select in which namespace to run the job.
- [`Airflow Kubernetes`](https://airflow.apache.org/docs/stable/kubernetes.html "Airflow Kubernetes")

## CI/CD

The docker images are built on CircleCI for every commit, and pushed to CAS' google cloud registry if the build occurs on the `develop` or `master` branch, or if the commit is tagged.

Deployement is done with Shipit, using the helm charts defined in the `helm` folder

- the `helm install` command should specify namespaces for the different CAS applications: `helm install --set namespaces.airflow=<< >> --set namespaces.ggircs=<< >> --set namespaces.ciip=<< >> --set namespaces.cif=<< >>`

There are a couple manual steps required for installation (the first deployment) at the moment:

1. Prior to deploying, the namespace where airflow is deployed should have:

- A "github-registry" secret, containing the pull secrets to the docker registry. This should be taken care of by [cas-pipeline](https://github.com/bcgov/cas-pipeline/)'s `make provision`.
- An "airflow-default-user-password" secret. This will have airflow create a 'cas-aiflow-admin' user with this password.

2. Deploy with shipit

3. The connections required in the various dags need to be manually created

## TODO

- [ ] stream-minio should be replaced to use gcs client
- [ ] the docker images should be imported in the cluster instead of pulling from GH every time we spin up a pod
- [ ] authentication should be done with GitHub (allowing members of https://github.com/orgs/bcgov/teams/cas-developers)
- [ ] automate the creation of connections on installation

## Contributing

### Cloning

```bash
git clone git@github.com:bcgov/cas-airflow.git ~/cas-airflow && cd $_
git submodule update --init
```

This repository contains the DAGs as well as the helm chart.
It submodules airflow through the cas-airflow-upstream repository, to use its helm chart as a dependency - and will eventually reference the official airflow instead.

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

Be sure to set the `$AIRFLOW_HOME` environment variable if this repository was cloned to a path other than `~/airflow`.

```bash
airflow db init
airflow users create -r Admin -u <<username>> -e <<email>> -f <<first name>> -l <<last name>> -p <<password>>
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
