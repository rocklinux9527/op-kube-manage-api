from kubernetes import client, config
from kubernetes.client.rest import ApiException


class k8sServiceManger:
    def __init__(self, config_file):
        self.config_file = config_file
        config.load_kube_config(config_file=self.config_file)
        self.v1 = client.CoreV1Api()

    def get_kube_service(self, namespace):
        """
         1.输入命名空间名称
        :param cluster:
        :return:
        """
        data = self.v1.list_namespaced_service(namespace=namespace)
        response_data = list()

        for i in data.items:
            x = {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "CLUSTER-IP": i.spec.cluster_ip,
                "type": i.spec.type,
                "Port(s)": ",".join(["%s:%s/%s" % (j.port, j.node_port, j.protocol) for j in i.spec.ports])
            }
            response_data.append(x)
        return response_data

    def get_kube_service_by_name(self, namespace, app_name):
        """
        1.根据svc名称查询 service
        :param cluster:
        :param config_file:
        :param app_name:
        :return:
        """
        data = self.get_kube_service(namespace=namespace)

        try:
            return [i for i in data if i["name"] == app_name][0]
        except Exception as e:
            status = getattr(e, "status")
            return [{
                "code": 1,
                "messages": str(e),
                "data": "the {svc} does not exist. check the name of the cluster service".format(svc=app_name),
                "status": False
            }]

    def create_kube_svc(self, namespace, svc_name, selector_labels, port, target_port, type="ClusterIP"):
        """
        1.创建svc 名称和svc属性信息
        :param namespace:
        :param svc_name:
        :param port:
        :param target_port:
        :param selector:
        :param type:
        :return:
        """
        if isinstance(selector_labels, dict):
            if selector_labels:
                runSvcBody = self.public_svc_body(svc_name, selector_labels, port, target_port, type)
                try:
                    data = self.v1.create_namespaced_service(namespace=namespace, body=runSvcBody)
                    if data:
                        return {
                            "code": 0,
                            "messages": "Create Service Success ",
                            "data": data,
                            "status": True
                        }
                except ApiException as e:
                    print(e)
                    status = getattr(e, "status")
                    if status == 409:
                        msg = "create {name} svc failure, svc not existing".format(name=svc_name)
                        return {"code": 1, "messages": msg, "data": "", "status": False}
            else:
                default_selector_labels = {"app": svc_name}
                runSvcBody = self.public_svc_body(svc_name, selector_labels, port, target_port, type)
                try:
                    data = self.v1.create_namespaced_service(namespace=namespace, body=runSvcBody)
                    if data:
                        return {
                            "code": 0,
                            "messages": "Create Service Success ",
                            "data": data,
                            "status": True
                        }
                except ApiException as e:
                    print(e)
                    status = getattr(e, "status")
                    if status == 409:
                        msg = "create {name} svc failure, svc not existing".format(name=svc_name)
                        return {"code": 1, "messages": msg, "data": "", "status": False}
        else:
            msg = "service selector labels It doesn't work properly unless it exists "
            return {"code": 1, "messages": msg, "data": "", "status": False}

    def replace_kube_svc(self, namespace, svc_name, selector_labels, port, target_port, type="ClusterIP"):
        """
        :param namespace:
        :param svc_name:
        :param selector_labels:
        :param port:
        :param target_port:
        :param type:
        :return:
        """
        if isinstance(selector_labels, dict):
            if selector_labels:
                runSvcBody = self.public_svc_body(svc_name, selector_labels, port, target_port, type)
                try:
                    data = self.v1.replace_namespaced_service(namespace=namespace, body=runSvcBody)
                    if data:
                        return {
                            "code": 0,
                            "messages": "Update Service Success",
                            "data": data,
                            "status": True
                        }
                except ApiException as e:
                    print(e)
                    status = getattr(e, "status")
                    if status == 409:
                        msg = "update {name} svc failure, svc not existing".format(name=svc_name)
                        return {"code": 1, "messages": msg, "data": "", "status": False}
            else:
                default_selector_labels = {"app": svc_name}
                runSvcBody = self.public_svc_body(svc_name, selector_labels, port, target_port, type)
                try:
                    data = self.v1.replace_namespaced_service(namespace=namespace, body=body)
                    if data:
                        return {
                            "code": 0,
                            "messages": "Update Service Success ",
                            "data": data,
                            "status": True
                        }
                except ApiException as e:
                    print(e)
                    status = getattr(e, "status")
                    if status == 409:
                        msg = "create {name} svc failure, svc not existing".format(name=svc_name)
                        return {"code": 1, "messages": msg, "data": "", "status": False}
        else:
            msg = "service selector labels It doesn't work properly unless it exists "
            return {"code": 1, "messages": msg, "data": "", "status": False}

    def delete_kube_svc(self, namespace, svc_name):
        """
        1.删除svc 地址
        :param namespace:
        :param name:
        :return:
        """
        try:
            data = self.v1.delete_namespaced_service(namespace=namespace, name=svc_name)
            return data
        except ApiException as e:
            print(e)
            msg = "service delete failure" + str(e)
            return {"code": 1, "messages": msg, "data": "", "status": False}

    def public_svc_body(self, svc_name, selector_labels, port, target_port, type="ClusterIP"):
        """
        1.公共svc body 方法
        :param svc_name:
        :param selector_labels:
        :param port:
        :param target_port:
        :param type:
        :return:
        """
        body = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=svc_name, labels=selector_labels
            ),
            spec=client.V1ServiceSpec(
                selector=selector_labels,
                ports=[client.V1ServicePort(
                    port=port,
                    target_port=target_port
                )],
                type=type
            )
        )
        return body


if __name__ == "__main__":
    client_config = "/Users/lijianxing/lijx-devops/python/fastapi/op-kube-manage-api/conf/kubeconf/dev_k8s-cluster-service.conf"
    svc_instance = k8sServiceManger(client_config)
    # data = svc_instance.get_kube_service("default")
    # svc_data = svc_instance.get_kube_service_by_name("default", "sre-nginx-web")
    # print(svc_data)
    # print(data)
    data = svc_instance.create_kube_svc("default", "demo-test-nginx",
                                        11881, 80)
    # print(data)
    # data = svc_instance.delete_kube_svc("default","demo-test-nginx")
    # print(data)
