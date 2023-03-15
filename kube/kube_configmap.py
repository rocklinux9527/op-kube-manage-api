"""
"""
from kubernetes import client, config
class k8sConfigMapManager:
    def __init__(self, clint_config_file, namespace):
        self.namespace = namespace
        self.config_file = clint_config_file
        config.load_kube_config(config_file=self.client_config)
        self.core_api = client.CoreV1Api()

    def get_kube_configmap(self):
        for cm in self.core_api.list_namespaced_config_map(namespace=self.namespace).items:
            name = cm.metadata.name
            namespace = cm.metadata.namespace
            data_length = ("0" if cm.data is None else len(cm.data))
            create_time = cm.metadata.creation_timestamp
            cm = {"name": name, "namespace": namespace, "data_length": data_length, "create_time": create_time}


