from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kube.kube_config import get_kube_namespace

class K8sNamespaceManager:
    """
    1. 可以使用更加规范的命名方式。例如，重命名`k8sNameSpaceManager`为`K8sNamespaceManager`。
    2. 可以使用`requests`模块中的`status_code`属性获取HTTP请求的状态码，而不是在异常中使用`status`属性。
    3. 异常信息不应该直接打印在控制台上，而是应该使用`raise`关键字抛出错误。
    """

    def __init__(self, client_config_file):
        self.client_config_file = client_config_file
        config.load_kube_config(config_file=self.client_config_file)
        self.v1 = client.CoreV1Api()

    def get_kube_all_namespaces(self):
        """
        获取集群中所有的namespace
        :return:
        """
        try:
            namespaces = [ns.metadata.name for ns in self.v1.list_namespace().items]
            return {
                "code": 0,
                "messages": "Query successful",
                "data": namespaces,
                "status": True
            }
        except ApiException as e:
            error = f"Failed to get namespaces: {e}"
            raise Exception(error)

    def create_kube_namespaces(self, name):
        """
        创建新的namespace
        :param name:
        :return:
        """
        body = client.V1Namespace(
            api_version="v1",
            kind="Namespace",
            metadata=client.V1ObjectMeta(name=name)
        )

        try:
            self.v1.create_namespace(body)
            return {
                "code": 0,
                "messages": "success",
                "data": f"Namespace {name} created successfully",
                "status": True
            }
        except ApiException as e:
            print("Exception when calling CoreV1Api->create_namespace: %s\n" % e)
            status = getattr(e, "status")
            if status == 409:
                msg = "Create {name} namespace failure  namespace exist".format(name=name)
                return {"code": 1, "messages": msg, "data": "", "status": False}

# class k8sNameSpaceManager:
#     def __init__(self, clint_config_file):
#         self.client_config = clint_config_file
#         config.load_kube_config(config_file=self.client_config)
#         self.v1 = client.CoreV1Api()
#
#     def get_kube_all_namespaces(self):
#         """
#         1.获取集群中所有namespace.
#         :return:
#         """
#         data = self.v1.list_namespace()
#         try:
#             nsList = []
#             for ns in data.items:
#                 if ns:
#                     ns_name = ns.metadata.name
#                     nsList.append(ns_name)
#                 else:
#                     nsList = []
#             return {"code": 0, "messages": "query success", "data": nsList, "status": True}
#
#         except Exception as e:
#             return {"code": 1, "messages": str(e), "data": "failure", "status": False}
#
#     def create_kube_namespaces(self, name):
#         """
#         1.输入命名空间名称
#         :param name:
#         :return:
#         """
#         body = client.V1Namespace(api_version="v1",
#                                   kind="Namespace",
#                                   metadata=client.V1ObjectMeta(
#                                       name=name)
#                                   )
#         try:
#             data = self.v1.create_namespace(body)
#             return {
#                 "code": 0,
#                 "messages": "success",
#                 "data": "create {name} namespace success".format(name=name),
#                 "status": True
#             }
#         except ApiException as e:
#             print("Exception when calling CoreV1Api->create_namespace: %s\n" % e)
#             status = getattr(e, "status")
#             if status == 409:
#                 msg = "Create {name} namespace failure  namespace exist".format(name=name)
#                 return {"code": 1, "messages": msg, "data": "", "status": False}
