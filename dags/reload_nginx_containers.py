from __future__ import print_function
import time
import kubernetes.client
import kubernetes.config
from kubernetes.stream import stream
from kubernetes.client.rest import ApiException
from pprint import pprint
import logging

# Command to hot reload nginx container config
reload_command = [
'/bin/sh',
'-c',
'nginx -s reload'
]

# For each pod that contains an nginx container, reload nginx
def reload_nginx_containers(deployment_name, namespace):
    try:
        kubernetes.config.load_incluster_config()
    except:
        kubernetes.config.load_kube_config()

    configuration = kubernetes.client.Configuration()
    api_instance = kubernetes.client.CoreV1Api(
        kubernetes.client.ApiClient(configuration))

    # Get all pod & container names for pods that have an nginx container
    try:
        pod_label_selector = "app.kubernetes.io/name=" + deployment_name
        api_response = api_instance.list_namespaced_pod(
            namespace, label_selector=pod_label_selector, pretty='true')
        pod_container_list = []
        for pod in api_response.items:
            for container in pod.spec.containers:
                if 'nginx' in container.name:
                    pod_container_set = [pod.metadata.name, container.name]
                    pod_container_list.append(pod_container_set)

        # Run the reload command in each nginx container
        for pod_container in pod_container_list:
            try:
                api_response = stream(api_instance.connect_post_namespaced_pod_exec,
                                      pod_container[0],
                                      namespace,
                                      container=pod_container[1],
                                      command=reload_command,
                                      stderr=True,
                                      stdin=True,
                                      stdout=True,
                                      tty=False,
                                      _preload_content=True)
                logging.critical(pprint(api_response))
            except ApiException as e:
                logging.critical(
                  "Exception when calling CoreV1Api->connect_post_namespaced_pod_exec: %s\n" % e)

    except ApiException as e:
        logging.critical(
            "Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)
