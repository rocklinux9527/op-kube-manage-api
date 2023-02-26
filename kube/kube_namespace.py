from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kube.kube_config import get_kube_namespace


class k8sNameSpaceManager:
    def __init__(self, clint_config_file):
        self.client_config = clint_config_file
        config.load_kube_config(config_file=self.client_config)
        self.v1 = client.CoreV1Api()

    def get_kube_all_namespaces(self):
        """
        1.获取集群中所有namespace.
        :return:
        """
        data = self.v1.list_namespace()
        try:
            nsList = []
            for ns in data.items:
                if ns:
                    ns_name = ns.metadata.name
                    nsList.append(ns_name)
                else:
                    nsList = []
            return {"code": 0, "messages": "query success", "data": nsList, "status": True}

        except Exception as e:
            return {"code": 1, "messages": str(e), "data": "failure", "status": False}

    def create_kube_namespaces(self, name):
        """
        1.输入命名空间名称
        :param name:
        :return:
        """
        body = client.V1Namespace(api_version="v1",
                                  kind="Namespace",
                                  metadata=client.V1ObjectMeta(
                                      name=name)
                                  )
        try:
            data = self.v1.create_namespace(body)
            return {
                "code": 0,
                "messages": "success",
                "data": "create {name} namespace success".format(name=name),
                "status": True
            }
        except ApiException as e:
            print("Exception when calling CoreV1Api->create_namespace: %s\n" % e)
            status = getattr(e, "status")
            if status == 409:
                msg = "Create {name} namespace failure  namespace exist".format(name=name)
                return {"code": 1, "messages": msg, "data": "", "status": False}
