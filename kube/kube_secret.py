"""
"""


class k8sSecretManager():
    def __init__(self):
        self.namespace = namespace
        self.config_file = clint_config_file
        config.load_kube_config(config_file=self.client_config)
        self.core_api = client.CoreV1Api()

    def get_kube_secret(self):
        secretList = []
        for secret in self.core_api.list_namespaced_secret(namespace=namespace).items:
            name = secret.metadata.name
            namespace = secret.metadata.namespace
            data_length = ("空" if secret.data is None else len(secret.data))
            create_time = secret.metadata.creation_timestamp
            secretList.append({"name": name, "namespace": namespace, "data_length": data_length, "create_time": create_time})
        return secretList

    def delete_kube_secret(self, secret_name):
        """
        1.secret 名称
        :param secret_name:
        :return:
        """
        self.core_api.delete_namespaced_secret(namespace=self.namespace, name=secret_name)
