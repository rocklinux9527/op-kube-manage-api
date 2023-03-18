from kubernetes import client, config
from kubernetes.client.rest import ApiException

class K8sServiceManager:
    def __init__(self, config_file):
        self.config_file = config_file
        config.load_kube_config(config_file=self.config_file)
        self.v1 = client.CoreV1Api()

    def get_kube_service(self, namespace):
        """
        1.输入命名空间名称
        :param namespace: 命名空间名称
        :return:
        """
        response_data = [
            {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "CLUSTER-IP": i.spec.cluster_ip,
                "type": i.spec.type,
                "Port(s)": ",".join([f"{j.port}:{j.node_port}/{j.protocol}" for j in i.spec.ports])}
            for i in self.v1.list_namespaced_service(namespace=namespace).items()]
        return response_data

    def get_kube_service_by_name(self, namespace, app_name):
        """
        1.根据svc名称查询 service
        :param namespace: 命名空间名称
        :param app_name: 应用名称
        :return: 若找到，则返回Svc信息，没找到则返回报错信息
        """
        data = self.get_kube_service(namespace)
        matches = [svc for svc in data if svc["name"] == app_name]

        if matches:
            return matches[0]
        else:
            raise Exception(f"The {app_name} service cannot be found in namespace {namespace}")

    def create_kube_svc(self, namespace, svc_name, port_num, target_port, service_type="ClusterIP", selector_labels=None):
        """
        1.创建svc 名称和svc属性信息
        :param namespace: 命名空间名称
        :param svc_name: 服务名称
        :param port_num: 服务端口
        :param target_port: 目标端口
        :param selector_labels: 选择器标签
        :param service_type: 服务类型
        :return: 若成功，则返回Svc信息，失败则返回报错信息
        """
        selector_labels = selector_labels or {"app": svc_name}

        if not isinstance(selector_labels, dict):
            msg = "Service selector labels are not in the correct format."
            raise ValueError(f"{msg} Provided selector labels are of type {type(selector_labels)}")

        body = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=svc_name, labels=selector_labels),
            spec=client.V1ServiceSpec(
                selector=selector_labels,
                ports=[client.V1ServicePort(port=port_num, target_port=target_port)],
                type=service_type
            )
        )
        try:
            response = self.v1.create_namespaced_service(namespace=namespace, body=body)
            return {
                "code": 0,
                "messages": "Create Service Success ",
                "data": response,
                "status": True
            }
        except ApiException as e:
            print(e)
            status = getattr(e, "status")
            if status == 400:
                msg = "Service Invalid format"
            elif status == 403:
                msg = "No permission"
            elif status == 409:
                msg = "Create Service failure: App Service exist"
            elif status == 404:
                msg = f"Create Service failure: Namespace {ns} not found"
            else:
                msg = "Create Service failure"
            return {"code": 1, "messages": msg, "data": "", "status": False}

    def replace_kube_svc(self, namespace, svc_name, port_num, target_port, selector_labels=None, service_type="ClusterIP"):
        """
        :param namespace: 命名空间名称
        :param svc_name: 服务名称
        :param port_num: 服务端口
        :param target_port: 目标端口
        :param selector_labels: 选择器标签
        :param service_type: 服务类型
        :return: 若成功，则返回Svc信息，失败则返回报错信息
        """
        selector_labels = selector_labels or {"app": svc_name}

        if not isinstance(selector_labels, dict):
            msg = "Service selector labels are not in the correct format."
            raise ValueError(f"{msg} Provided selector labels are of type {type(selector_labels)}")

        body = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=svc_name, labels=selector_labels),
            spec=client.V1ServiceSpec(
                selector=selector_labels,
                ports=[client.V1ServicePort(port=port_num, target_port=target_port)],
                type=service_type
            )
        )

        try:
            response = self.v1.replace_namespaced_service(namespace=namespace, body=body)
            return response
        except ApiException as e:
            if e.status == 409:
                msg = (f"Failed to replace Svc ({svc_name}): the "
                       f"{namespace} namespace does not contain an Svc with that name.")
            else:
                msg = f"Failed to update Svc ({svc_name}): {str(e)}"

            raise Exception(msg)

    def delete_kube_svc(self, namespace, svc_name):
        """
        1.删除svc 地址
        :param namespace: 命名空间名称
        :param svc_name: 服务名称
        :return:
        """
        try:
            response = self.v1.delete_namespaced_service(namespace=namespace, name=svc_name)
            return response
        except ApiException as e:
            msg = f"Failed to delete Svc ({svc_name}): {str(e)}"
            raise Exception(msg)


if __name__ == "__main__":
    client_config = "/Users/lijianxing/lijx-devops/python/fastapi/op-kube-manage-api/conf/kubeconf/dev_k8s-cluster-service.conf"
    svc_instance = K8sServiceManager(client_config)
    # data = svc_instance.get_kube_service("default")
    # svc_data = svc_instance.get_kube_service_by_name("default", "sre-nginx-web")
    # print(svc_data)
    # print(data)
    data = svc_instance.create_kube_svc("default", "demo-test-nginx",11881, 80)
    # print(data)
    # data = svc_instance.delete_kube_svc("default","demo-test-nginx")
    # print(data)
