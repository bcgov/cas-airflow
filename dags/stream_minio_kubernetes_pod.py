from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator

k = KubernetesPodOperator(namespace='default',
                          image="ubuntu:16.04",
                          cmds=["bash", "-cx"],
                          arguments=["echo", "808080801010"],
                          labels={"foo": "bar"},
                          name="test",
                          task_id="task",
                          is_delete_operator_pod=True
                          )
