from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator

kubernetes_min_pod = KubernetesPodOperator(
    # The ID specified for the task.
    task_id='pod-ex-minimum',
    # Name of task you want to run, used to generate Pod ID.
    name='pod-ex-minimum',
    # Entrypoint of the container, if not specified the Docker container's
    # entrypoint is used. The cmds parameter is templated.
    cmds=['echo'],
    # The namespace to run within Kubernetes, default namespace is
    # `default`. There is the potential for the resource starvation of
    # Airflow workers and scheduler within the Cloud Composer environment,
    # the recommended solution is to increase the amount of nodes in order
    # to satisfy the computing requirements. Alternatively, launching pods
    # into a custom namespace will stop fighting over resources.
    namespace='default',
    # Docker image specified. Defaults to hub.docker.com, but any fully
    # qualified URLs will point to a custom repository. Supports private
    # gcr.io images if the Composer Environment is under the same
    # project-id as the gcr.io images and the service account that Composer
    # uses has permission to access the Google Container Registry
    # (the default service account has permission)
    image='gcr.io/gcp-runtimes/ubuntu_18_0_4')
