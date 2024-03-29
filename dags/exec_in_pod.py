from __future__ import print_function
import time
import kubernetes.client
import kubernetes.config
from kubernetes.stream import stream
from kubernetes.client.rest import ApiException
from pprint import pprint
import logging


def get_pod_name(deployment_name, namespace, selector=False):
    try:
        kubernetes.config.load_incluster_config()
    except:
        kubernetes.config.load_kube_config()

    api_instance = kubernetes.client.CoreV1Api()

    try:
        if selector:
            pod_label_selector = "app=" + deployment_name + ", " + selector
        else:
            pod_label_selector = "app=" + deployment_name
        api_response = api_instance.list_namespaced_pod(
            namespace, label_selector=pod_label_selector, pretty='true')
        for x in api_response.items:
            if deployment_name in x.metadata.name:
                return x.metadata.name
    except ApiException as e:
        logging.critical(
            "Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)


def exec_in_pod(deployment_name, namespace, command, selector=False):
    try:
        kubernetes.config.load_incluster_config()
    except:
        kubernetes.config.load_kube_config()

    api_instance = kubernetes.client.CoreV1Api()

    name = get_pod_name(deployment_name, namespace, selector)

    try:
        api_response = stream(api_instance.connect_post_namespaced_pod_exec, name, namespace, command=command, stderr=True,
                              stdin=True,
                              stdout=True,
                              tty=False,
                              _preload_content=True)
        logging.critical(pprint(api_response))
    except ApiException as e:
        logging.critical(
            "Exception when calling CoreV1Api->connect_post_namespaced_pod_exec: %s\n" % e)

# API RESPONSE NOT WORKING FOR EXEC COMMAND
# https://github.com/kubernetes-client/python/issues/485
