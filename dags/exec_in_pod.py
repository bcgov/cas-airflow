from __future__ import print_function
import time
import kubernetes.client
from kubernetes.client.rest import ApiException
from pprint import pprint

def get_pod_name(deployment_name, namespace):

  configuration = kubernetes.client.Configuration()
  api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))

  # field_selector = 'field_selector_example' # str | A selector to restrict the list of returned objects by their fields. Defaults to everything. (optional)
  label_selector = deployment_name # str | A selector to restrict the list of returned objects by their labels. Defaults to everything. (optional)
  limit = 1 # int | limit is a maximum number of responses to return for a list call. If more items exist, the server will set the `continue` field on the list metadata to a value that can be used with the same initial query to retrieve the next set of results. Setting a limit may return fewer than the requested amount of items (up to zero items) in the event all requested objects are filtered out and kubernetes.clients should only use the presence of the continue field to determine whether more results are available. Servers may choose not to support the limit argument and will return all of the available results. If limit is specified and the continue field is empty, kubernetes.clients may assume that no more results are available. This field is not supported if watch is true.  The server guarantees that the objects returned when using continue will be identical to issuing a single list call without a limit - that is, no objects created, modified, or deleted after the first request is issued will be included in any subsequent continued requests. This is sometimes referred to as a consistent snapshot, and ensures that a kubernetes.client that is using limit to receive smaller chunks of a very large result can ensure they see all possible objects. If objects are updated during a chunked list the version of the object that was present at the time the first list result was calculated is returned. (optional)
  timeout_seconds = 56 # int | Timeout for the list/watch call. This limits the duration of the call, regardless of any activity or inactivity. (optional)

  try:
      api_response = api_instance.list_namespaced_pod(namespace, pretty=pretty, allow_watch_bookmarks=allow_watch_bookmarks, _continue=_continue, field_selector=field_selector, label_selector=label_selector, limit=limit, resource_version=resource_version, timeout_seconds=timeout_seconds, watch=watch)
      return api_response
  except ApiException as e:
      print("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

def exec_in_pod(deployment_name, namespace, command):

  configuration = kubernetes.client.Configuration()
  api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))

  name = get_pod_name(deployment_name, namespace)

  try:
      api_response = api_instance.connect_post_namespaced_pod_exec(name, namespace, command=command)
      pprint(api_response)
  except ApiException as e:
      print("Exception when calling CoreV1Api->connect_post_namespaced_pod_exec: %s\n" % e)
